# CLAUDE.md — VyapaarSetu Project

## What is VyapaarSetu?

**VyapaarSetu** (व्यापार सेतु = "Trade Bridge") is an AI-powered MSE Agent Mapping Tool that automates, optimises, and scales the MSME TEAM (Trade Enablement and Marketing) initiative — helping Micro and Small Enterprises get onboarded onto ONDC (Open Network for Digital Commerce) by eliminating manual data entry, inconsistent product categorisation, and labour-intensive SNP matching.

Built for the **IndiaAI Innovation Challenge 2026 — Problem Statement 2 (PS2), Ministry of MSME**.

---

## Competition Context

- **Challenge:** IndiaAI Innovation Challenge 2026 (IndiaAI + MeitY + Ministry of MSME)
- **Problem Statement:** PS2 — AI-powered MSE Agent Mapping Tool
- **Ministry:** MSME (in collaboration with NSIC as implementing agency)
- **Stage 1 Prize:** INR 25 Lakhs (up to 3 teams shortlisted per PS)
- **Stage 2 Prize:** INR 1 Crore work contract (2 years deployment)
- **Submission Deadline:** Extended by 8 days from 22 Feb 2026
- **Compliance:** DPDP Act 2023, Responsible AI, Cybersecurity guidelines, E-Commerce Rules 2020
- **Guidelines PDF:** `.claude/project-docs/guidelines.pdf`

---

## The Problem VyapaarSetu Solves

### TEAM Initiative Background
- MSME launched TEAM scheme (Rs. 277 Cr, 3 years FY2024–2027)
- Goal: Onboard 5 lakh MSEs onto ONDC (50% women-led)
- NSIC is implementing agency
- MSEs are mapped to SNPs (Seller Network Participants) who build their ONDC catalogue

### Current Pain Points
1. **Manual data entry** — MSEs fill complex digital forms they don't understand
2. **Inconsistent product category tagging** — wrong ONDC taxonomy = product invisible on buyer apps
3. **Labour-intensive claim verification by NSIC** — delays, rejections, bottlenecks
4. **Language/literacy barriers** — rural MSEs can't navigate English portals

### What VyapaarSetu Does
- Removes language barriers via voice + multilingual registration
- AI maps products to correct ONDC taxonomy (CaaS layer)
- Intelligently matches MSEs to best-fit SNPs
- Reduces NSIC's manual verification workload via AI pre-screening

---

## ONDC Network Understanding

### How ONDC Works
```
Buyer (consumer)
      ↓
Buyer App (Paytm / PhonePe / Magicpin)
      ↓ (via Gateway — multicast search)
Seller App = SNP (DotPe / Meesho / GlobalLinker)
      ↓
MSE Seller (merchant / craftsman / manufacturer)
```

- **ONDC is like UPI but for commerce** — open interoperable network
- Seller lists on ONE SNP → product discoverable on ALL buyer apps
- SNP = Marketplace Seller Node (MSN) — aggregator, manages MSE catalogues on ONDC
- MSE does NOT need to interact with ONDC protocol directly — SNP handles it

### ONDC Network Participant Types
| Type | Role | Examples |
|---|---|---|
| Buyer App | Consumer-facing search + purchase | Paytm, PhonePe, Magicpin |
| MSN (Seller App / SNP) | Onboards sellers, manages catalogues | DotPe, Meesho, GlobalLinker |
| ISN (Inventory Seller Node) | Large sellers who are NPs themselves | D2C brands, dark stores |
| Gateway | Multicasts search queries | ONDC Gateway |

### ONDC Retail Product Taxonomy (RET Codes)
These are seeded into the `OndcCategory` table in DB:

