
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from packages.consts import AES_KEY, IV

def encrypt_AES(data, AES_KEY = AES_KEY, IV = IV):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, IV)
    cipher_text = cipher.encrypt(pad(data, AES.block_size))
    return cipher_text

def decrypt_AES(enc_data, AES_KEY = AES_KEY, IV = IV):
    decrypt_cipher = AES.new(AES_KEY, AES.MODE_CBC, IV)
    unpadded = decrypt_cipher.decrypt(enc_data)
    plain_text = unpad(unpadded, AES.block_size)
    return plain_text
