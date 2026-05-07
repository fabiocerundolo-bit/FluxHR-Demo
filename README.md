# FluxHR

> Piattaforma SaaS per l'automazione della selezione del personale nelle PMI.

FluxHR riceve CV in formato PDF o DOCX, estrae automaticamente dati anagrafici e competenze, sanitizza i dati sensibili per conformità GDPR e invia un'informativa privacy al candidato (Art. 14) tramite email asincrona. Una dashboard web permette ai recruiter di gestire l'intero pipeline di selezione.

![Stato](https://img.shields.io/badge/stato-MVP%20funzionante-brightgreen)
![Licenza](https://img.shields.io/badge/licenza-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![React](https://img.shields.io/badge/React-19-61DAFB)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

---

## Indice

- [Funzionalità](#funzionalità)
- [Architettura](#architettura)
- [Stack tecnologico](#stack-tecnologico)
- [Installazione](#installazione)
- [Utilizzo](#utilizzo)
- [API Reference](#api-reference)
- [Conformità GDPR](#conformità-gdpr)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)
- [Licenza](#licenza)

---

## Funzionalità

- **Upload CV** drag-and-drop (PDF e DOCX, max 5 MB)
- **Estrazione automatica** di nome, email, telefono e competenze
- **Sanitizzazione GDPR** — rimozione di riferimenti a salute, politica e religione prima dello storage
- **Email Art. 14** inviata al candidato entro 30 secondi dall'upload (Celery + SMTP)
- **Dashboard** con ricerca full-text, filtri per stato, paginazione
- **Gestione stati** candidato: `new → reviewed → shortlisted → rejected`
- **Tema scuro/chiaro** e modalità presentazione
- **Autenticazione JWT** stateless

---

## Architettura

```
[Browser]
   ↓ HTTP
[Frontend — React 19]          :3000
   ↓ REST API
[Backend — FastAPI]             :8000
   ├─ [PostgreSQL 16]           :5432   ← candidati, utenti
   ├─ [Redis]                   :6379   ← code Celery
   └─ [Celery Worker]                   ← invio email Art.14
```

Tutti i servizi sono containerizzati e orchestrati tramite **Docker Compose**.

---

## Stack tecnologico

| Categoria | Tecnologia | Note |
|---|---|---|
| Backend | FastAPI + Python 3.12 | Swagger automatico, integrazione Pydantic |
| Frontend | React 19 + TypeScript + Tailwind | Vite, componenti riutilizzabili |
| Database | PostgreSQL 16 | Supporto pgcrypto per crittografia colonne |
| Code | Redis + Celery | Invio email asincrono |
| Parser CV | pdfplumber + python-docx | Nessuna dipendenza esterna, dati in locale |
| Auth | JWT / OAuth2 password flow | Stateless, hash bcrypt per le password |
| Container | Docker + Docker Compose | Ambiente identico in dev e produzione |

---

## Installazione

### Prerequisiti

- Docker ≥ 20.10 e Docker Compose
- Git

### 1. Clona il repository

```bash
git clone https://github.com/fabiocerundolo-bit/FluxHR-Demo.git
cd FluxHR-Demo
```

### 2. Configura le variabili d'ambiente

Crea un file `.env` nella root del progetto:

```env
# Database
DATABASE_URL=postgresql://fluxhr:fluxhr_secret@postgres:5432/fluxhr_db

# Redis & Celery
REDIS_URL=redis://redis:6379/0

# SMTP — usare App Password, non la password personale
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tuoaccount@gmail.com
SMTP_PASSWORD=<app-password-gmail>
FROM_EMAIL=privacy@tuaazienda.com
```

> ⚠️ **Non committare mai il file `.env`** — aggiungilo al `.gitignore`.  
> Per Gmail è obbligatorio usare una [App Password](https://support.google.com/accounts/answer/185833), non la password personale.

### 3. Avvia i container

```bash
docker-compose up --build -d
```

Verifica lo stato:

```bash
docker-compose ps
docker-compose logs -f          # tutti i servizi
docker-compose logs -f backend  # solo il backend
```

### 4. Primo accesso

Apri [http://localhost:3000](http://localhost:3000) e accedi con le credenziali predefinite:

```
Username: admin
Password: fluxhr2025
```

> ⚠️ **Cambia immediatamente** le credenziali di default prima di qualsiasi deploy in produzione.

---

## Utilizzo

### Upload di un CV

1. Trascina un file PDF o DOCX nell'area drag-and-drop
2. Il backend estrae e sanitizza i dati automaticamente
3. Il candidato appare nella tabella con status `new`
4. Entro 30 secondi viene inviata l'email Art. 14 al candidato

### Gestione candidati

Usa i pulsanti **Reviewed**, **Shortlist** e **Reject** per aggiornare lo stato. La barra di ricerca filtra per nome o email; il menu stato filtra per fase del processo.

---

## API Reference

Tutti gli endpoint richiedono `Authorization: Bearer <token>`, tranne `/health` e `/token`.

### Autenticazione

```bash
# Login
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=<password>"

# Risposta
{ "access_token": "eyJhbGc...", "token_type": "bearer" }
```

### Candidati

```bash
# Lista con filtri e paginazione
GET /candidates?skip=0&limit=10&search=rossi&status=new

# Aggiorna stato
PATCH /candidates/{id}/status
Body: { "status": "shortlisted" }

# Upload CV
POST /upload-cv
Content-Type: multipart/form-data
Campo: file (PDF o DOCX, max 5 MB)
```

**Esempio risposta `GET /candidates`:**

```json
[
  {
    "id": 1,
    "name": "Mario Rossi",
    "email": "mario.rossi@example.com",
    "skills": ["python", "fastapi"],
    "status": "new",
    "created_at": "2026-04-30T10:15:00"
  }
]
```

**Esempio risposta `POST /upload-cv`:**

```json
{
  "status": "CV processato e candidato salvato",
  "candidate_id": 5,
  "dati_estratti": {
    "nome": "Mario Rossi",
    "email": "mario.rossi@email.it",
    "telefono": "+39 333 123 4567",
    "competenze": ["python", "docker", "react"]
  }
}
```

La documentazione Swagger completa è disponibile su [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Conformità GDPR

FluxHR è progettato con approccio **Privacy by Design** (GDPR — UE 2016/679).

| Principio | Implementazione |
|---|---|
| Minimizzazione | Vengono memorizzati solo: nome, email, telefono, competenze, stato, timestamp |
| Sanitizzazione | `gdpr_sanitize.py` rimuove riferimenti a salute, politica e religione |
| Informativa Art. 14 | Email automatica al candidato entro 30 secondi dall'upload |
| Sicurezza password | Hash bcrypt — le password non sono mai salvate in chiaro |
| Diritto all'oblio | Endpoint `DELETE /candidates/{id}` — pianificato Sprint 1 |
| Data retention | Cancellazione automatica dopo 6 mesi — pianificata Sprint 1 |
| Crittografia DB | Attivazione pgcrypto — pianificata Sprint 1 |

---

## Roadmap

| Sprint | Periodo | Obiettivi |
|---|---|---|
| **S1 — GDPR** | 30 apr – 13 mag 2026 | Diritto all'oblio, data retention 6 mesi, crittografia pgcrypto |
| **S2 — Sicurezza** | 14 mag – 27 mag 2026 | OAuth2 SMTP, test pytest >80%, rimozione credenziali di default |
| **S3 — Feature** | 28 mag – 10 giu 2026 | Import email OAuth2, export CSV, documentazione Swagger pubblica |
| **S4 — Scalabilità** | 11 giu – 24 giu 2026 | Multi-tenancy, ruoli utente, deploy Nginx + SSL |
| **S5 — Integrazioni** | 25 giu – 8 lug 2026 | Webhook Zucchetti/TeamSystem, mobile responsive, notifiche in-app |

---

## Troubleshooting

| Problema | Causa | Soluzione |
|---|---|---|
| `ERR_SOCKET_NOT_CONNECTED` | Backend non avviato | `docker-compose logs backend` |
| `401 Unauthorized` | Token JWT scaduto | Logout e login di nuovo |
| Upload fallisce con `422` | File > 5 MB o formato non valido | Usare PDF o DOCX entro 5 MB |
| Email non inviate | Credenziali SMTP errate | Verificare `SMTP_USER` e `SMTP_PASSWORD` nel `.env` |
| Immagine Docker non aggiornata | Cache di build | `docker-compose build --no-cache && docker-compose up -d` |
| `Invalid hook call` sul frontend | Doppia copia di React | `docker-compose build --no-cache frontend` + pulizia cache browser |

---

## Struttura del progetto

```
fluxhr/
├── backend/
│   ├── main.py             # Entry point FastAPI
│   ├── auth.py             # Autenticazione JWT
│   ├── database.py         # Modelli SQLAlchemy
│   ├── gdpr_sanitize.py    # Sanitizzazione GDPR
│   ├── celery_app.py       # Task email asincroni
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── Login.tsx
│   │   └── index.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Licenza

Distribuito sotto licenza **MIT**. Per segnalazioni di bug o richieste di funzionalità aprire una [issue](https://github.com/fabiocerundolo-bit/FluxHR-Demo/issues).

**Contatti:** supporto@fluxhr.com
