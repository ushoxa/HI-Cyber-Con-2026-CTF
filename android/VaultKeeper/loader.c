#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <time.h>

static uintptr_t image_base = 0x20000000ULL;

static void load_chunk(int fd, void *dst, off_t off, size_t len) {
    ssize_t n = pread(fd, dst, len, off);
    if (n != (ssize_t)len) { perror("pread"); exit(1); }
}

static void capture_sync(const uint8_t *p, uint32_t n) {
    printf("nv_sync(%u): ", n);
    fwrite(p, 1, n, stdout);
    putchar('\n');
}

static uint32_t rol32(uint32_t x, unsigned n) {
    n &= 31;
    return n ? (x << n) | (x >> (32 - n)) : x;
}

static uint32_t ror32(uint32_t x, unsigned n) {
    n &= 31;
    return n ? (x >> n) | (x << (32 - n)) : x;
}

static void java_k1(uint32_t x[128]) {
    for (uint32_t round = 0; round < 7; round++) {
        int reverse = (round % 2) != 0;
        for (uint32_t j = 0; j < 128; j++) {
            uint32_t i = reverse ? (127 - j) : j;
            uint32_t a = x[(i - 1) & 127];
            uint32_t b = x[i];
            uint32_t c = x[(i + 1) & 127];
            uint32_t v = b + rol32(a, 11) + ror32(c, 5);
            v *= 0x85ebca6bU;
            x[i] = rol32(v, 13 + (round % 3));
        }
    }
}

static void java_k2(uint8_t data[2048], const uint32_t x[128]) {
    for (uint32_t pos = 0, block = 0; pos < 2048; block++) {
        uint8_t ks[256];
        for (uint32_t i = 0; i < 256; i++) {
            uint32_t w = x[(i * 7 + block * 13) & 127];
            ks[i] = (uint8_t)((w >> ((i & 3) * 8)) ^ ((block * 31 + i) & 255));
        }
        uint32_t take = 2048 - pos;
        if (take > 256) take = 256;
        for (uint32_t i = 0; i < take; i++) data[pos + i] ^= ks[i];
        pos += take;
    }
}

int main(void) {
    const char *libpath = "work/vaultkeeper/apk/lib/x86_64/libvaultnative.so";
    int fd = open(libpath, O_RDONLY);
    if (fd < 0) { perror("open lib"); return 1; }
    void *mem = mmap((void *)image_base, 0x10000,
                     PROT_READ | PROT_WRITE | PROT_EXEC,
                     MAP_PRIVATE | MAP_ANON | MAP_FIXED, -1, 0);
    if (mem == MAP_FAILED) { perror("mmap"); return 1; }
    load_chunk(fd, (void *)image_base, 0, 0x6790);
    load_chunk(fd, (void *)(image_base + 0x7790), 0x6790, 0x2d8);
    close(fd);

    *(uintptr_t *)(image_base + 0x7790) += image_base;
    *(uintptr_t *)(image_base + 0x7798) = image_base + 0x3ba0;
    *(uintptr_t *)(image_base + 0x77a0) = image_base + 0x3b80;

    *(void **)(image_base + 0x7948) = malloc;
    *(void **)(image_base + 0x7950) = memset;
    *(void **)(image_base + 0x7958) = (void *)(image_base + 0x40c0);
    *(void **)(image_base + 0x7960) = free;
    *(void **)(image_base + 0x7968) = (void *)(image_base + 0x4310);
    *(void **)(image_base + 0x7970) = (void *)(image_base + 0x4440);
    *(void **)(image_base + 0x7978) = (void *)(image_base + 0x46e0);
    *(void **)(image_base + 0x7998) = memcpy;
    *(void **)(image_base + 0x79a0) = clock_gettime;
    *(void **)(image_base + 0x7a60) = capture_sync;

    /* Skip the Android-only environment/anti-instrumentation audit. */
    *(uint8_t *)(image_base + 0x4f80) = 0xc3;

    uint8_t vault[8192];
    fd = open("work/vaultkeeper/apk/assets/vault.bin", O_RDONLY);
    if (fd < 0) { perror("open vault"); return 1; }
    load_chunk(fd, vault, 0, sizeof(vault));
    close(fd);

    uint8_t token[16] = {0};
    uint32_t cells[128] = {0};
    uint8_t unsealed[2048] = {0};

    void (*nv_seed)(const uint8_t *, uint32_t, const uint8_t *, uint32_t *) =
        (void *)(image_base + 0x40c0);
    void (*nv_unseal)(const uint32_t *, const uint8_t *, uint8_t *, uint32_t) =
        (void *)(image_base + 0x4310);
    int (*nv_exec)(const uint8_t *, uint32_t, const uint32_t *, const uint8_t *) =
        (void *)(image_base + 0x4440);
    int (*nv_final)(const uint8_t *) = (void *)(image_base + 0x46e0);

    nv_seed(vault, sizeof(vault), token, cells);
    java_k1(cells);
    nv_unseal(cells, token, unsealed, sizeof(unsealed));
    java_k2(unsealed, cells);
    int er = nv_exec(unsealed, sizeof(unsealed), cells, token);
    printf("nv_exec=%d stage=%u flags=%#x\n", er,
           *(uint32_t *)(image_base + 0x8a74),
           *(uint32_t *)(image_base + 0x8a70));
    *(uint32_t *)(image_base + 0x8a70) = 0;
    int fr = nv_final(token);
    printf("nv_final=%d rejected=%u\n", fr, *(uint32_t *)(image_base + 0x8a7c));
    return 0;
}
