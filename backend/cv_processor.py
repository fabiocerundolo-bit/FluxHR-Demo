import os
import uuid
import re
import io
import pdfplumber
import docx
from sqlalchemy.orm import Session
from database import Candidate
from gdpr_sanitize import sanitize_cv

UPLOAD_DIR = "/app/uploads/candidates"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_email(text):
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None

def extract_phone(text):
    # Numero italiano o internazionale
    match = re.search(r'(\+?39\s?)?\d{3}[-\s]?\d{7,8}', text)
    if not match:
        match = re.search(r'(\+?\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4,}', text)
    return match.group(0) if match else None

def extract_name_from_text(text):
    # 1. Prova con pattern classico "Nome: Mario Rossi"
    match = re.search(r'(?:nome|name)[\s:]+([A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # 2. Cerca la prima riga che contiene due parole con iniziali maiuscole (es. "Sara Caruso")
    lines = text.split('\n')
    for line in lines[:20]:
        line = line.strip()
        # Ignora righe vuote o troppo corte
        if len(line) < 5:
            continue
        # Cerca due parole maiuscole separate da spazio
        match = re.match(r'^([A-Z][a-z]+\s+[A-Z][a-z]+)', line)
        if match:
            return match.group(1)
    return None
def capitalize_skill(skill: str) -> str:
    # Capitalizza la prima lettera di ogni parola, ma mantiene "BLS" e sigle in maiuscolo
    words = skill.split()
    capitalized = []
    for w in words:
        if w.isupper() or w.upper() == w:   # mantiene sigle come ACLS, BLS
            capitalized.append(w)
        else:
            capitalized.append(w.capitalize())
    return ' '.join(capitalized)

def extract_skills_from_section(text):
    """
    Estrae competenze cercando righe che contengono percentuali (es. 'Assistenza clinica 81%').
    Funziona su CV Europass senza dover riconoscere il titolo della sezione.
    """
    lines = text.split('\n')
    skills = []
    for line in lines:
        line = line.strip()
        # Cerca pattern: parole (anche con spazi) seguite da spazio e percentuale
        match = re.search(r'^([A-Za-zÀ-ÿ\s/&]+?)\s*\d+%', line)
        if match:
            skill = match.group(1).strip()
            if skill and len(skill) > 2:
                skills.append(skill.lower())
    # Se non trova nulla, prova con metodo tradizionale (per compatibilità con altri CV)
    if not skills:
        # Pattern flessibile per la sezione competenze
        pattern = r'(?:COMPETENZE TECNICHE|SKILLS|CAPACITÀ TECNICHE)[\s:]*\n(.*?)(?:\n\s*\n|\n[A-Z]{2,}|\Z)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            skills_text = match.group(1)
            for line in skills_text.split('\n'):
                line = line.strip()
                if line and not line.isupper():
                    clean = re.sub(r'\s*\d+%', '', line).strip()
                    if clean:
                        skills.append(capitalize_skill(skill))
    return skills[:15]

def extract_skills_legacy(text):
    # Lista di skill comuni (tecnologiche, sanitarie, ecc.)
    skills_list = [
        "python", "java", "sql", "docker", "react", "fastapi",
        "cucina italiana", "pasticceria", "haccp", "gestione cucina",
        "tedesco", "inglese", "ecdl", "icdl", "volontariato",
        "assistenza clinica", "pronto soccorso", "gestione farmaci", "bls", "acls"
    ]
    found = [skill for skill in skills_list if skill in text.lower()]
    return found[:10]

def process_cv_file(contents, filename, db: Session, source_email=None):
    # Estrai testo
    text = ""
    if filename.lower().endswith('.pdf'):
        try:
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
        except Exception as e:
            raise ValueError(f"Errore lettura PDF: {str(e)}")
    elif filename.lower().endswith('.docx'):
        try:
            doc = docx.Document(io.BytesIO(contents))
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            raise ValueError(f"Errore lettura DOCX: {str(e)}")
    else:
        raise ValueError("Formato file non supportato (usa PDF o DOCX)")

    if not text.strip():
        debug_dir = "/app/uploads/debug"
        os.makedirs(debug_dir, exist_ok=True)
        debug_path = os.path.join(debug_dir, f"failed_{uuid.uuid4().hex}_{filename}")
        with open(debug_path, "wb") as f:
            f.write(contents)
        raise ValueError("Il file non contiene testo estraibile (scansione?). Usa un PDF testuale.")

    # Sanitizzazione GDPR
    sanitized = sanitize_cv(text)

    # Estrai email e telefono
    email = extract_email(sanitized)
    if not email and source_email and '@' in source_email:
        email = source_email
    if not email:
        email = "unknown@example.com"

    phone = extract_phone(sanitized)

    # Estrai nome
    name = extract_name_from_text(sanitized)
    if not name:
        # Fallback: usa il nome del file (senza estensione e underscore)
        name = os.path.splitext(os.path.basename(filename))[0].replace('_', ' ').title()

    # Estrai competenze
    skills = extract_skills_from_section(sanitized)
    if not skills:
        skills = extract_skills_legacy(sanitized)

    # Salva file originale
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(contents)
    relative_path = f"uploads/candidates/{unique_name}"

    candidate = Candidate(
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        status="new",
        cv_file_path=relative_path
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate