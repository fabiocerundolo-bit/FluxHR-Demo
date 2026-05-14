import os, requests, base64, smtplib
from celery import Celery
from .database import SessionLocal
from .models import Candidate
from .cv_processor import process_cv_file
from .templates.gdpr_email import get_art14_html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

celery_app = Celery('fluxhr', broker=os.getenv("REDIS_URL", "redis://redis:6379/0"))

@celery_app.task(name="app.worker.ingest_emails_task")
def ingest_emails_task():
    try:
        response = requests.get("http://mailhog:8025/api/v2/messages")
        messages = response.json().get('items', [])
        db = SessionLocal()
        for msg in messages:
            if 'MIME' in msg and 'Parts' in msg['MIME']:
                for part in msg['MIME']['Parts']:
                    content_disp = part.get('Headers', {}).get('Content-Disposition', [""])[0]
                    if "filename=" in content_disp:
                        filename = content_disp.split("filename=")[1].strip('"')
                        if filename.endswith(('.pdf', '.docx')):
                            body_raw = part.get('Body', '')
                            try:
                                file_bytes = base64.b64decode(body_raw)
                            except:
                                file_bytes = body_raw.encode()
                            
                            candidate = process_cv_file(file_bytes, filename, db)
                            # Lancio del task email HTML
                            send_art14_email_task.delay(candidate.email, candidate.name)
                            
                            # Rimuove l'email processata
                            requests.delete(f"http://mailhog:8025/api/v1/messages/{msg['ID']}")
        db.close()
    except Exception as e:
        print(f"Worker Error: {e}")

@celery_app.task(name="app.worker.send_art14_email_task")
def send_art14_email_task(email_dest, name):
    """Invia email professionale con HTML e CSS"""
    msg = MIMEMultipart('alternative')
    msg["Subject"] = "📌 Conferma Ricezione CV - FluxHR"
    msg["From"] = "FluxHR Privacy <privacy@fluxhr.com>"
    msg["To"] = email_dest

    html_content = get_art14_html(name)
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP("mailhog", 1025) as server:
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

celery_app.conf.beat_schedule = {
    'ingest-every-30s': {'task': 'app.worker.ingest_emails_task', 'schedule': 30.0}
}