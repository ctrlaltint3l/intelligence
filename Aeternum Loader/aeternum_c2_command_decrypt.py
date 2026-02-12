import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

def decrypt_command(contract_address, encrypted):
    iv_b64, ct_b64 = encrypted.split(":", 1) # Extract IV / ENC data

    iv = base64.b64decode(iv_b64)          # B64 decode IV 
    ciphertext = base64.b64decode(ct_b64)  # B64 decode ENC data

    
    addr = contract_address.lower().encode("utf-8")   
    kdf = PBKDF2HMAC(                             # Derive AES key from contract address
        algorithm=hashes.SHA256(), 
        length=32,            # 256 bits
        salt=addr,            # salt = contract address (same as password)
        iterations=100_000,
    )
    key = kdf.derive(addr)    # password = contract address


    aesgcm = AESGCM(key) 
    plaintext = aesgcm.decrypt(iv, ciphertext, None)  # AES decrypt


    return plaintext.decode("utf-8") #Plaintext command
