# Promethicc AI

A hybrid platform of specialized AI expert agents — **Code**, **Eng**, **Agri**, **Med**, **Law** — each operable in two modes:

- **Offline** (free tier): One shared quantized local model on a free CPU host, zero marginal cost
- **Online** (paid tier): External LLM APIs + web search + RAG

## Architecture

```
┌──────────────────┐     ┌──────────────────────────────────┐     ┌──────────────┐
│  Next.js (Vercel)│────▶│  FastAPI (HF Space, CPU Basic)   │────▶│  Supabase    │
│  Landing + Chat  │ JWT │  Router → Safety → Inference     │     │  Auth + DB   │
│  Supabase Auth   │     │  llama-cpp-python (offline)      │     │  pgvector    │
└──────────────────┘     │  External LLM API (online)       │     └──────────────┘
                         └──────────────────────────────────┘
```

## Experts

| Expert | Label | Risk Tier | Notes |
|--------|-------|-----------|-------|
| Code | Promethicc-Code | Standard | Software engineering |
| Eng | Promethicc-Eng | Standard | General/civil/mechanical engineering |
| Agri | Promethicc-Agri | Standard | Agricultural science |
| Med | Promethicc-Med | High Stakes | Health info only, never diagnosis/dosing |
| Law | Promethicc-Law | High Stakes | Jurisdiction-scoped, never legal advice |

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project (free tier)
- (Optional) A GGUF model file for offline inference

### 1. Supabase

Apply the migration to your Supabase project:

```sql
-- Run supabase/migrations/0001_init.sql against your project
```

Enable Google as an OAuth provider in the Supabase dashboard:
**Auth → Providers → Google** (not scriptable via SQL).

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase URL, keys, model path
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
cd web
npm install
cp .env.example .env.local
# Edit .env.local with your Supabase and backend URLs
npm run dev
```

## Modes

- **Offline (free)**: Runs on the HF Space's CPU via llama-cpp-python. Zero marginal cost.
- **Online (paid)**: Calls external LLM APIs (Groq/Gemini). Requires active subscription/credits.

Mode access is enforced **server-side** — a free-tier user requesting online mode gets a 403, even calling the API directly.

## Safety (Med & Law)

- **Disclaimer gate**: Users must accept a per-expert disclaimer before their first query
- **Emergency detection**: Medical emergencies and mental health crises return a fixed safe response, never a model-generated one
- **Jurisdiction requirement**: Law queries require a jurisdiction before any substantive answer
- **RAG over free generation**: High-stakes facts retrieved from curated, source-cited documents

## License

Open-source (offline mode). Online mode requires a paid tier.
