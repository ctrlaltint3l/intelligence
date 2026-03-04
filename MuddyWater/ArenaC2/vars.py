from datetime import date, datetime
import threading, os

SERVER_PORT = 0
SERVER_IP = ''

sessions, sessions_num, active_session, active_command, old_active_command = {}, 0, 0, "", ""
# startDay = date.today()
startTime = datetime.now()
# def get_log_file():
os.makedirs('packages/history', exist_ok=True)
os.makedirs('packages/history/DB', exist_ok=True)
# os.makedirs('packages/history/logs', exist_ok=True)
# os.makedirs('packages/history/inputs', exist_ok=True)
# return open(f'packages/history/logs/Log-{startDay}.txt', 'a', encoding='utf-8')
# logFile = get_log_file()

shell_handler_event, shell_creation_success, upload_start_success, upload_index_success = threading.Event(), threading.Event(), threading.Event(), threading.Event(),
# download_start_success, download_index_success, create_process_thread_success, goto_exe_understood = threading.Event(), threading.Event(), threading.Event(), threading.Event()

active_number_of_packets, active_local_file = 0, None
# active_pid_tid, active_exe_id = , 0, 0

healthy_db = True
