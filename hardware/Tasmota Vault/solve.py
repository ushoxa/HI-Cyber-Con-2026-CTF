from pathlib import Path
import struct, re, hashlib, hmac
from Crypto.Cipher import AES

root = Path(__file__).parent
flash = (root/'flash.bin').read_bytes()
bec = flash[0x3b4000:0x3b4000+0x5b8]
pos = 8
def read(n):
    global pos
    b = bec[pos:pos+n]; pos += n
    assert len(b)==n
    return b
def num(n): return int.from_bytes(read(n),'little')
def string(): return read(num(2)).decode()
builtin = num(4); globals_count = num(4)
globals_names = [string() for _ in range(globals_count)]
ops = re.findall(r'^OPCODE\((\w+)\)', (root/'source/Tasmota-15.6.0/lib/libesp32/berry/src/be_opcodes.h').read_text(), re.M)
def proto():
    name=string(); source=string(); args=read(4)
    code=[num(4) for _ in range(num(4))]
    const=[]
    for _ in range(num(4)):
        t=num(1)
        if t==16: const.append(string())
        elif t in (1,2): const.append(num(4))
        elif t in (0,3): const.append(('type',t))
        else: raise ValueError((t,pos))
    print('\nFUNCTION',name,'args',list(args),'constants',const)
    def rk(v): return repr(const[v&255]) if v&256 and (v&255)<len(const) else 'R'+str(v)
    for i,w in enumerate(code):
        op=ops[w>>26]; a=(w>>18)&255; b=(w>>9)&511; c=w&511; bx=w&0x3ffff
        print(f'{i:03} {op:9} R{a} {rk(b)} {rk(c)} bx={bx} sbx={bx-131071}')
    for _ in range(num(4)): proto()
    up=read(num(1)*2)
    print('UPVAL',name,up.hex())
proto()
print('END',pos,len(bec))

device=flash[0x3b2104:0x3b2114]
keyring=flash[0x3b2204:0x3b2270]
sealed=flash[0x3b2384:0x3b23ce]
rotations=[(7,'9bb1ebe2f5663269d3be1348ee57dc7dbce22b373243aebd67897581cf6f65f0'),(8,'1a3dfb1382455e073f25450c8c8cee24ba89b0a924f86b7103a732ab902a2606')]
for epoch,nonce in rotations:
    matches=[keyring[i+4:i+36] for i in range(0,len(keyring),36) if int.from_bytes(keyring[i:i+4],'little')==epoch]
    assert len(matches)==1
    material=b'tasmota-vault/unwrap/v2\0'+device+struct.pack('<I',epoch)+bytes.fromhex(nonce)
    key=hmac.new(matches[0],material,hashlib.sha256).digest()
    cipher=AES.new(key,AES.MODE_GCM,nonce=sealed[:12])
    try:
        plain=cipher.decrypt_and_verify(sealed[12:-16],sealed[-16:])
        print('AUTHENTICATED',epoch,repr(plain),plain.hex())
    except ValueError:
        print('REJECTED',epoch)
