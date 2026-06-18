# GEMINI.md

## Project: Promethicc AI

A hybrid platform of specialized AI expert agents — Code, Eng, Agri, Med,
Law — each operable in two modes: **Offline** (one shared quantized local
model on a free CPU host, zero marginal cost) and **Online** (external LLM
APIs + web search + RAG, costs money per call). A Promethicc Router selects
expert + mode per request. Ships open-source/free first (offline mode
only), monetizes later by unlocking online mode behind a paid tier.

## Product positioning

- **Offline mode = free tier.** Zero marginal cost to Vedant — runs
  entirely on the HF Space's CPU. This is what gets open-sourced and
  builds the initial user base.
- **Online mode = paid tier.** Every call costs API credits, so access
  must be checked server-side against the user's subscription/credit
  balance — never just hidden in the UI.
- **Open-source phase:** router + offline experts public, hosted on
  Vercel Hobby + HF free CPU + Supabase free tier — genuinely $0 to run.
- **Paid phase:** once usage justifies it, upgrade Vercel to Pro ($20/mo —
  required the moment this is commercial, Hobby explicitly forbids it) and
  unlock online mode for paying users.
- **Risk profiles differ sharply across experts.** Code/Eng/Agri carry
  informational-error risk (bad code, bad advice). Med/Law carry
  real-world-harm risk (a wrong answer can hurt someone's health or legal
  outcome). Rules 9-13 below exist because of that difference — they are
  not optional polish, they're what separates a project from a liability.

## Non-negotiable architecture rules

1. **One shared offline model, not five.** v1 offline mode runs a single
   quantized instruct model (3B-class GGUF) loaded once at Space startup.
   Per-expert specialization comes from (a) a per-expert system prompt and
   (b) a per-expert RAG namespace — not five separately fine-tuned models.
   Training five domain SLMs is a v2+ research effort, not part of this
   build.
2. **Router decides expert + mode before any inference call.** One
   FastAPI endpoint classifies which expert a query belongs to, checks the
   user's tier for mode eligibility, and only then dispatches. No
   expert-specific routing logic duplicated in the frontend.
3. **Mode access is enforced server-side.** A free-tier user's request for
   online mode must be rejected by the backend (403) regardless of what
   the client sends. Check the user's subscription/credit row in Supabase
   on every online-mode request.
4. **Expert definitions are data, not code.** Each expert's name, system
   prompt, RAG namespace, and risk tier (`standard` | `high_stakes`) live
   in one config file (`experts.yaml`). Adding expert #6 must not require
   new Python branches.
5. **Async FastAPI throughout.** The offline model loads once into a
   module-level singleton, never reloaded per request.
6. **No secrets in code.** All config via `.env` / Supabase service role
   key, never hardcoded.
7. **Rate limiting on offline mode**, enforced server-side and recorded in
   a Supabase `usage_log` table — it's a shared CPU resource; one user
   must not be able to starve the other 99.
8. **Every interaction is audited** (timestamp, user, expert, mode,
   success/fail).

## High-stakes expert rules (Med, Law) — non-negotiable

9. **Disclaimer acknowledgment gate.** A user must explicitly accept a
   per-expert disclaimer ("general information only, not a substitute for
   a licensed [physician/attorney], consult one for decisions about your
   [health/legal] situation") before their first query to Med or Law.
   Store `(user_id, expert, accepted_at)` in Supabase. The backend checks
   this row exists before answering — not just a frontend modal that can
   be skipped.
10. **Jurisdiction is mandatory input for Law**, collected before any
    substantive answer — law is jurisdiction-specific, and answering one
    country's law as if it were another's is actively harmful. Store the
    selected jurisdiction with the query in the audit log.
11. **Med agent constraints, enforced in the system prompt and verified in
    testing:** never give specific medication dosing, never instruct a
    user to start/stop/change a medication, never attempt diagnosis —
    frame everything as general information and point toward a clinician
    for anything actionable.
12. **Emergency short-circuit runs server-side, not just as a prompt
    instruction.** Before dispatching to Med or Law, the router checks the
    query against a classifier for medical emergencies (chest pain,
    severe bleeding, breathing difficulty, overdose, etc.) or a mental
    health crisis (suicidal ideation, self-harm). On a match, skip the
    normal agent entirely and return a fixed safe response directing to
    local emergency services or a crisis line — prompt-only safety is not
    a reliable enough backstop for this category. Bias the classifier
    toward false positives: over-triggering the safe response is the
    correct failure mode, under-triggering is not.
13. **RAG over free generation for high-stakes facts.** Med/Law answers
    should retrieve from a curated, source-cited document set (Supabase
    pgvector) rather than answer from raw model knowledge wherever
    possible, and the UI must surface the source.

## Tech stack

- Frontend: Next.js (Vercel), Tailwind, Supabase JS client
- Backend: FastAPI on a Hugging Face Space (CPU Basic, 16GB RAM)
- Offline inference: `llama-cpp-python` against one shared quantized GGUF
  model
- Online inference: external OpenAI-compatible API (Groq / Gemini free
  tier) via `httpx`
- Web search/fetch for online mode: `duckduckgo-search` + `httpx` (same
  pattern as the MCP web server from the prior project — reusable as-is,
  in-process, no MCP protocol needed here)
- DB / Auth / vector store: Supabase (Postgres + pgvector + Auth with
  Google provider)
- Tests: `pytest`, `pytest-asyncio`

## Coding conventions

- Type hints on every function signature.
- One class/module per concern — no god objects.
- Docstrings: one-line summary + Args/Returns, Google style.
- Max function length ~40 lines; extract helpers past that.
- Logging via `logging` module, never bare `print()` outside local dev
  scripts.
- No TODOs left in shipped code — either implement it or remove the stub.

## Definition of done

- The FastAPI backend starts locally against a `.env`, the Supabase
  migration applies cleanly, and a request through each of the 5 experts
  in offline mode returns a response.
- Med/Law cannot be queried without a stored disclaimer-acceptance row; an
  emergency-pattern query returns the fixed safe response, never a
  model-generated one.
- Online mode returns 403 for a user with no active subscription/credits.
- `pytest` passes.
