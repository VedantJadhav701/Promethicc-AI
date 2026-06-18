-- Promethicc AI — Initial Schema Migration
-- Requires: Supabase project with pgvector extension available

-- =============================================================================
-- Extensions
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA "extensions";

-- =============================================================================
-- profiles — user tier and credit balance
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id          uuid PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
    tier        text NOT NULL DEFAULT 'free'
                    CHECK (tier IN ('free', 'pro', 'enterprise')),
    credits     integer NOT NULL DEFAULT 0
                    CHECK (credits >= 0),
    created_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.profiles IS
    'User profiles storing subscription tier and credit balance.';

-- Auto-create a profile row when a new user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.profiles (id) VALUES (NEW.id);
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- =============================================================================
-- disclaimer_acceptances — per-expert disclaimer acknowledgment gate
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.disclaimer_acceptances (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES auth.users ON DELETE CASCADE,
    expert      text NOT NULL,
    accepted_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, expert)
);

COMMENT ON TABLE public.disclaimer_acceptances IS
    'Tracks per-user, per-expert disclaimer acceptance for high-stakes experts.';

CREATE INDEX IF NOT EXISTS idx_disclaimer_user_expert
    ON public.disclaimer_acceptances (user_id, expert);

-- =============================================================================
-- usage_log — rate limiting and usage tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.usage_log (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES auth.users ON DELETE CASCADE,
    expert      text NOT NULL,
    mode        text NOT NULL CHECK (mode IN ('offline', 'online')),
    tokens_used integer NOT NULL DEFAULT 0,
    created_at  timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.usage_log IS
    'Per-request usage logging for rate limiting and billing.';

CREATE INDEX IF NOT EXISTS idx_usage_user_date
    ON public.usage_log (user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_usage_user_mode_date
    ON public.usage_log (user_id, mode, created_at);

-- =============================================================================
-- audit_log — every interaction is audited
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.audit_log (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             uuid NOT NULL REFERENCES auth.users ON DELETE CASCADE,
    expert              text NOT NULL,
    mode                text NOT NULL CHECK (mode IN ('offline', 'online')),
    query               text NOT NULL,
    jurisdiction        text,
    emergency_triggered boolean NOT NULL DEFAULT false,
    success             boolean NOT NULL DEFAULT true,
    created_at          timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.audit_log IS
    'Comprehensive audit trail for every interaction.';

CREATE INDEX IF NOT EXISTS idx_audit_user_date
    ON public.audit_log (user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_audit_emergency
    ON public.audit_log (emergency_triggered)
    WHERE emergency_triggered = true;

-- =============================================================================
-- rag_documents — per-expert RAG document store with pgvector embeddings
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.rag_documents (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    expert       text NOT NULL,
    source_title text NOT NULL,
    source_url   text,
    content      text NOT NULL,
    embedding    extensions.vector(1536)
);

COMMENT ON TABLE public.rag_documents IS
    'Per-expert RAG document store with pgvector embeddings for retrieval.';

CREATE INDEX IF NOT EXISTS idx_rag_expert
    ON public.rag_documents (expert);

-- HNSW index for fast approximate nearest-neighbor search
CREATE INDEX IF NOT EXISTS idx_rag_embedding
    ON public.rag_documents
    USING ivfflat (embedding extensions.vector_cosine_ops)
    WITH (lists = 100);

-- =============================================================================
-- Row Level Security
-- =============================================================================

-- profiles: users can read/update their own profile
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY profiles_select ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY profiles_update ON public.profiles
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- disclaimer_acceptances: users can read/insert their own
ALTER TABLE public.disclaimer_acceptances ENABLE ROW LEVEL SECURITY;

CREATE POLICY disclaimer_select ON public.disclaimer_acceptances
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY disclaimer_insert ON public.disclaimer_acceptances
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- usage_log: users can read their own
ALTER TABLE public.usage_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY usage_select ON public.usage_log
    FOR SELECT USING (auth.uid() = user_id);

-- audit_log: users can read their own
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY audit_select ON public.audit_log
    FOR SELECT USING (auth.uid() = user_id);

-- rag_documents: public read for all authenticated users
ALTER TABLE public.rag_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY rag_select ON public.rag_documents
    FOR SELECT USING (auth.role() = 'authenticated');
