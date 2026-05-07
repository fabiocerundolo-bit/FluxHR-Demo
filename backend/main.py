from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from cv_processor import process_cv_file
from database import SessionLocal, Candidate, init_db
from auth import Token, authenticate_user, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI(title="FluxHR API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("=" * 50)
    print("❌ ERRORE 422 - Validazione fallita")
    print("Dettagli:", exc.errors())
    print("=" * 50)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CandidateOut(BaseModel):
    id: int
    name: Optional[str]
    email: str
    skills: List[str]
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: str

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "FluxHR ready"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/candidates", response_model=List[CandidateOut])
def get_candidates(db: Session = Depends(get_db), limit: int = 10, skip: int = 0, search: Optional[str] = None, status: Optional[str] = None, current_user = Depends(get_current_user)):
    query = db.query(Candidate)
    if status:
        query = query.filter(Candidate.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter((Candidate.name.ilike(search_pattern)) | (Candidate.email.ilike(search_pattern)))
    candidates = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()
    return candidates

@app.patch("/candidates/{candidate_id}/status")
def update_candidate_status(candidate_id: int, update: StatusUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidato non trovato")
    allowed_statuses = ["new", "reviewed", "shortlisted", "rejected"]
    if update.status not in allowed_statuses:
        raise HTTPException(400, f"Stato non valido. Usa: {', '.join(allowed_statuses)}")
    candidate.status = update.status
    db.commit()
    return {"ok": True, "new_status": candidate.status}

@app.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, detail="Candidato non trovato")
    db.delete(candidate)
    db.commit()
    return {"ok": True, "message": f"Candidato {candidate_id} eliminato"}

@app.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        if not file.filename.endswith(('.pdf', '.docx')):
            raise HTTPException(400, "Solo file PDF o DOCX")
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(400, "File troppo grande (max 5MB)")
        candidate = process_cv_file(contents, file.filename, db)
        from celery_app import send_art14_email
        send_art14_email.delay(candidate.email, candidate.name or "Candidato")
        return {
            "status": "ok",
            "candidate_id": candidate.id,
            "dati_estratti": {
                "nome": candidate.name,
                "email": candidate.email,
                "telefono": candidate.phone,
                "competenze": candidate.skills
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(400, str(e))