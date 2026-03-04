from peewee import *
import os

from packages import vars
from packages.utill import log_and_print as print

db = SqliteDatabase('packages/history/DB/HttpsCC.db', pragmas={'journal_mode': 'wal','cache_size': -1024 * 64})

class CommonTB(Model):
    sessions_num=IntegerField()
    active_session=IntegerField()
    SERVER_PORT=IntegerField()
    SERVER_IP=CharField(max_length=20)
    class Meta:
        database=db
        db_table='common-vars'

class SessionsTB(Model):
    sessionId=IntegerField()
    ip=CharField(max_length=20)
    port=IntegerField()
    mid=IntegerField()
    createTime=DateTimeField()
    lastCheckTime=DateTimeField()
    isServer=BooleanField(default=False)
    isAdmin=BooleanField(default=False)
    isSystem=BooleanField(default=False)
    isDomain=BooleanField(default=False)
    is32=BooleanField(default=False)
    isVM=BooleanField(default=False)
    osVersion=CharField(max_length=50)
    user=TextField()
    computerName=TextField()
    domain=TextField()
    sleepTime=CharField(max_length=20)
    greeting=BlobField()
    # exes_num=IntegerField()
    class Meta:
        database=db
        db_table='sessions'

# class ExesTB(Model):
#     sessionId=IntegerField()
#     exeId=IntegerField()
#     type=CharField(max_length=20)
#     path=TextField()
#     pid=IntegerField()
#     interactive=BooleanField()
#     args=TextField()
#     createTime=DateTimeField()
#     class Meta:
#         database=db
#         db_table='exes'

def handle_db(clear_db = False):
    try:
        db.connect()
    except:
        print("can not connect to database.", color='red')
        vars.healthy_db = False
        return
    tables = db.get_tables()
    if 'common-vars' not in tables or 'sessions' not in tables:
        db.create_tables([SessionsTB, CommonTB])
    if clear_db:
        rows1, rows2 = SessionsTB.select(), CommonTB.select()
        for row in rows1:
            row.delete_instance()
        for row in rows2:
            row.delete_instance()

def healthy_db(func):
    def run(*args, **kwargs):
        if vars.healthy_db:
            func(*args, **kwargs)
    return run

@healthy_db
def load_sessions():
    rows = SessionsTB.select()
    for row in rows:
        read_pipe, write_pipe = os.pipe()
        # exes, exes_all = {}, ExesTB.select()
        # for exe in exes_all:
        #     if exe.sessionId == row.sessionId:
        #         exes[exe.exeId] = {
        #             'type' : exe.type,
        #             'path' : exe.path,
        #             'pid' : exe.pid,
        #             'interactive' : exe.interactive,
        #             'args' : exe.args,
        #             'createTime' : exe.createTime
        #         }
        vars.sessions[row.sessionId] = {
            "client_address": (row.ip, row.port),
            "mid" : row.mid,
            "create_time" : row.createTime,
            "last_check_time" : row.lastCheckTime,
            "isAdmin" : row.isAdmin,
            "isSystem": row.isSystem,
            "isDomain" : row.isDomain,
            "isServer" : row.isServer,
            "osVersion" : row.osVersion,
            "is32" : row.is32,
            "isVM" : row.isVM,
            "user" : row.user,
            "computerName" : row.computerName,
            "domain" : row.domain,
            "sleep_time" : row.sleepTime,
            "greeting": row.greeting,
            "read_pipe": read_pipe,
            "write_pipe": write_pipe,
            "command_sizes": [],
            # "exes": exes,
            # "exes_num": row.exes_num
        }

@healthy_db
def add_session(id, session):
    SessionsTB(sessionId=id, ip=session["client_address"][0], port=session["client_address"][1], mid=session["mid"], createTime=session["create_time"], lastCheckTime=session["last_check_time"], 
                isServer=session["isServer"] != 0, isAdmin=session["isAdmin"] != 0, isSystem=session["isSystem"] != 0, isDomain=session["isDomain"] != 0, is32=session["is32"] != 0, isVM=session["isVM"] != 0, 
                osVersion=session["osVersion"], user=session["user"], computerName=session["computerName"], domain=session["domain"], sleepTime=session["sleep_time"], greeting=session["greeting"], 
                # exes_num=session['exes_num']
                ).save()

# @healthy_db
# def add_exe(sid, id, exe):
#     ExesTB(sessionId=sid, exeId=id, type=exe['type'], path=exe['path'], pid=exe['pid'], interactive=exe['interactive'], args=exe['args'], createTime=exe["createTime"]).save()

# @healthy_db
# def remove_exe(sid, id):
#     records = ExesTB.select().where(ExesTB.sessionId == sid and ExesTB.exeId == id)
#     if len(records) == 1:
#         records[0].delete_instance()

@healthy_db
def update_session_exists(id, session):
    records = SessionsTB.select().where(SessionsTB.sessionId == id)
    if(len(records) == 1):
        record = records[0]
        record.sleepTime = session["sleep_time"]
        record.lastCheckTime = session["last_check_time"]
        record.mid = session["mid"]
        record.port = session["client_address"][1]
        record.save()

@healthy_db
def update_session_sleep_time(time):
    records = SessionsTB.select().where(SessionsTB.sessionId == vars.active_session)
    if(len(records) == 1):
        record = records[0]
        record.sleepTime = time
        record.save()

# @healthy_db
# def update_session_exe_num(num):
#     records = SessionsTB.select().where(SessionsTB.sessionId == vars.active_session)
#     if(len(records) == 1):
#         record = records[0]
#         record.exes_num = num
#         record.save()

@healthy_db
def update_session_processor(id, session):
    records = SessionsTB.select().where(SessionsTB.sessionId == id)
    if(len(records) == 1):
        record = records[0]
        record.lastCheckTime = session["last_check_time"]
        record.mid = session["mid"]
        record.save()

@healthy_db
def load_common_vars():
    rows = CommonTB.select()
    if len(rows) == 1:
        vars.sessions_num=rows[0].sessions_num
        vars.active_session=rows[0].active_session
        vars.SERVER_PORT=rows[0].SERVER_PORT
        vars.SERVER_IP=rows[0].SERVER_IP

@healthy_db
def update_common_vars():
    rows = CommonTB.select()
    if len(rows) == 1:
        rows[0].sessions_num=vars.sessions_num
        rows[0].active_session=vars.active_session
        rows[0].SERVER_PORT=vars.SERVER_PORT
        rows[0].SERVER_IP=vars.SERVER_IP
        rows[0].save()
    else:
        CommonTB(SERVER_IP=vars.SERVER_IP, SERVER_PORT=vars.SERVER_PORT, active_session=vars.active_session, sessions_num=vars.sessions_num).save()

@healthy_db
def update_common_vars_active_session():
    rows = CommonTB.select()
    if len(rows) == 1:
        rows[0].active_session=vars.active_session
        rows[0].save()

@healthy_db
def update_common_vars_sessions_num():
    rows = CommonTB.select()
    if len(rows) == 1:
        rows[0].sessions_num=vars.sessions_num
        rows[0].save()

# @healthy_db
# def update_exe_id(exeid, newid):
#     rows = ExesTB.select().where(ExesTB.sessionId == vars.active_session and ExesTB.exeId == exeid)
#     if len(rows) == 1:
#         rows[0].exeId=newid
#         rows[0].save()

