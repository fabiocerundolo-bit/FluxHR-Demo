import smtplib
import os
import mimetypes
from email.message import EmailMessage

# --- CONFIGURAZIONE ---
SMTP_SERVER = "localhost"
SMTP_PORT = 1025  # Mailhog
TARGET_EMAIL = "jobs@fluxhr.local"
SOURCE_FOLDER = "./campioni_cv"  # Cartella dove metti i tuoi file reali

# Lista di email fittizie per simulare candidati diversi
ALIASES = [
    "candidato.uno@gmail.com",
    "info.test@outlook.it",
    "mario.rossi.work@yahoo.com",
    "tech.talent@protonmail.com",
    "hr.selection.test@legalmail.it"
]

def send_cv_from_file(file_path, sender_email):
    file_name = os.path.basename(file_path)
    print(f"📦 Elaborazione file: {file_name}...")

    # 1. Creazione del messaggio
    msg = EmailMessage()
    msg['Subject'] = f"Candidatura per posizione aperta - {file_name}"
    msg['From'] = sender_email
    msg['To'] = TARGET_EMAIL
    msg.set_content(f"Buongiorno, in allegato invio il mio CV ({file_name}) per la vostra selezione.")

    # 2. Rilevamento tipo di file e caricamento
    ctype, encoding = mimetypes.guess_type(file_path)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)

    with open(file_path, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=file_name
        )

    # 3. Invio a Mailhog
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.send_message(msg)
        print(f"✅ Inviato con successo da: {sender_email}")
    except Exception as e:
        print(f"❌ Errore durante l'invio di {file_name}: {e}")

def run():
    if not os.path.exists(SOURCE_FOLDER):
        print(f"❌ Errore: La cartella '{SOURCE_FOLDER}' non esiste. Creala e inserisci i PDF.")
        return

    files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith(('.pdf', '.docx'))]
    
    if not files:
        print(f"⚠️  Nessun file PDF o DOCX trovato in '{SOURCE_FOLDER}'.")
        return

    print(f"🚀 Trovati {len(files)} file. Inizio invio pipeline...\n")

    for i, file_name in enumerate(files):
        path = os.path.join(SOURCE_FOLDER, file_name)
        # Sceglie un alias a rotazione o ne crea uno basato sul nome file
        sender = ALIASES[i % len(ALIASES)]
        
        send_cv_from_file(path, sender)

    print("\n🏁 Simulazione completata!")
    print("Controlla Mailhog (http://localhost:8025) e la Dashboard (http://localhost:3000).")

if __name__ == "__main__":
    run()