# PROMPT.md

# Build Task: Promethicc AI (v1)

Read GEMINI.md first and follow every rule in it. Build in phases; each
phase should be independently runnable/testable before moving to the next.

## Phase 0 — Monorepo scaffold

```
promethicc-ai/
├── web/                          # Next.js app (Vercel)
├── backend/                      # FastAPI app (HF Space)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── auth.py
│   │   ├── router.py
│   │   ├── experts.yaml
│   │   ├── safety/
│   │   │   ├── __init__.py
│   │   │   ├── disclaimers.py
│   │   │   └── emergency_detector.py
│   │   ├── inference/
│   │   │   ├── __init__.py
│   │   │   ├── offline_engine.py
│   │   │   └── online_engine.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   └── retriever.py
│   │   ├── tools/
│   │   │   └── web_search.py     # ported from the earlier MCP web_server.py
│   │   └── audit.py
│   ├── scripts/
│   │   └── ingest_docs.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile                # HF Spaces SDK: docker
├── supabase/
│   └── migrations/
│       └── 0001_init.sql
└── README.md
```

## Phase 1 — Supabase schema (`supabase/migrations/0001_init.sql`)

Enable the `pgvector` extension first, then create:

- `profiles (id uuid pk references auth.users, tier text default 'free', credits int default 0, created_at timestamptz default now())`
- `disclaimer_acceptances (id uuid pk default gen_random_uuid(), user_id uuid references auth.users, expert text, accepted_at timestamptz default now(), unique(user_id, expert))`
- `usage_log (id uuid pk default gen_random_uuid(), user_id uuid, expert text, mode text, tokens_used int, created_at timestamptz default now())`
- `audit_log (id uuid pk default gen_random_uuid(), user_id uuid, expert text, mode text, query text, jurisdiction text, emergency_triggered bool default false, success bool, created_at timestamptz default now())`
- `rag_documents (id uuid pk default gen_random_uuid(), expert text, source_title text, source_url text, content text, embedding vector(1536))`

Note in README: enabling Google as an OAuth provider is a manual step in
the Supabase dashboard (Auth → Providers → Google), not scriptable via SQL
migration.

Acceptance: migration applies cleanly on a fresh Supabase project;
`select * from pg_extension where extname = 'vector';` returns a row.

## Phase 2 — `backend/app/experts.yaml`

```yaml
experts:
  code:
    label: "Promethicc-Code"
    risk_tier: standard
    system_prompt: "You are Promethicc-Code, a software engineering expert. Give correct, idiomatic, well-explained answers."
    rag_namespace: code
  eng:
    label: "Promethicc-Eng"
    risk_tier: standard
    system_prompt: "You are Promethicc-Eng, a general/civil/mechanical engineering expert. Be precise about units, standards, and assumptions."
    rag_namespace: eng
  agri:
    label: "Promethicc-Agri"
    risk_tier: standard
    system_prompt: "You are Promethicc-Agri, an agricultural science expert. Account for regional/climate context when relevant and ask for it if missing."
    rag_namespace: agri
  med:
    label: "Promethicc-Med"
    risk_tier: high_stakes
    system_prompt: "You are Promethicc-Med. Provide general health information only. Never give specific medication dosing. Never instruct the user to start, stop, or change a medication. Never attempt a diagnosis. Always recommend seeing a licensed physician for anything actionable."
    rag_namespace: med
  law:
    label: "Promethicc-Law"
    risk_tier: high_stakes
    system_prompt: "You are Promethicc-Law. Provide general legal information only, strictly scoped to the jurisdiction supplied in context. Never claim to be a substitute for a licensed attorney. If no jurisdiction is supplied, do not answer substantively."
    rag_namespace: law
```

`backend/app/config.py` loads this into a `dict[str, ExpertConfig]`
pydantic model (`label: str`, `risk_tier: Literal["standard", "high_stakes"]`,
`system_prompt: str`, `rag_namespace: str`) at startup — the ONLY place
expert metadata lives.

## Phase 3 — Auth (`backend/app/auth.py`)

- `async def verify_jwt(token: str) -> dict` — verifies a Supabase-issued
  JWT against the project's JWT secret, returns decoded claims (`sub` =
  user id). Raises `HTTPException(401)` on failure.
- FastAPI dependency `async def get_current_user(authorization: str = Header(...)) -> User`
  wrapping the above; used on every protected route.

## Phase 4 — Router (`backend/app/router.py`)

`POST /v1/chat`

Request body: `{expert: str, mode: Literal["offline", "online"], message: str, jurisdiction: str | None}`

Flow:
1. `get_current_user` dependency resolves the caller.
2. Look up `expert` in the experts config; 404 if unknown.
3. If `expert.risk_tier == "high_stakes"`: check
   `disclaimer_acceptances` for `(user_id, expert)` — 403 with error code
   `DISCLAIMER_REQUIRED` if missing, so the frontend can show the modal.
4. If `expert == "law"` and `jurisdiction` is missing/empty: 400 with
   error code `JURISDICTION_REQUIRED`.
