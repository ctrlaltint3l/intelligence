import base64

def xor_decrypt(data: bytes, key: str) -> bytes:
    key_bytes = key.encode()
    output = bytearray()

    for i in range(len(data)):
        output.append(data[i] ^ key_bytes[i % len(key_bytes)])

    return bytes(output)

def decrypt_string(input_string: str) -> str:
    key = "mysecretkey"

    if not input_string:
        return ""

    decoded = base64.b64decode(input_string)
    xored = xor_decrypt(decoded, key)

    # Windows CMD output is often OEM/ANSI encoded, not always UTF-8.
    for encoding in ("utf-8", "cp437", "cp850", "cp1252", "latin-1"):
        try:
            return xored.decode(encoding)
        except UnicodeDecodeError:
            continue
    return xored.decode("utf-8", errors="replace")
def enc_string(input_string: str) -> str:
    key = "mysecretkey"

    # تبدیل string به bytes
    data_bytes = input_string.encode()

    xored = xor_decrypt(data_bytes, key)
    encoded = base64.b64encode(xored)

    return encoded.decode()