| Code | Category | Key MSE Types | Required Attributes |
|---|---|---|---|
| ONDC:RET10 | Grocery | Spices, pulses, condiments | Product name, MRP, weight/volume, expiry, FSSAI, country of origin |
| ONDC:RET11 | Food & Beverages | Packaged food, pickles, snacks | Product name, MRP, weight, expiry, FSSAI license, ingredients |
| ONDC:RET12 | Fashion | Handloom, textiles, garments, sarees | Product name, MRP, size, material, colour, care instructions |
| ONDC:RET13 | Beauty & Personal Care | Herbal products, hair oils | Product name, MRP, volume/weight, ingredients, shelf life |
| ONDC:RET14 | Electronics | Basic electronics, accessories | Product name, MRP, brand, model, warranty, power specs |
| ONDC:RET15 | Appliances | Small appliances | Product name, MRP, brand, warranty, power consumption |
| ONDC:RET16 | Home & Decor | Brass items, handicrafts, wooden crafts | Product name, MRP, material, dimensions, colour, MOQ |
| ONDC:RET17 | Toys & Games | Handmade toys, wooden toys | Product name, MRP, age group, material, safety cert |
| ONDC:RET18 | Health & Wellness | Herbal, Ayurvedic products | Product name, MRP, weight, ingredients, certifications |
| ONDC:RET19 | Pharma | Medicines | Product name, MRP, composition, manufacturer, batch no, expiry |

### SNP Seed Data (Real SNPs from ONDC Network)
These are seeded into the `SNP` table:

| SNP | Categories | Geography | B2B | B2C | Avg Days |
|---|---|---|---|---|---|
| GlobalLinker | RET10,12,13,14,15,16,18 | All India | Yes | Yes | 7 |
| Plotch | RET10,12,13,14,15,16,18 | All India | No | Yes | 5 |
| SellerApp | RET10,12,14,16 | All India | Yes | Yes | 10 |
| eSamudaay | RET11 | All India | No | Yes | 4 |
| DotPe | RET10,11,12,13,16 | All India | No | Yes | 6 |
| MyStore | RET10,12,13,14,16 | All India | No | Yes | 7 |

---

## Three Core AI Capabilities (PS2 Requirements)

### 1. Multilingual Voice-Enabled Registration + Automated Form Filling
- Web Speech API for voice input (Hindi + English + Hinglish)
- Udyam number → API auto-fetches business details (mocked for PoC)
- LLM extracts structured data from unstructured voice input
- Auto-populates registration form fields

### 2. AI-Driven Product Categorisation (ONDC Taxonomy)
- MSE describes product in natural language / voice / WhatsApp
- LLM classifies to correct ONDC RET code + subcategory
- NER extracts all mandatory attributes per category
- Compliance validation against E-Commerce Rules 2020 + Legal Metrology Act
- Returns compliance score + missing fields list
- VyapaarSetu IS the "Cataloguing as a Service (CaaS)" layer ONDC proposed

### 3. Intelligent MSE-to-SNP Matching
- Semantic similarity between MSE product categories and SNP capabilities
- Rule-based scoring: category overlap + geography + B2B/B2C + capacity
- Qdrant vector search on SNP knowledge base
- Returns Top 3 SNPs with match score + reasons
- MSE selects SNP → onboarding package auto-generated

---

## Three Portals

### Portal A: MSE Portal (PRIMARY — competition focus)
Pages:
1. `/` — Landing (what is VyapaarSetu, TEAM scheme explained)
2. `/login` — Udyam number + mobile OTP
3. `/onboarding/profile` — Business profile (voice-enabled)
4. `/onboarding/catalogue` — AI catalogue builder (web + WhatsApp)
5. `/onboarding/match` — SNP recommendations + selection
6. `/dashboard` — Onboarding status tracker + WhatsApp notifications
7. `/knowledge` — TEAM/ONDC FAQ (RAG-powered)

### Portal B: SNP Portal (PoC — simplified)
Pages:
1. `/snp/login` — SNP login
2. `/snp/dashboard` — Stats overview
3. `/snp/leads` — AI-matched MSE leads with readiness score
4. `/snp/leads/[id]` — MSE profile + catalogue preview, accept/reject

### Portal C: NSIC Admin Portal (PoC — mock dashboard)
Pages:
1. `/admin/login` — Admin login
2. `/admin/dashboard` — Funnel analytics (registered, catalogue ready, matched, live)
3. `/admin/verify` — AI pre-screened verification queue

---

## Skill-Based Agent Architecture

### 3 Skills

