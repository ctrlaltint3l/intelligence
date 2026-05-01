#!/usr/bin/env python3

import binascii
import argparse
import base64
import readline
import struct


# Date: 10/21/2023
# Author: Jamie



class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def get_args():
    parser = argparse.ArgumentParser(description='SMBGhost Detection and Exploitation')
    parser.add_argument('-i', '--input', dest='fi', type=str, required=True, help='Input File')
    parser.add_argument('-o', '--out', dest='fo', type=str, required=True, help='Output File')
    
    return parser.parse_args()
    
def safe_decode(byte_data, encoding='UTF-8'):
    try:
        return byte_data.decode(encoding)
    except UnicodeDecodeError:
        # Return a default value or the byte data itself
        return byte_data.decode(encoding, errors='replace')  # Or 'ignore' to drop invalid characters


def parse_credentials(fileIn, fileOut):
    try:
        with open(fileIn, 'rb') as credential_file:
            credential_data = credential_file.read()
            credential_data = credential_data.strip()
            #print ("SHELL CODE",credential_data)
    except:
        print((" [!] WARNING: path not found"))
        return None

    if len(credential_data) == 0:
        print(" [!] WARNING: no credential restrieved", )
        return None

    file_len = len(credential_data)
    out_file = open(fileOut, 'w')
    out_file.write("User,Password,Status\n")
    for index in range(0, int(file_len / 0x84)):
        username = (credential_data[index * 0x84 : index * 0x84 + 0x40])
        password = (credential_data[index * 0x84 + 0x40: index * 0x84 + 0x80])
        result = credential_data[index * 0x84 + 0x80: index * 0x84 + 0x84]
        
        userlen = username.index(b'\x00')
        passlen = password.index(b'\x00')
        if (password[passlen - 1] == 10):
            passlen -= 1
        status = "failed"
        match result[0]:
            case 1:
                status = "success"
            case 2:
                status = "no_matching_policy"
            case 3:
                status = "insufficient_credential"
            case 4:
                status = "unknown_user"
            case 5:
                status = "permission_denied"
            case 8: 
                status = "password_expired"
            case 9: 
                status = "change_password_failed"
            case 6: 
                status = "Password_expired"
            case _: 
                status = "cert_checked_error"
                if (result[0] != 12):
                    status = "token_timeout"
                    if (result[0] != 13):
                        status = "unknown_reason"
        username_decoded = safe_decode(username[0:userlen]) if isinstance(username, bytes) else username[0:userlen]
        password_decoded = safe_decode(password[0:passlen]) if isinstance(password, bytes) else password[0:passlen]
        data = "%s,%s,%s\n" % (username_decoded, password_decoded, status)
        out_file.write(data)
    out_file.close()



if __name__ == '__main__':
    args = get_args()
    filein = args.fi
    fileout = args.fo
    
    parse_credentials(filein, fileout + ".csv")
