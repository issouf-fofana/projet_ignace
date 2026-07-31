import os
import smtplib
from email.message import EmailMessage


def send_contact_email(to_addr, subject, body, reply_to=None):
    """Envoie un e-mail via SMTP configuré par variables d'environnement.

    Variables attendues : SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD.
    Retourne True si l'envoi a réussi, False sinon (ex. SMTP non configuré).
    """
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")

    if not host or not port or not user or not password:
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)

    with smtplib.SMTP(host, int(port), timeout=10) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
    return True