| Skill | Channels | Workflow Steps | Tools |
|---|---|---|---|
| `onboarding` | Web, WhatsApp | Registration, profile | `fetch_udyam_data`, `search_knowledge` |
| `cataloguing` | Web, WhatsApp | Product categorisation | `classify_product`, `extract_attributes`, `validate_catalogue`, `get_category_info` |
| `matching` | Web | SNP recommendation | `match_snp`, `search_knowledge` |

### 8 Agent Tools

| Tool | What It Does |
|---|---|
| `fetch_udyam_data` | Mock Udyam API — returns MSE business details from Udyam number |
| `classify_product` | LLM maps product description to ONDC RET code + subcategory |
| `extract_attributes` | NER extracts: product name, MRP, MOQ, HSN, material, country of origin |
| `validate_catalogue` | Checks compliance against E-Commerce Rules 2020 + Legal Metrology Act |
| `get_category_info` | Returns required attributes for ONDC category from Qdrant |
| `match_snp` | Scores SNPs: category overlap + geography + B2B/B2C + semantic similarity |
| `search_knowledge` | RAG over TEAM scheme + ONDC knowledge base in Qdrant |
| `send_notification` | WhatsApp notification via Baileys at milestone events |

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

---

## Database Models

| Model | Purpose | Key Fields |
|---|---|---|
| `User` | All portal users | id, role (mse/snp/admin), mobile, email |
| `MSE` | MSE business profile | udyam_number, business_name, owner_name, nic_code, state, district, major_activity, turnover, employee_count, transaction_type (b2b/b2c/both), target_states, onboarding_status, selected_snp_id |
| `SNP` | SNP capabilities | name, platform_name, ondc_live, supported_categories, supported_states, b2b, b2c, avg_onboarding_days, capability_score |
| `Product` | MSE product items | mse_id, raw_description, product_name, ondc_category_code, subcategory, attributes (JSON), hsn_code, mrp, moq, compliance_score, status (draft/ready/listed) |
| `OndcCategory` | ONDC taxonomy | code, name, domain, required_attributes (JSON), optional_attributes (JSON) |
| `MSEMatch` | MSE-SNP match results | mse_id, snp_id, match_score, match_reasons (JSON), status (suggested/selected/rejected) |
| `Session` | Chat sessions | user_id, skill, channel (web/whatsapp) |
| `Message` | Chat messages | session_id, role, content, tool_calls |

---

## Tech Stack

| Layer | Technology | Reuse from ODRMitra |
|---|---|---|
| Frontend | Next.js 16 + React 19 | Yes |
| State | Zustand | Yes |
| Backend | FastAPI (async) | Yes |
| Database | PostgreSQL + SQLAlchemy async | Yes |
| Cache | Redis | Yes |
| Vector DB | Qdrant | Yes |
| LLM | DeepSeek via LangChain | Yes |
| Embeddings | sentence-transformers (local) | Yes |
| Auth | JWT (python-jose) | Yes |
| Config | Dynaconf | Yes |
| Voice | Web Speech API (Hindi + English + Hinglish) | Yes |
| WhatsApp | Baileys | Yes |

---

## WhatsApp Channel Flow

```
MSE receives welcome WhatsApp after registration
        ↓
Bot: "Product add karne ke liye photo + description bhejiye"
        ↓
MSE sends product photo + text (e.g. "Peetal ka diya, Rs 150, MOQ 10")
        ↓
AI: OCR on photo + NLP on text
  → classifies to ONDC:RET16 (Home & Decor)
  → extracts attributes (MRP: 150, material: brass, MOQ: 10)
  → flags missing: HSN code, dimensions
        ↓
Bot: "Product 1 add ho gaya! HSN code bata dijiye."
        ↓
MSE replies → product updated → marked Ready
        ↓
MSE types "Done" → AI runs matching → WhatsApp notification:
"Aapka catalogue ready hai! SNP select karne ke liye login karein: [link]"
        ↓
After SNP selection:
"SNP GlobalLinker ko aapka profile bhej diya. Onboarding 7 din mein hogi."
```

---

## Project Structure

```
VyapaarSetu/
├── CLAUDE.md                          # This file
├── README.md
├── .claude/
│   ├── project-docs/
│   │   ├── guidelines.pdf             # IndiaAI challenge guidelines
│   │   ├── ondc.pdf                   # ONDC Trust paper (architecture)
│   │   ├── taxonomy_ondc_network.pdf  # ONDC entity taxonomy
│   │   ├── implementation-plan.md     # Step-by-step dev plan
│   │   └── ondc-knowledge.md          # ONDC taxonomy + SNP seed data + references
│   └── assets/
├── backend/
│   ├── config/
│   │   ├── settings.toml
│   │   └── .secrets.toml
│   ├── migrations/versions/
│   ├── src/
│   │   ├── main.py
│   │   ├── config/settings.py
│   │   ├── core/
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models/               # User, MSE, SNP, Product, OndcCategory, MSEMatch, Session, Message
│   │   ├── llm/client.py
│   │   ├── agent/
│   │   │   ├── engine.py
│   │   │   ├── context/loader.py
│   │   │   └── prompt/
│   │   ├── skills/
│   │   │   ├── loader.py
│   │   │   ├── manager.py
│   │   │   ├── sync.py
│   │   │   └── builtin/
│   │   │       ├── onboarding/        # SKILL.md + tools/
│   │   │       ├── cataloguing/       # SKILL.md + tools/
│   │   │       └── matching/          # SKILL.md + tools/
│   │   ├── tools/
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   └── core/                  # 8 tools
│   │   ├── rag/
│   │   ├── chat/
│   │   ├── api/routes/
│   │   │   ├── auth.py
│   │   │   ├── mse.py
│   │   │   ├── snp.py
│   │   │   ├── products.py
│   │   │   ├── catalogue.py
│   │   │   ├── match.py
│   │   │   ├── admin.py
│   │   │   ├── chat.py
│   │   │   └── channel/whatsapp.py
│   │   └── data/                      # ONDC taxonomy JSON, SNP seed data
│   └── pyproject.toml
├── frontend/
│   ├── src/app/
│   │   ├── (auth)/login/
│   │   ├── (mse)/
│   │   │   ├── onboarding/profile/
│   │   │   ├── onboarding/catalogue/
│   │   │   ├── onboarding/match/
│   │   │   ├── dashboard/
│   │   │   └── knowledge/
│   │   ├── (snp)/snp/
│   │   │   ├── dashboard/
│   │   │   ├── leads/
│   │   │   └── leads/[id]/
│   │   └── (admin)/admin/
│   │       ├── dashboard/
│   │       └── verify/
│   ├── src/components/
│   ├── src/lib/api.ts
│   └── src/store/
└── docker-compose.yml
```

---

## Branding

- **Primary:** Deep Indigo `#312e81`
- **Accent:** Amber `#f59e0b`
- **Background:** White `#ffffff`
- **Name:** VyapaarSetu (व्यापार सेतु)

---

## Development Rules

- Do NOT edit files without explicit permission
- Do NOT create/delete/rename files unless instructed
- Follow ODRMitra patterns exactly — same FastAPI structure, same Next.js layout, same agent/skill architecture
- Reference `D:/My_project/ODRMitra/ODRMitra/` for all patterns
- Type hints mandatory on all functions
- No dead code, no unused imports
- Docstrings on all public functions/classes
- No `.env`, API keys, or `__pycache__` in git

---

## Key References

| Resource | Location / URL |
|---|---|
| ODRMitra Reference Project | `D:/My_project/ODRMitra/ODRMitra/` |
| Competition Guidelines | `.claude/project-docs/guidelines.pdf` |
| ONDC Trust Paper | `.claude/project-docs/ondc.pdf` |
| ONDC Entity Taxonomy | `.claude/project-docs/taxonomy_ondc_network.pdf` |
| ONDC Retail Specs | `github.com/ONDC-Official/ONDC-RET-Specifications` |
| ONDC Common Taxonomy | `github.com/ONDC-Official/Common-Taxonomy-Project` |
| ONDC Resources | `resources.ondc.org` |
| ONDC Network Participants | `ondc.org/network-participants` |
| TEAM Portal | `team.msmemart.com` |
| TEAM Scheme Guidelines PDF | `team.msmemart.com/themes/msme/scheme/images/pdf/Approved-msme-team-guidelines.pdf` |
| IndiaAI Challenge Portal | `aikosh.indiaai.gov.in` |
