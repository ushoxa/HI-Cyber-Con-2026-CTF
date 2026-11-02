#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

static void load_chunk(int fd, void *dst, off_t off, size_t len) {
    ssize_t n = pread(fd, dst, len, off);
    if (n != (ssize_t)len) {
        perror("pread");
        exit(1);
    }
}

int main(void) {
    const char *path = "work/obs-flow/challenge";
    int fd = open(path, O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }

    void *base = mmap((void *)0x400000, 0x6000,
                      PROT_READ | PROT_WRITE | PROT_EXEC,
                      MAP_PRIVATE | MAP_ANON | MAP_FIXED, -1, 0);
    if (base == MAP_FAILED) { perror("mmap"); return 1; }

    load_chunk(fd, (void *)0x400000, 0x0000, 0x0618);
    load_chunk(fd, (void *)0x401000, 0x1000, 0x1a99);
    load_chunk(fd, (void *)0x403000, 0x3000, 0x049c);
    load_chunk(fd, (void *)0x404df8, 0x3df8, 0x0248);
    close(fd);

    *(void **)0x405000 = (void *)strncmp;
    *(void **)0x405008 = (void *)puts;
    *(void **)0x405010 = (void *)strlen;
    *(void **)0x405018 = (void *)printf;
    *(void **)0x405020 = (void *)fgets;
    *(void **)0x405028 = (void *)fflush;
    *(FILE **)0x405040 = stdout;
    *(FILE **)0x405050 = stdin;

    int (*challenge_main)(void) = (int (*)(void))0x4010c0;
    return challenge_main();
}
