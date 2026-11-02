import socket, ssl, re, hashlib, hmac, struct

host='c3-vault-9bc2ce4beb36.chall.hiddeninvestigations.net'
device=bytes.fromhex('ee0315f3953aad298d7f3f43973ad618')
seed=bytes.fromhex('826e4e9e65c0ce89f413b7c291bb7e84185c64d4ec8769805227253b985083c5')
key=hmac.new(seed,b'c3-vault/device-key/v2\0'+device+struct.pack('<I',7),hashlib.sha256).digest()

# Match the provided ncat --ssl transport, which does not request certificate verification.
ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.check_hostname=False
ctx.verify_mode=ssl.CERT_NONE
with socket.create_connection((host,1337),timeout=12) as raw:
    with ctx.wrap_socket(raw,server_hostname=host) as sock:
        sock.settimeout(8)
        def recv_prompt():
            result=b''
            while not result.endswith(b'> '):
                chunk=sock.recv(8192)
                if not chunk: break
                result+=chunk
            print(result.decode())
            return result
        banner=recv_prompt()
        nonce=bytes.fromhex(re.search(rb'CHALLENGE ([0-9a-f]{64})',banner)[1].decode())
        response=hmac.new(key,b'C3VAULT-AUTH-V2\0'+nonce+device,hashlib.sha256).hexdigest()
        sock.sendall(b'auth '+response.encode()+b'\n')
        recv_prompt()
