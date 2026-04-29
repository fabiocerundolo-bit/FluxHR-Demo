from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import re
import io
import pdfplumber
import docx
from pydantic import BaseModel
from celery_app import send_art14_email

from database import SessionLocal, Candidate, init_db
from gdpr_sanitize import sanitize_cv
from auth import (
    Token, authenticate_user, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

# ---------- App initialization ----------
app = FastAPI(title="FluxHR API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Error handler for 422 ----------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("=" * 50)
    print("❌ ERRORE 422 - Validazione fallita")
    print("Dettagli:", exc.errors())
    print("=" * 50)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# ---------- DB dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Pydantic models ----------
class CandidateOut(BaseModel):
    id: int
    name: Optional[str]
    email: str
    skills: List[str]
    status: str
    created_at: datetime

class StatusUpdate(BaseModel):
    status: str

    class Config:
        from_attributes = True

# ---------- Startup ----------
@app.on_event("startup")
def startup():
    init_db()

# ---------- Health ----------
@app.get("/health")
def health():
    return {"status": "FluxHR ready"}

# ---------- Authentication ----------
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ---------- Protected endpoints ----------
@app.get("/candidates", response_model=List[CandidateOut])
def get_candidates(
    db: Session = Depends(get_db),
    limit: int = 10,      # invece di 100, per paginazione
    skip: int = 0,
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    query = db.query(Candidate)
    
    # Filtro per status (se fornito)
    if status:
        query = query.filter(Candidate.status == status)
    
    # Ricerca testuale su nome ed email (case-insensitive)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Candidate.name.ilike(search_pattern)) |
            (Candidate.email.ilike(search_pattern))
        )
    
    # Paginazione
    candidates = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()
    return candidates

@app.patch("/candidates/{candidate_id}/status")
def update_candidate_status(
    candidate_id: int,
    update: StatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidato non trovato")
    
    allowed_statuses = ["new", "reviewed", "shortlisted", "rejected"]
    if update.status not in allowed_statuses:
        raise HTTPException(400, f"Stato non valido. Usa: {', '.join(allowed_statuses)}")
    
    candidate.status = update.status
    db.commit()
    return {"ok": True, "new_status": candidate.status}

# ---------- Helper extraction functions ----------
def extract_email(text: str) -> Optional[str]:
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None

def extract_phone(text: str) -> Optional[str]:
    match = re.search(r'(\+?\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4,}', text)
    return match.group(0) if match else None

def extract_name_fallback(text: str, email: Optional[str] = None) -> Optional[str]:
    # Prova a cercare due parole maiuscole all'inizio
    match = re.search(r'^([A-Z][a-z]+\s+[A-Z][a-z]+)', text, re.MULTILINE)
    if match:
        return match.group(1)
    # Cerca due parole maiuscole ovunque
    match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
    if match:
        return match.group(1)
    # Fallback dall'email
    if email:
        local = email.split('@')[0]
        parts = re.split(r'[._-]', local)
        parts = [p.capitalize() for p in parts if p]
        if parts:
            return ' '.join(parts)
    return None

def extract_skills(text: str) -> List[str]:
    skills_list = [
        "python", "java", "sql", "docker", "react", "fastapi",
        "javascript", "typescript", "machine learning", "gcp",
        "aws", "postgresql", "mongodb", "html", "css", "tailwind",
        "kubernetes", "terraform", "golang", "redis", "django"
    ]
    found = [skill for skill in skills_list if skill in text.lower()]
    return found[:10]

# ---------- Upload CV endpoint (final, single version) ----------
@app.post("/upload-cv")
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Validazione estensione
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(400, "Solo file PDF o DOCX sono supportati")

    contents = await file.read()

    # Limite 5 MB
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "File troppo grande (max 5MB)")

    # Controllo minimo PDF
    if file.filename.endswith('.pdf') and not contents.startswith(b'%PDF'):
        raise HTTPException(400, "Il file non sembra un PDF valido")

    # Estrazione testo
    text = ""
    if file.filename.endswith('.pdf'):
        try:
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
        except Exception as e:
            raise HTTPException(400, f"Errore nella lettura del PDF: {str(e)}")
    else:  # .docx
        try:
            doc = docx.Document(io.BytesIO(contents))
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            raise HTTPException(400, f"Errore nella lettura del DOCX: {str(e)}")

    if not text.strip():
        raise HTTPException(400, "Nessun testo estratto dal file")

    # Sanitizzazione GDPR
    sanitized_text = sanitize_cv(text)

    # Estrazione campi
    email = extract_email(sanitized_text)
    if not email:
        email = "unknown@example.com"

    phone = extract_phone(sanitized_text)

    # Nome
    name = None
    # Prova pattern "Nome:"
    match = re.search(r'(?:nome|name)[\s:]+([A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+)', sanitized_text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
    if not name:
        name = extract_name_fallback(sanitized_text, email)

    skills = extract_skills(sanitized_text)

    # Salvataggio DB
    candidate = Candidate(
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        status="new"
    )
    db.add(candidate)
    db.commit()
    from celery_app import send_art14_email
    send_art14_email.delay(candidate.email, candidate.name or "Candidato")
    db.refresh(candidate)

    print(f"[GDPR Art.14] Email informativa inviata a {candidate.email} (simulata)")

    return {
        "status": "CV processato e candidato salvato",
        "candidate_id": candidate.id,
        "dati_estratti": {
            "nome": name,
            "email": email,
            "telefono": phone,
            "competenze": skills
        },
        "testo_sanitizzato_anteprima": sanitized_text[:300] + "..."
    }