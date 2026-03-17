# APT28 / FancyBear Phishing Framework

This directory contains a copy of the phishing and C2 framework from the exposed operation box (203.161.50.145:8889). It is for research and documentation only.

---

## 1. How to Run It

### Requirements

- Python 3
- Flask, flask-cors, pycryptodome (for the `/` POST route that decrypts Firefox creds and writes loot.txt)

```bash
pip install flask flask-cors pycryptodome
```

### Start the server

```bash
cd phishing_framework
python server.py
```

- Listens on **0.0.0.0:5000** (all interfaces).
- Default index (`/`) serves **roundcube.html** and logs each visit to `taker/visit.csv`.

## 2. How the Phishing Flow Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│  VICTIM                                                                  │
└─────────────────────────────────────────────────────────────────────────┘
        │
        │  1. GET /
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  server.py  index()                                                      │
│  • log_visit() → appends to taker/visit.csv (IP, User-Agent, date)       │
│  • returns roundcube.html (fake Roundcube login page)                    │
└─────────────────────────────────────────────────────────────────────────┘
        │
        │  2. User submits username + password
        │     POST /authentification.php  (_user, _pass)
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  server.py  handle_authentification()                                    │
│  • If not duplicate: append to taker/creds.csv                         │
│  • Redirect → https://zhblz.com/Adob_Scan_15_ian._2025.pdf              │
└─────────────────────────────────────────────────────────────────────────┘
```

- **Phishing pages:** `roundcube.html` (default, ~847 KB, inline assets) and `logon.html` (Spanish, needs `rb_files/`).
- **Form action:** `authentification.php` (handled by Flask; no real PHP).
- **Post-login:** Redirect to a lure PDF on the C2 domain (in production the PDF was on zhblz.com; local copy included: `Adob_Scan_15_ian._2025.pdf`).

---

## 3. Where are the Payloads?

Payloads are the JS files that run in the context of a compromised webmail (Roundcube/SquirrelMail) after XSS. The **same server** that hosts the phishing pages also **serves these payloads** (and logs telemetry).

### 4.1 Payload delivery endpoints (server.py)

| URL | File served | Purpose |
|-----|-------------|---------|
| `/worker` | worker.js | Roundcube XSS payload (main) |
| `/worker2` | worker2.js | SquirrelMail XSS payload |
| `/<path>` | any file under `.` | Catch-all static; e.g. `/addRedirectMailBox.js` → addRedirectMailBox.js |

So **payloads live in the same directory as the server** and are served by the Flask catch-all `serve_static` or explicit routes for `/worker` and `/worker2`.

### 4.2 Payload files (what gets sent to the victim browser)

| File | Target | Role |
|------|--------|------|
| **worker.js** | Roundcube | Victim ID, creds (Chrome in-line + getUserCredentialsOLD), Sieve redirect (addRedirectMailBox), 2FA (keyTwoAuth), Inbox/Sent exfil to `/zJ2w9x/uploadfile/`. |
| **old_worker.js** | Roundcube | Same as worker.js (earlier variant). |
| **worker2.js** | SquirrelMail | Victim ID (takeUsername), creds (Chrome + getUserCredentials), address book only; no mailbox exfil. |
| **scriptTaker.js** | Roundcube | Obfuscated; uses long C2 path for logging; Sieve + creds + 2FA. |

### 4.3 Modules (loaded by payloads from zhblz.com / same server)

These are **fetched by the payloads** from the same host (e.g. https://zhblz.com/...) when the C2 domain points to this server:

| File | Fetched by | Function |
|------|------------|----------|
| addRedirectMailBox.js | worker, old_worker | Create Sieve rule to forward mail to actor. |
| getUserCredentials.js | worker2 | Firefox credential extraction. |
| getUserCredentialsOLD.js | worker, old_worker | Roundcube login-form credential extraction. |
| keyTwoAuth.js | worker, old_worker, backuBDMS/worker | Read Roundcube 2FA plugin (five password fields). |
| adbook.js | backuBDMS/worker.js | Roundcube address book exfil. |
| delTwoAuth.js / delTwoAuth1.js | (available) | 2FA deletion/manipulation. |

So **payload location on disk** = project root (e.g. `worker.js`, `worker2.js`, `addRedirectMailBox.js`, etc.). **Payload “delivery”** = HTTP GET to `/worker`, `/worker2`, or direct request to the module JS filenames.

### 4.4 C2 endpoints used by payloads (in code)

- **Logging:** GET `https://zhblz.com/zJ2w9x?log=...` (worker/old_worker/worker2 use short path; scriptTaker uses long path).
- **Email upload:** POST `https://zhblz.com/zJ2w9x/uploadfile/` (body: `.eml` file).
- **Module fetch:** GET `https://zhblz.com/addRedirectMailBox.js`, etc.

In a live setup, zhblz.com would point to this Flask app (or a reverse proxy in front of it). This copy does not include url.txt, root/roundish/files, or real taker data; those are created at runtime.

---

## 5. Directory Layout (This Copy)

```
phishing_framework/
├── server.py              # Main Flask app (phishing + C2)
├── servertest.py          # Variant with secure-header check on /zJ2w9x
├── roundcube.html         # Default phishing page (Roundcube clone)
├── logon.html             # Alternate phishing page (Spanish; needs rb_files/)
├── styles.min.css
├── jquery-ui-1.10.4.custom.css
├── roundcube_logo.png
├── linen.jpg, linen_login.jpg
│
├── taker/
│   ├── creds.csv          # Captured credentials (empty here)
│   └── visit.csv          # Visit log (empty here)
│
├── uploads/               # Firefox logins.json/key4.db per victim (folder_N)
├── files/                 # Exfiltrated .eml from Roundcube (uploadfile)
│
├── # Lure PDFs (post-login redirect target; also usable as static)
├── Adob_Scan_15_ian._2025.pdf
├── defense.pdf
├── dokladMVR.pdf
├── energetikamk.pdf
├── oborona.pdf
│
├── # Payloads (XSS → loaded in victim webmail)
├── worker.js
├── old_worker.js
├── worker2.js
├── scriptTaker.js
├── backuBDMS/
│   └── worker.js
│
└── # Modules (fetched by payloads from C2 host)
    ├── addRedirectMailBox.js
    ├── getUserCredentials.js
    ├── getUserCredentials1.js
    ├── getUserCredentialsOLD.js
    ├── keyTwoAuth.js
    ├── adbook.js
    ├── delTwoAuth.js
    ├── delTwoAuth1.js
    └── remFu.js
```

---

## 6. Other server.py Routes (Reference)

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Phishing landing: log_visit(), serve roundcube.html. |
| `/authentification.php` | POST | Credential harvest; redirect to lure PDF. |
| `/worker` | GET | Serve worker.js. |
| `/worker2` | GET | Serve worker2.js. |
| `/zJ2w9x` | GET | Append request URL to url.txt (telemetry). |
| `/zJ2w9x/uploadfile/` | POST | Save uploaded file (e.g. .eml) to `files/`. |
| `/addRedirectMailBox.js` etc. | GET | Serve module JS. |
| `/upload` | POST | JSON: filename + base64 content; save to uploads/folder_N (Firefox). |
| `/` (web blueprint) | POST | AES-GCM decrypt; append to loot.txt. |
| `/<path:filename>` | GET | Serve any other file from current directory. |

---
