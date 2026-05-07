from celery import Celery
from celery.schedules import crontab
import os
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery('fluxhr', broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.beat_schedule = {
    'delete-old-candidates': {
        'task': 'celery_app.delete_old_candidates',
        'schedule': crontab(hour=2, minute=0),
    },
}
celery_app.conf.timezone = 'UTC'

@celery_app.task
def delete_old_candidates():
    from database import SessionLocal, Candidate
    db = SessionLocal()
    try:
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        deleted = db.query(Candidate).filter(Candidate.created_at < six_months_ago).delete()
        db.commit()
        print(f"[Retention] Eliminati {deleted} candidati")
        return deleted
    except Exception as e:
        db.rollback()
        print(f"[Retention] ERRORE: {e}")
        raise
    finally:
        db.close()

@celery_app.task
def send_art14_email(candidate_email: str, candidate_name: str = "Candidato"):
    SMTP_SERVER = os.getenv("SMTP_SERVER", "mailhog")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "privacy@fluxhr.com")

    subject = "Informativa privacy ai sensi dell'Art. 14 GDPR - FluxHR"
    body_text = f"""Gentile {candidate_name},

abbiamo ricevuto il Suo curriculum vitae tramite la piattaforma FluxHR.

Ai sensi dell'Art. 14 del Regolamento Generale sulla Protezione dei Dati (GDPR 2016/679), La informiamo che:

- I Suoi dati personali (nome, email, competenze, esperienze) verranno trattati esclusivamente per finalità di selezione del personale.
- I dati particolari (salute, opinioni politiche, credo religioso, ecc.) eventualmente presenti nel CV sono stati automaticamente rimossi dal sistema (sanitizzazione).
- Il trattamento è basato sul legittimo interesse del Titolare e sull'esecuzione di misure precontrattuali.
- I dati verranno conservati per un periodo massimo di 6 mesi, trascorsi i quali saranno cancellati automaticamente.
- Lei ha il diritto di chiedere al Titolare l'accesso, la rettifica, la cancellazione, la limitazione del trattamento o di opporsi al trattamento.
- Può esercitare tali diritti contattando il responsabile HR all'indirizzo privacy@fluxhr.com.

Cordiali saluti,
Il team di FluxHR
"""
    body_html = f"""<html>
<head></head>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #4f46e5;">FluxHR - Informativa privacy (Art. 14 GDPR)</h2>
    <p>Gentile <strong>{candidate_name}</strong>,</p>
    <p>abbiamo ricevuto il Suo curriculum vitae tramite la piattaforma FluxHR.</p>
    <p>Ai sensi dell'<strong>Art. 14 del Regolamento Generale sulla Protezione dei Dati (GDPR 2016/679)</strong>, La informiamo che:</p>
    <ul>
        <li>I Suoi dati personali (nome, email, competenze, esperienze) verranno trattati esclusivamente per finalità di selezione del personale.</li>
        <li>I dati particolari (salute, opinioni politiche, credo religioso, ecc.) eventualmente presenti nel CV sono stati automaticamente rimossi dal sistema (sanitizzazione).</li>
        <li>Il trattamento è basato sul legittimo interesse del Titolare e sull'esecuzione di misure precontrattuali.</li>
        <li>I dati verranno conservati per un periodo massimo di <strong>6 mesi</strong>, trascorsi i quali saranno cancellati automaticamente.</li>
        <li>Lei ha il diritto di chiedere al Titolare l'accesso, la rettifica, la cancellazione, la limitazione del trattamento o di opporsi al trattamento.</li>
        <li>Può esercitare tali diritti contattando il responsabile HR all'indirizzo <a href="mailto:privacy@fluxhr.com">privacy@fluxhr.com</a>.</li>
    </ul>
    <p>Cordiali saluti,<br>Il team di FluxHR</p>
    <hr style="margin-top: 30px;">
    <p style="font-size: 12px; color: #888;">Ricevi questo messaggio perché hai inviato una candidatura. Per maggiori informazioni, consultare la nostra privacy policy.</p>
</body>
</html>"""
    msg = EmailMessage()
    msg.set_content(body_text)
    msg.add_alternative(body_html, subtype='html')
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = candidate_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if SMTP_SERVER != "mailhog":
                server.starttls()
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[Celery] Email Art.14 inviata a {candidate_email}")
        return True
    except Exception as e:
        print(f"[Celery] ERRORE invio email: {e}")
        return False