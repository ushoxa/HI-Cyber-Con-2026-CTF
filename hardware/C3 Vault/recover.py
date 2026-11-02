from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import struct
root=Path(__file__).parent
flash=(root/'flash_image.bin').read_bytes()
efuse=(root/'efuse_read.bin').read_bytes()
raw=efuse[0x70:0x90]
def decrypt(data, address, key):
    out=bytearray()
    for i in range(0,len(data),128):
        tweak=struct.pack('<I',address+i)+bytes(12)
        dec=Cipher(algorithms.AES(key),modes.XTS(tweak)).decryptor()
        out.extend(dec.update(data[i:i+128][::-1])[::-1])
    return bytes(out)
for key in (raw,raw[::-1]):
    table=decrypt(flash[0x8000:0x9000],0x8000,key)
    print('key',key.hex(),'table',table[:64].hex())
    if table[:2]==b'\xaa\x50':
        plain=decrypt(flash,0,key)
        (root/'decrypted.bin').write_bytes(plain)
        for i in range(0,0xc0,32): print(table[i:i+32].hex())
plain=(root/'decrypted.bin').read_bytes()
nvs_key=plain[0xf000:0xf040]
for page in range(6):
    start=0x9000+page*4096
    bitmap=int.from_bytes(flash[start+32:start+64],'little')
    for entry in range(126):
        state=(bitmap>>(2*entry))&3
        if state==3: continue
        rel=page*4096+64+entry*32
        dec=Cipher(algorithms.AES(nvs_key),modes.XTS(rel.to_bytes(16,'little'))).decryptor()
        item=dec.update(flash[0x9000+rel:0x9000+rel+32])
        print('NVS',page,entry,'state',state,item.hex(),repr(item))
