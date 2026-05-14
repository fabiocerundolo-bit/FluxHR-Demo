from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm

# IMPORT SEPARATI E CORRETTI
from .cv_processor import process_cv_file
from .database import SessionLocal, init_db, get_db
from .models import Candidate 
from .auth import Token, authenticate_user, create_access_token, get_current_user

app = FastAPI(title="FluxHR API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusUpdate(BaseModel):
    status: str

class DashboardStats(BaseModel):
    total_candidates: int
    status_pie: List[dict]
    skills_bar: List[dict]
    status_distribution: dict

@app.on_event("startup")
def startup():
    init_db()

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        # 1. Conta totale candidati
        total = db.query(Candidate).count()

        # 2. Aggregazione Skill (Logica Real-time)
        all_candidates = db.query(Candidate.skills).all()
        skill_counts = {}

        for row in all_candidates:
            # row[0] è la lista delle skill del singolo candidato
            if row[0]:
                for skill in row[0]:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Trasforma in lista di oggetti per Recharts e prendi le top 5
        # Formato richiesto dal frontend: { name: "Python", count: 10 }
        skills_bar = [
            {"name": k, "count": v} 
            for k, v in sorted(skill_counts.items(), key=lambda item: item[1], reverse=True)
        ][:5]

        # 3. Distribuzione Stati
        status_pie = [
            {"name": "Nuovi", "value": db.query(Candidate).filter(Candidate.status == "new").count()},
            {"name": "Revisionati", "value": db.query(Candidate).filter(Candidate.status == "reviewed").count()},
            {"name": "Shortlist", "value": db.query(Candidate).filter(Candidate.status == "shortlisted").count()},
        ]

        return {
            "total_candidates": total,
            "status_pie": status_pie,
            "skills_bar": skills_bar,
            "status_distribution": {item["name"]: item["value"] for item in status_pie}
        }
    except Exception as e:
        print(f"Error in stats: {e}")
        return {"total_candidates": 0, "skills_bar": [], "status_distribution": {}}

@app.get("/candidates")
def get_candidates(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Candidate).order_by(Candidate.created_at.desc()).all()

@app.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        contents = await file.read()
        candidate = process_cv_file(contents, file.filename, db)
        
        # IMPORT RELATIVO CORRETTO PER IL TASK
        from .worker import send_art14_email
        send_art14_email.delay(candidate.email, candidate.name or "Candidato")
        
        return {"status": "ok", "candidate_id": candidate.id}
    except Exception as e:
        raise HTTPException(400, str(e))
class StatusUpdate(BaseModel):
    status: str

# --- NUOVI ENDPOINT DI GESTIONE ---

@app.patch("/candidates/{candidate_id}/status")
def update_status(candidate_id: int, update: StatusUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidato non trovato")
    
    candidate.status = update.status
    db.commit()
    return {"message": "Stato aggiornato", "new_status": candidate.status}

@app.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidato non trovato")
    
    # Eliminiamo il record (Il file fisico andrebbe rimosso qui per GDPR completo)
    db.delete(candidate)
    db.commit()
    return {"message": "Candidato rimosso con successo"}

# Endpoint per scaricare il file originale (usato nella dashboard)
from fastapi.responses import FileResponse
@app.get("/candidates/{candidate_id}/download")
def download_cv(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate or not candidate.cv_file_path:
        raise HTTPException(404, "File non trovato")
    return FileResponse(candidate.cv_file_path)