5. Run `safety.emergency_detector.check(message)` for `med`/`law`. If
   triggered: write to `audit_log` with `emergency_triggered=true`, return
   the fixed safe response immediately, skip inference entirely.
6. If `mode == "online"`: check `profiles.tier`/`credits` for the user —
   403 (`UPGRADE_REQUIRED`) if insufficient.
7. Check `usage_log` against the configured daily cap for offline mode —
   429 if exceeded.
8. Optionally retrieve RAG context via
   `rag.retriever.search(expert.rag_namespace, message)`.
9. Dispatch to `inference.offline_engine.generate(...)` or
   `inference.online_engine.generate(...)` with the expert's system
   prompt + RAG context + message.
10. Write rows to `usage_log` and `audit_log`. Return
    `{response: str, sources: list[str], mode: str, expert: str}`.

## Phase 5 — `backend/app/safety/emergency_detector.py`

`async def check(message: str) -> bool` — v1 implementation: keyword/
phrase matching against two curated lists (medical emergency phrases,
mental health crisis phrases), with a cheap LLM-based classifier call as a
second pass only when the keyword pass is ambiguous. Bias toward false
positives — over-triggering the safe response is the correct failure
mode, under-triggering is not.

`SAFE_RESPONSE_MEDICAL` and `SAFE_RESPONSE_CRISIS` — fixed strings, never
model-generated, pointing to emergency services / a crisis line and
stating Promethicc cannot help with this directly.

## Phase 6 — `backend/app/inference/offline_engine.py`

- Module-level singleton: load one quantized GGUF model via
  `llama_cpp.Llama(...)` at import time (model path from `.env`, e.g. a
  3B-class instruct model).
- `async def generate(system_prompt: str, rag_context: str | None, message: str) -> str`
  — builds the prompt, runs inference wrapped in `asyncio.to_thread` so
  the blocking llama.cpp call doesn't block the event loop, returns text.

## Phase 7 — `backend/app/inference/online_engine.py`

- `async def generate(system_prompt: str, rag_context: str | None, message: str) -> str`
  — calls the external OpenAI-compatible endpoint (Groq/Gemini,
  configurable via `.env`), optionally calling `tools/web_search.py`
  first if the query looks like it needs current information. Port the
  `web_search`/`fetch_url` functions from the earlier MCP project's
  `web_server.py` directly — same DuckDuckGo-based implementation, used
  in-process here (no MCP protocol needed for this internal use).

## Phase 8 — `backend/app/rag/retriever.py`

- `async def search(namespace: str, query: str, top_k: int = 5) -> list[dict]`
  — embeds `query` (small local embedding model, or the online API's
  embedding endpoint), runs a pgvector similarity query scoped to
  `rag_documents.expert = namespace`, returns
  `[{content, source_title, source_url}, ...]`.
- `backend/scripts/ingest_docs.py` — CLI script that chunks and embeds
  source documents per expert into `rag_documents`. Ship with a handful
  of seed documents per expert so the pipeline is provably working;
  expanding the corpus is an ongoing task, not a one-time v1 deliverable.

## Phase 9 — `web/` (Next.js on Vercel)

- Landing page: product pitch, the 5 expert cards, a single **Launch**
  button.
- Launch → Supabase Auth Google OAuth flow → redirect to `/dashboard`.
- `/dashboard`: expert picker, per-expert chat UI, mode toggle (online
  disabled/greyed for free-tier users with an "Upgrade" CTA), usage meter
  reading from `usage_log` via a Supabase query.
- High-stakes expert chat screens show the disclaimer modal on first
  visit per expert, calling `POST /v1/disclaimers/{expert}/accept` to
  record acceptance, and for Law, a jurisdiction selector shown before
  the chat input unlocks.
- All chat calls go to the FastAPI backend's `/v1/chat`, passing the
  Supabase session JWT in the `Authorization` header.

## Phase 10 — Tests

- `backend/tests/test_safety.py` — emergency-detector true/false cases;
  disclaimer-gate rejection.
- `backend/tests/test_router.py` — mode enforcement (free user denied
  online), jurisdiction requirement for Law, rate-limit enforcement.
- `backend/tests/test_rag.py` — retrieval returns seeded documents for a
  known query.

## Final acceptance checklist

- [ ] All 5 experts respond in offline mode for a logged-in user; no
      disclaimer friction for Code/Eng/Agri
- [ ] Med/Law return `DISCLAIMER_REQUIRED` until acceptance is recorded,
      then work normally afterward
- [ ] Law returns `JURISDICTION_REQUIRED` until a jurisdiction is supplied
- [ ] A medical-emergency-phrased query to Med returns the fixed safe
      response, never a generated one, and logs `emergency_triggered=true`
- [ ] A free-tier user requesting `mode: online` gets a 403
      `UPGRADE_REQUIRED`, even calling the API directly (not just via the UI)
- [ ] Offline-mode rate limit kicks in after the configured daily cap and
      returns 429
- [ ] `pytest` passes
- [ ] Landing → Launch → Google OAuth → Dashboard flow works end to end on
      a fresh Supabase project
