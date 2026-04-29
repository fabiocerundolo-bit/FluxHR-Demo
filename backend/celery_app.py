from celery import Celery
import os
import smtplib
from email.message import EmailMessage

# Configurazione Redis (usa la stessa del docker-compose)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery('fluxhr', broker=REDIS_URL, backend=REDIS_URL)

# Configurazioni email (da variabili d'ambiente)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)

@celery_app.task
def send_art14_email(candidate_email: str, candidate_name: str = "Candidato"):
    """
    Invia l'informativa privacy GDPR Art.14 al candidato.
    """
    subject = "Informativa privacy - FluxHR"
    body = f"""Gentile {candidate_name},

abbiamo ricevuto la Sua candidatura tramite la piattaforma FluxHR.
Ai sensi dell'Art.14 del GDPR, La informiamo che:

- I Suoi dati verranno trattati esclusivamente per finalità di selezione del personale.
- I dati sensibili (salute, opinioni politiche, etc.) sono stati automaticamente rimossi.
- Potrà richiedere la cancellazione dei Suoi dati in qualsiasi momento.

Per maggiori informazioni, contatti il responsabile HR.

Cordiali saluti,
Il team di FluxHR
"""
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = candidate_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[Celery] Email Art.14 inviata a {candidate_email}")
        return True
    except Exception as e:
        print(f"[Celery] ERRORE invio email: {e}")
        return False