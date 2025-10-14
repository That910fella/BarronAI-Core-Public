from __future__ import annotations
import os, smtplib
from email.mime.text import MIMEText

def send_email(subject: str, body: str):
    if not os.getenv("EMAIL_ALERTS","False").lower() in {"1","true","yes"}:
        return {"status":"disabled"}
    host = os.getenv("SMTP_HOST"); port = int(os.getenv("SMTP_PORT","587"))
    user = os.getenv("SMTP_USER"); pwd  = os.getenv("SMTP_PASS")
    to   = os.getenv("ALERT_EMAIL_TO")
    if not all([host,port,user,pwd,to]):
        return {"status":"missing-config"}
    msg = MIMEText(body)
    msg["Subject"] = subject; msg["From"] = user; msg["To"] = to
    with smtplib.SMTP(host, port) as s:
        s.starttls(); s.login(user, pwd); s.sendmail(user, [to], msg.as_string())
    return {"status":"sent"}
