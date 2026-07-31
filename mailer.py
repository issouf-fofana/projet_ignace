import smtplib
from email.message import EmailMessage


def send_contact_email(to_addr, subject, body, reply_to=None, smtp_host=None, smtp_port=None, smtp_user=None, smtp_password=None):
    """Envoie un e-mail via SMTP.

    Les identifiants sont fournis par l'appelant (paramètres de site
    configurables depuis l'admin), pas par des variables d'environnement,
    afin de pouvoir en changer sans redéployer.
    Retourne True si l'envoi a réussi, False si SMTP n'est pas configuré.
    """
    if not smtp_host or not smtp_port or not smtp_user or not smtp_password:
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_addr
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, int(smtp_port), timeout=10) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    return True
