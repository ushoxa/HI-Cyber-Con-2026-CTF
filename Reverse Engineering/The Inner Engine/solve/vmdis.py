import sys, struct

ELF = sys.argv[1]
data = open(ELF, "rb").read()

# .rodata file offset == VMA for these (VMA 0x405e00 -> file off 0x5e00; load bias: off=VMA-0x400000)
VM_OFF = 0x5e00
# program bytes: PC range 0..0x492 ; read a bit more
prog = data[VM_OFF:VM_OFF + 0x492 + 5]

OPS = {
    0xf2: ("ANTIDBG", False),
    0x49: ("JZ", True),
    0x4c: ("PUSHKEY", True),
    0xa3: ("DUP", False),
    0x2b: ("DROP", False),
    0x38: ("STOREG", True),
    0x17: ("PUSH", True),
    0xbf: ("OR", False),
    0x95: ("LOADREG", True),
    0xc1: ("SUB", False),
    0x64: ("ROL", True),
    0xd7: ("JMP", True),
    0xe5: ("STATE1", False),
    0x5a: ("STATE2", False),
    0x52: ("XOR", False),
    0x1e: ("EQ", False),
    0x7d: ("ADD", False),
    0x33: ("AND", False),
    0x8a: ("MUL", False),
    0x71: ("NEG", False),
    0xae: ("NOT", False),
    0xcc: ("SHL", True),
    0x0b: ("UNSEAL", False),
}

pc = 0
while pc + 5 <= len(prog):
    op = prog[pc]
    imm = struct.unpack("<I", prog[pc + 1:pc + 5])[0]
    name, has_imm = OPS.get(op, ("??op%02x" % op, True))
    if has_imm:
        # show imm in dec and hex/char
        extra = ""
        if name in ("JZ", "JMP"):
            extra = "  ; -> instr#%d" % (imm // 5)
        print("%4d (pc=%4d): %-8s %d (0x%x)%s" % (pc // 5, pc, name, imm, imm, extra))
    else:
        print("%4d (pc=%4d): %-8s" % (pc // 5, pc, name))
    pc += 5

