import os
import uuid
import re
import io
import pdfplumber
import docx
from sqlalchemy.orm import Session
from .models import Candidate
from .gdpr_sanitize import sanitize_cv

UPLOAD_DIR = "/app/uploads/candidates"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- FUNZIONI DI SUPPORTO PER L'ESTRAZIONE ---

def extract_email(text: str) -> str:
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None

def extract_phone(text: str) -> str:
    match = re.search(r'(\+?39\s?)?\d{3}[-\s]?\d{7,8}', text)
    if not match:
        match = re.search(r'(\+?\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4,}', text)
    return match.group(0) if match else None

def extract_name(text: str) -> str:
    """Cerca il nome nelle prime righe ignorando i titoli comuni"""
    noise = ["curriculum", "vitae", "europass", "profilo", "cv", "informazioni", "personali"]
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:5]:
        if not any(n in line.lower() for n in noise):
            if re.match(r'^([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+)', line):
                return line
    return None

def extract_skills(text: str) -> list:
    """Estrae le skill cercando parole chiave nel testo (Real-time tracking)"""
    keywords = [
        "Python", "FastAPI", "React", "Docker", "SQL", "PostgreSQL", 
        "JavaScript", "TypeScript", "Kubernetes", "AWS", "Figma", 
        "Tailwind", "Node.js", "Java", "Linux", "UI/UX", "Excel", "PHP"
    ]
    found_skills = []
    text_lower = text.lower()
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower):
            found_skills.append(kw)
    return list(set(found_skills))[:10]

# --- FUNZIONE PRINCIPALE RICHIESTA ---

def process_cv_file(contents: bytes, filename: str, db: Session, source_email=None):
    """
    Processa un file CV: Estrazione testo -> Sanitizzazione -> Estrazione Dati -> 
    Salvataggio File -> Salvataggio Database.
    """
    text = ""
    ext = os.path.splitext(filename)[1].lower()

    # 1. Estrazione del testo grezzo in base al formato
    try:
        if ext == '.pdf':
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                # Estraiamo testo da tutte le pagine
                text = "".join([page.extract_text() or "" for page in pdf.pages])
        elif ext == '.docx':
            doc = docx.Document(io.BytesIO(contents))
            text = "".join([para.text + "\n" for para in doc.paragraphs])
        else:
            raise ValueError(f"Formato file {ext} non supportato")
    except Exception as e:
        print(f"ERRORE ESTRAZIONE TESTO: {e}")
        text = "Testo non leggibile"

    # 2. Sanitizzazione GDPR (oscuramento dati sensibili)
    sanitized_text = sanitize_cv(text)

    # 3. Estrazione dati strutturati dal testo sanitizzato
    name = extract_name(text) # Cerchiamo il nome sul testo originale per precisione
    email = extract_email(text) or source_email or "unknown@example.com"
    phone = extract_phone(text)
    skills = extract_skills(text)

    # Fallback per il nome se non trovato nel testo
    if not name:
        name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()

    # 4. Salvataggio fisico del file nel volume Docker
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    
    with open(file_path, "wb") as f:
        f.write(contents)

    # 5. Creazione record nel Database tramite SQLAlchemy
    candidate = Candidate(
        name=name,
        email=email,
        phone=phone,
        skills=skills, # Salvato come JSON
        status="new",
        cv_file_path=file_path
    )
    
    try:
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        print(f"✅ Candidato salvato: {name} ({email})")
    except Exception as e:
        db.rollback()
        print(f"❌ ERRORE DATABASE: {e}")
        raise e

    return candidate