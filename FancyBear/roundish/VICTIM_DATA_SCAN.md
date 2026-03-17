# Victim Data Scan — phishing_framework/

**Scan date:** 2025-03-15  
**Purpose:** Confirm no victim data is present; only actor framework/tooling.

---

## Summary

**No exfiltrated victim data was found.** The directory contains only the actor’s phishing/C2 framework. A small number of **suspected non-victim references** (placeholder emails, lure content, template origins) are listed below for transparency.

---

## Checked Locations

| Location | Result |
|----------|--------|
| `taker/creds.csv` | **Empty** (0 bytes). No captured credentials. |
| `taker/visit.csv` | **Empty** (0 bytes). No visitor log. |
| `uploads/` | **Empty.** No Firefox profile uploads (logins.json/key4.db). |
| `files/` | **Empty.** No exfiltrated .eml files. |
| `url.txt` | **Not present.** No C2 telemetry log. |
| `root/` (exfil storage) | **Not present.** No exfil directory. |
| Any `*.eml` | **None** in tree. |

---

## Email Addresses in Code

| Email / reference | File(s) | Verdict |
|-------------------|--------|--------|
| `advenwolf@proton.me` | worker.js, old_worker.js, backuBDMS/worker.js, scriptTaker.js | **Actor.** Sieve redirect / collection mailbox; not victim data. |
| `emas@mail.com` | scriptTaker.js (inside obfuscated string array) | **Suspected placeholder/test.** Used in script logic when Sieve check fails (fallback log text). Treat as actor test value, not a real victim. |
| `mail.ascentio.com.ar` | logon.html (favicon link) | **Template origin.** Cloned Roundcube source for Argentine phishing page; not victim data. |

No other email addresses matching victim orgs (e.g. roaf.ro, gp.gov.ua, arma.gov.ua, hndgs.mil.gr, mod.gov.rs, pd.government.bg) appear in the codebase.

---

## Other References

| Item | Location | Verdict |
|------|----------|--------|
| `request_token`: `fab9c6abfd28aca434130bf7dcaa0813` | logon.html, roundcube.html | **Actor.** Static CSRF/token in phishing form. |
| `state.gov` (e.g. `PM_RSAT-TPT@state.gov`) | Adob_Scan_15_ian._2025.pdf (Romanian lure) | **Lure content.** Part of the actor-created document to look official; not exfiltrated victim data. |
| Form labels "Username", "Password" | server.py, servertest.py, logon.html, worker2.js, getUserCredentials*.js | **Code.** Format strings / UI labels for credential harvest; no stored victim data. |

---

## Conclusion

- **No victim credentials, visit logs, exfiltrated emails, or C2 telemetry** are in `phishing_framework/`.
- **Only actor infrastructure** (server, phishing pages, payloads, modules, lure PDFs) is present.
- **Suspected non-victim data:** `emas@mail.com` in scriptTaker.js (placeholder/test). Optional: replace with a generic placeholder (e.g. `test@example.com`) if you want to avoid any real-looking address.
