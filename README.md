# FluxHR Demo

> Piattaforma HR dimostrativa con analisi AI dei curricula, gestione candidati e workflow automatizzati.

---

## Indice

- [Panoramica](#panoramica)
- [Stack Tecnologico](#stack-tecnologico)
- [Architettura dei Servizi](#architettura-dei-servizi)
- [Prerequisiti](#prerequisiti)
- [Avvio Rapido](#avvio-rapido)
- [Struttura del Progetto](#struttura-del-progetto)
- [Porte e URL](#porte-e-url)
- [Variabili d'Ambiente](#variabili-dambiente)
- [Sviluppo](#sviluppo)
- [Note](#note)

---

## Panoramica

FluxHR Demo è un'applicazione fullstack per la gestione delle risorse umane, pensata come ambiente dimostrativo. Offre:

- Caricamento e analisi automatica di CV in formato PDF
- Dashboard candidati con React
- API REST con FastAPI (Python)
- Task asincroni e scheduling tramite Celery + Redis
- Testing delle email con MailHog (nessuna mail reale inviata)

---

## Stack Tecnologico

| Layer | Tecnologia |
|---|---|
| Frontend | React (TypeScript), Tailwind CSS, Yarn |
| Backend | Python, FastAPI, Uvicorn |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 16 |
| Email testing | MailHog |
| Containerizzazione | Docker + Docker Compose |

---

## Architettura dei Servizi

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  PostgreSQL │
│  React :3000│     │ FastAPI:8000│     │    :5433    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐     ┌─────────────┐
                    │   Worker    │────▶│    Redis    │
                    │  (Celery)   │     │    :6379    │
                    └─────────────┘     └─────────────┘
                                        ┌─────────────┐
                                        │   MailHog   │
                                        │ SMTP :1025  │
                                        │  UI  :8025  │
                                        └─────────────┘
```

Tutti i servizi comunicano sulla rete Docker interna `fluxhr-network`.

---

## Prerequisiti

- [Docker](https://docs.docker.com/get-docker/) >= 24
- [Docker Compose](https://docs.docker.com/compose/) >= 2.x (plugin integrato in Docker Desktop)
- Git

---

## Avvio Rapido

```bash
# 1. Clona il repository
git clone https://github.com/fabiocerundolo-bit/FluxHR-Demo.git
cd FluxHR-Demo

# 2. Avvia tutti i servizi
docker compose up --build

# Oppure usa lo script di convenienza
chmod +x start.sh
./start.sh
```

Al primo avvio Docker scaricherà le immagini base e installerà le dipendenze: l'operazione può richiedere qualche minuto.

---

## Struttura del Progetto

```
FluxHR-Demo/
├── backend/              # API Python/FastAPI
│   └── app/
│       ├── main.py       # Entry point Uvicorn
│       └── worker.py     # Definizione Celery app
├── frontend/             # React/TypeScript app
│   └── src/
│       └── Login.tsx     # Schermata di login
├── docker-compose.yml    # Orchestrazione servizi
├── start.sh              # Script di avvio rapido
├── cv_sample.md          # CV di esempio (Markdown)
├── cv_sample.pdf         # CV di esempio (PDF)
├── cv_to_pdf.py          # Script conversione CV → PDF
├── dashboard.html        # Prototipo HTML dashboard
└── Log.txt               # Log di build di riferimento
```

---

## Porte e URL

| Servizio | URL | Note |
|---|---|---|
| Frontend React | http://localhost:3000 | UI principale |
| Backend API | http://localhost:8000 | REST API + Swagger UI |
| Swagger / Docs | http://localhost:8000/docs | Documentazione interattiva API |
| MailHog UI | http://localhost:8025 | Visualizzatore email di test |
| PostgreSQL | localhost:5433 | Porta non-standard (evita conflitti) |
| Redis | interno | Non esposto all'host |

> **Nota:** PostgreSQL è esposto sulla porta `5433` (anziché `5432`) per evitare conflitti con eventuali istanze locali già in esecuzione.

---

## Variabili d'Ambiente

Le variabili sono gestite direttamente in `docker-compose.yml`. Per ambienti di produzione è consigliato usare un file `.env`.

| Variabile | Valore default | Descrizione |
|---|---|---|
| `DATABASE_URL` | `postgresql://admin:password@db:5432/fluxhr` | Connessione PostgreSQL |
| `REDIS_URL` | `redis://redis:6379/0` | Connessione Redis |
| `SMTP_SERVER` | `mailhog` | Host SMTP (test) |
| `SMTP_PORT` | `1025` | Porta SMTP MailHog |
| `POSTGRES_USER` | `admin` | Utente DB |
| `POSTGRES_PASSWORD` | `password` | Password DB |
| `POSTGRES_DB` | `fluxhr` | Nome database |

---

## Sviluppo

### Ricostruire un singolo servizio

```bash
docker compose up --build backend
docker compose up --build frontend
```

### Visualizzare i log in tempo reale

```bash
docker compose logs -f
docker compose logs -f backend
docker compose logs -f worker
```

### Accedere alla shell di un container

```bash
docker compose exec backend bash
docker compose exec frontend sh
```

### Fermare tutti i servizi

```bash
docker compose down

# Per eliminare anche i volumi (dati DB e uploads)
docker compose down -v
```

### Convertire un CV Markdown in PDF

```bash
python cv_to_pdf.py
```

---

## Note

- Questo è un ambiente **demo**: le credenziali nel `docker-compose.yml` sono di default e non devono essere usate in produzione.
- Il volume `postgres_data` persiste i dati del database tra un riavvio e l'altro.
- Il volume `uploads_data` conserva i file CV caricati, condiviso tra `backend` e `worker`.
- MailHog intercetta tutte le email inviate: nessun messaggio viene recapitato a indirizzi reali.
- Il frontend usa `CHOKIDAR_USEPOLLING=true` per garantire il hot-reload in ambienti Docker su macOS/Windows.
