import sys
import os
import time
import socket
import struct
import ssl
import binascii
import atexit
import signal
import json
import locale
from threading import Thread

class Scanner:

	def __init__(self, host, port):
			self.host = host
			self.port = port
			self.socket = None

	def connect(self):
		tries = 1
		useSSL = True
		while tries <= 2:
			try:
				self.cleartext_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				if useSSL == True:
					ctx = ssl._create_unverified_context()
					self.socket = ctx.wrap_socket(self.cleartext_socket)
				else:
					self.socket = self.cleartext_socket
				self.socket.settimeout(2.0)
				self.socket.connect((self.host, self.port))

				return self.socket
			except Exception as e:
				tries += 1
				#print(e)
				continue
		
		return None
	        
	def parsewoff(self, woff):
	
		signature, flavor, length, num_tables, \
        	reserved, total_sfnt_size, \
        	major_version, minor_version, \
        	meta_offset, meta_length, \
        	meta_orig_length, priv_offset, priv_length = struct.unpack(">4s4sLHHLHHLLLLL", woff[:44])

		table_directory = []
		index = 0
		
		if num_tables > 30:
			print("[!] Wrong font type.")
			return None
		for _ in range(num_tables):
			tag, offset, comp_length, orig_length, orig_checksum = struct.unpack(">4sLLLL", woff[44 + index * 20 : 44 + (index + 1) * 20])
			index += 1
			table_directory.append((tag.decode("ascii"), offset, comp_length, orig_length, orig_checksum))

		for tag, offset, comp_length, orig_length, orig_checksum in table_directory:
			if tag == "head":
				return hex(orig_checksum) 
				
		return None      
	
	def gethash(self):

		try:
			req = b""
			req += b"GET /remote/login?lang=en HTTP/1.1\r\n"
			req += b"Host: " + self.host.encode() + b": " + str(self.port).encode()  + b"\r\n"
			req += b"User-Agent: AAAAAAAAAAAAAAAA\r\n"
			req += b"Content-Type: application/x-www-form-urlencoded\r\n"
			req += b"Accept: */*\r\n\r\n"  
								
			self.socket.sendall(req)
			            
			self.socket.settimeout(10) 
			buf = self.socket.recv(1048576)

			if len(buf) == 0:
				return None

			if buf.decode().__contains__("HTTP/1.1 200 OK"):
				txt = buf.decode().find("login.js?q=")
				subtxt = buf.decode()[txt:]
				txt2 = subtxt.find(">")
				mhash = subtxt[11:txt2-1]
			elif buf.decode().__contains__("HTTP/1.1 302 Found"):
				txt = buf.decode().find("Location: ")
				ss = buf.decode()[txt:]
				txt2 = ss.find("\r\n")
				sub = ss[10:txt2]
				print(sub)
				req2 = b""
				req2 += b"GET "+sub.encode()+b" HTTP/1.1\r\n"
				req2 += b"Host: " + self.host.encode() + b": " + str(self.port).encode()  + b"\r\n"
				req2 += b"User-Agent: AAAAAAAAAAAAAAAA\r\n"
				req2 += b"Content-Type: application/x-www-form-urlencoded\r\n"
				req2 += b"Accept: */*\r\n\r\n"  
									
				self.socket.sendall(req2)
					    
				self.socket.settimeout(10) 
				buf = self.socket.recv(1048576)
				self.socket.close()

				if len(buf) == 0:
					return None

				if buf.decode().__contains__("HTTP/1.1 200 OK"):
					txt = buf.decode().find("login.js?q=")
					subtxt = buf.decode()[txt:]
					txt2 = subtxt.find(">")
					mhash = subtxt[11:txt2-1]
				else:
					return None
			else :
				return None
			return mhash
	        	
		except socket.timeout as e:
				#print("[>] Target waited for more data. Not vulnerable.")
			return None
		except Exception as e:
			
				#print("[>] Target dropped the connection, which indicates a vulnerable device!")
	            #print(e)
			return None

	def gettime(self):

		try:
			req = b""
			req += b"GET /fonts/ftnt-icons.woff HTTP/1.1\r\n"
			req += b"Host: " + self.host.encode() + b":" + str(self.port).encode()  + b"\r\n"
			req += b"User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0\r\n"
			req += b"Accept-Encoding: gzip, deflate, br\r\n"
			req += b"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8\r\n\r\n"
								
			self.socket.sendall(req)
			            
			self.socket.settimeout(4)
			 
			responseheader = self.socket.recv(5000).decode()
			
			first = responseheader.find("HTTP/")
			second = responseheader[first:].find("\r\n")
			
			status = int(responseheader[first:second].split(' ')[1])
			
			if status > 400 :
				print("[!] Response not OK. " + self.host)
				return None
			else:
				temp1 = responseheader.find("Content-Length:")
				subtxt = responseheader[temp1:]
				temp2 = subtxt.find("\r\n")
				length = int(subtxt[16:temp2])
				
				if length < 10000:
					print("[!] Target is not fortigate.")
					return None
				
				woff = b""
				templen = length
				loopcnt = 0
				
				while templen > 0:
					buf = self.socket.recv(0x2000)
					woff += buf
					templen -= len(buf)
					if len(buf) == 0:
						if loopcnt == 5:
							break
						loopcnt += 1
					
				if len(woff) != length:
					print("[!] Recv woff failed.")
					return None
	
				return self.parsewoff(woff)	
	        	
		except socket.timeout as e:
			print("[!] Exception. " + str(e) + " " + self.host)
			return None
		except Exception as e:
			print("[!] Exception. " + str(e) + " " + self.host)
			return None

if __name__ == '__main__':

	try:
		ip = sys.argv[1]
		port = sys.argv[2]
		
		fgfmscan = Scanner(ip, 541)
		res = fgfmscan.connect()

		if res != None:
			print("[+] Fgfm is alive.")
			res.close()
		else:
			print("[-] Fgfm is dead.")

		scanner = Scanner(ip, int(port,10))
		
		res = scanner.connect() 
		if res == None:
			print("[!] Error connecting to target" + scanner.host)
			exit(1)
			
		mtime = scanner.gettime()
		

		if mtime != None:
			print("[+] Checksum is " + mtime)
			
		mhash = scanner.gethash()

		if mhash != None and mhash != "":
			print("[+] Hash is " + mhash)

		exit(1)

	except Exception as e:
		print(e)
		print("[!]Usage : targetinfoprinter.py <target> <port>")

