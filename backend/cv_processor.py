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

def extract_email(text: str) -> str:
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None

def extract_phone(text: str) -> str:
    match = re.search(r'(\+?39\s?)?\d{3}[-\s]?\d{7,8}', text)
    if not match:
        match = re.search(r'(\+?\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4,}', text)
    return match.group(0) if match else None

def extract_name(text: str) -> str:
    match = re.search(r'^([A-Z][a-z]+\s+[A-Z][a-z]+)', text, re.MULTILINE)
    if match:
        return match.group(1)
    match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
    if match:
        return match.group(1)
    return None

def capitalize_skill(skill: str) -> str:
    words = skill.split()
    return ' '.join(w if w.isupper() else w.capitalize() for w in words)

def extract_skills(text: str) -> list:
    lines = text.split('\n')
    skills = []
    for line in lines:
        line = line.strip()
        match = re.search(r'^([A-Za-zÀ-ÿ\s/&]+?)\s*\d+%', line)
        if match:
            skill = match.group(1).strip()
            if skill and len(skill) > 2:
                skills.append(capitalize_skill(skill))
    if not skills:
        match = re.search(r'(?:COMPETENZE TECNICHE|SKILLS|CAPACITÀ TECNICHE)[\s:]*\n(.*?)(?:\n\s*\n|\n[A-Z]{2,}|\Z)', text, re.IGNORECASE | re.DOTALL)
        if match:
            skills_text = match.group(1)
            for line in skills_text.split('\n'):
                line = line.strip()
                if line and not line.isupper():
                    clean = re.sub(r'\s*\d+%', '', line).strip()
                    if clean:
                        skills.append(capitalize_skill(clean))
    # Rimuovi duplicati
    unique = []
    for s in skills:
        if s not in unique:
            unique.append(s)
    return unique[:15]

def process_cv_file(contents, filename, db: Session, source_email=None):
    text = ""
    if filename.lower().endswith('.pdf'):
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    elif filename.lower().endswith('.docx'):
        doc = docx.Document(io.BytesIO(contents))
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        raise ValueError("Formato non supportato")
    if not text.strip():
        raise ValueError("Testo vuoto")
    sanitized = sanitize_cv(text)
    email = extract_email(sanitized)
    if not email and source_email:
        email = source_email
    if not email:
        email = "unknown@example.com"
    phone = extract_phone(sanitized)
    name = extract_name(sanitized)
    if not name:
        name = os.path.splitext(os.path.basename(filename))[0].replace('_', ' ').title()
    skills = extract_skills(sanitized)
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