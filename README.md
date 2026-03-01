# VyapaarSetu (व्यापार सेतु)

**AI-powered MSE Agent Mapping Tool for ONDC TEAM Initiative**

Built for **IndiaAI Innovation Challenge 2026 — Problem Statement 2 (PS2)**, Ministry of MSME.

VyapaarSetu ("Trade Bridge") automates and scales the MSME TEAM (Trade Enablement and Marketing) scheme — helping Micro and Small Enterprises get onboarded onto ONDC by eliminating manual data entry, inconsistent product categorisation, and labour-intensive SNP matching.

---

## Three Core AI Capabilities

| # | Capability | What It Does |
|---|---|---|
| 1 | **Multilingual Voice-Enabled Registration** | MSE describes their business in Hindi/English/Hinglish via voice — AI auto-fills registration forms |
| 2 | **AI Product Categorisation (CaaS)** | Maps products to correct ONDC RET taxonomy, extracts mandatory attributes, validates compliance |
| 3 | **Intelligent MSE-to-SNP Matching** | Scores and recommends best-fit Seller Network Participants based on category, geography, B2B/B2C |

---

## Architecture

```
                    ┌─── Next.js Frontend (Web — 3 portals)
User (Voice/Chat) ──┤
                    └─── WhatsApp (Baileys)
                              │
                              ▼
                     FastAPI Backend → DeepSeek LLM (LangChain)
                         │
                    Skills System (3 skills)
                         │
                    ┌────┴────┐──────────────┐
                    │         │              │
               PostgreSQL   Redis          Qdrant
              (MSE, SNP,   (sessions)   (ONDC taxonomy +
               products,               SNP knowledge +
               matches)                TEAM scheme RAG)
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 + React 19 + Zustand + Tailwind CSS 4 |
| Backend | FastAPI (async) + SQLAlchemy 2.0 |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Vector DB | Qdrant |
| LLM | DeepSeek via LangChain |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (local) |
| Auth | JWT (python-jose + bcrypt) |
| Voice | Web Speech API (Hindi + English + Hinglish) |
| WhatsApp | Baileys |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Node.js 20+
- DeepSeek API key (or OpenAI-compatible)

### 1. Start Infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL (5432), Redis (6379), and Qdrant (6333).

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Configure secrets
cp config/.secrets.toml.example config/.secrets.toml
# Edit config/.secrets.toml — add your DeepSeek API key

# Run database migrations
alembic upgrade head

# Seed demo data (SNPs, ONDC categories, demo MSEs, Qdrant indexes)
python seed.py

# Start backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open http://localhost:3000

---

## Demo Credentials

| Role | Mobile | Password | What to See |
|---|---|---|---|
| MSE (Brass artisan) | `7409210692` | `demo1234` | Full onboarding flow: profile, catalogue, SNP matching |
| MSE (Textiles) | `9876543211` | `demo1234` | Profile complete, catalogue in progress |
| MSE (Organic food) | `9876543212` | `demo1234` | SNP already selected, dashboard view |
| SNP (GlobalLinker) | `9000000001` | `snpdemo` | SNP portal: view matched MSE leads |
| Admin (NSIC) | `9000000002` | `admindemo` | Admin dashboard: funnel analytics, verification queue |

---

## Demo Flow

1. **Login as Rajesh** (brass artisan, Maharashtra) — mobile: `7409210692`
2. View **profile pre-filled** from Udyam API
3. Go to **Catalogue** — describe product via text or voice: *"Peetal ke diye banata hoon, Rs 150, MOQ 10"*
4. AI classifies to **ONDC:RET16** (Home & Decor), extracts attributes, shows compliance score
5. Fix missing fields (HSN code, dimensions) — compliance rises to 100%
6. Go to **SNP Matching** — click "Generate Recommendations"
7. AI recommends **Top 3 SNPs** — GlobalLinker is best match (87.5%)
8. **Select SNP** — status moves to "SNP Selected"
9. View **Dashboard** — see onboarding timeline with current stage
10. **Login as SNP** (`9000000001`) — see Rajesh's lead with catalogue preview
11. **Login as Admin** (`9000000002`) — see funnel dashboard, approve MSEs

---

## Three Portals

### Portal A: MSE Portal (Primary)
- `/` — Landing page (TEAM scheme explained)
- `/login` — Udyam + OTP login
- `/onboarding/profile` — Voice-enabled business profile (Step 1)
- `/onboarding/catalogue` — AI catalogue builder with chat (Step 2)
- `/onboarding/match` — SNP recommendations (Step 3)
- `/dashboard` — Onboarding status tracker
- `/knowledge` — RAG-powered TEAM/ONDC FAQ

### Portal B: SNP Portal
- `/snp/dashboard` — Stats overview
- `/snp/leads` — AI-matched MSE leads with readiness scores

### Portal C: NSIC Admin Portal
- `/admin/dashboard` — Funnel analytics
- `/admin/verify` — AI pre-screened verification queue

---

## AI Agent Architecture

### 3 Skills × 8 Tools

| Skill | Tools |
|---|---|
| `onboarding` | `fetch_udyam_data`, `search_knowledge` |
| `cataloguing` | `classify_product`, `extract_attributes`, `validate_catalogue`, `get_category_info` |
| `matching` | `match_snp`, `search_knowledge` |

### SNP Matching Algorithm

```
total_score = (
    category_overlap   × 0.45 +    # Most important
    geography_coverage × 0.25 +    # State overlap
    transaction_type   × 0.20 +    # B2B/B2C alignment
    capacity_score     × 0.10      # Onboarding speed
)
```

---

## Project Structure

```
VyapaarSetu/
├── backend/
│   ├── config/               # Dynaconf settings + secrets
│   ├── migrations/           # Alembic database migrations
│   ├── seed.py               # Demo data seeder
│   └── src/
│       ├── main.py           # FastAPI application
│       ├── api/routes/       # 9 API route modules
│       ├── agent/            # ReAct agent engine
│       ├── skills/builtin/   # 3 skills (onboarding, cataloguing, matching)
│       ├── tools/core/       # 8 AI tools
│       ├── db/models/        # 8 SQLAlchemy models
│       ├── rag/              # Qdrant vector search
│       ├── llm/              # LangChain LLM client
│       └── data/             # ONDC taxonomy + SNP seed data
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages (3 portals)
│       ├── components/       # ChatPanel, VoiceInput
│       ├── lib/api.ts        # API client
│       └── store/            # Zustand auth store
└── docker-compose.yml        # PostgreSQL + Redis + Qdrant
```

---

## Compliance

- **DPDP Act 2023** — No personal data stored beyond registration; consent-based
- **E-Commerce Rules 2020** — Product attribute validation enforced
- **Legal Metrology Act 2011** — MRP, net quantity, manufacturer validation
- **FSSAI** — Food product categories (RET10, RET11) require license verification
- **Responsible AI** — Transparent AI decisions with match reasoning; human-in-the-loop verification

---

## License

Proprietary — Built for IndiaAI Innovation Challenge 2026, Ministry of MSME.
