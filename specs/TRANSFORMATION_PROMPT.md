# ArogyaMitra AI — Stack Transformation Prompt
> Purpose: The current codebase was built on the WRONG stack (Node/Express/TypeScript
> with a JSON file "database"). This file is the single prompt + implementation guide
> to tear that down and rebuild on the CORRECT, specified stack: Python FastAPI +
> SQLAlchemy + PostgreSQL + Redis + LangGraph.
> Hand this entire file to your AI IDE as the next instruction.

---

## 0. What Went Wrong — Root Cause

```
The AI IDE's audit confirmed the actual repo is:
  - Express + TypeScript (server.ts) instead of FastAPI + Python
  - A JSON-file "database" (backend/database.ts) instead of SQLAlchemy + PostgreSQL
  - Node crypto instead of Python cryptography + python-jose
  - Google GenAI instead of Groq + LangGraph
  - No agent pipeline at all — agents were never actually built as LangGraph nodes
  - requirements.txt, FEATURES.md, TECH_STACK.md, PHASE1_CHECKLIST.md — none of
    the specs were ever placed in the repo, so there was nothing for the AI IDE
    to build against in the first place

This happened because the AI IDE that wrote the original code was never given
the actual spec files as context — it defaulted to a stack it assumed was
reasonable (Express is a common default) instead of following FEATURES.md /
TECH_STACK.md, which were never placed into the project directory.

THE FIX: delete the wrong implementation, place every spec file into the repo
root, and rebuild top-to-bottom following the exact build order already
defined — this time with Postgres + Redis from day one instead of SQLite,
per the updated database decision below.
```

---

## 1. Updated Database Decision — PostgreSQL + Redis From Day One

```
Prior guidance suggested SQLite for Phase 1, Postgres for Phase 2+. That
guidance is now SUPERSEDED. Build directly on PostgreSQL + Redis starting now,
for these reasons:

1. The current rebuild is starting from zero anyway — there is no SQLite data
   to migrate away from, so there is no cost to starting correctly.
2. Free-tier Postgres (Supabase, Neon, or Railway) costs the same as SQLite:
   ₹0. The "SQLite is free" argument no longer holds an advantage once you
   factor in that Postgres free tiers are equally free.
3. Multi-user auth, family profiles, and concurrent agent pipeline writes
   are all specified even in Phase 1-adjacent work — Postgres's row-level
   locking avoids rebuilding the data layer a second time at Phase 2.
4. Redis gives you the TTL cache (already specified in PRODUCTION_BACKEND.md
   §4.3) as a real shared cache instead of an in-process Python dict —
   this matters the moment you deploy more than one backend instance, and
   costs nothing to set up now versus retrofitting later.

CHOSEN STACK:
  Database  : PostgreSQL 16 (via Supabase free tier, or Neon free tier,
              or local Docker Postgres for development)
  Cache     : Redis 7 (via Upstash free tier for serverless-friendly Redis,
              or local Docker Redis for development)
  ORM       : SQLAlchemy 2.0 (async-capable, same as previously specified)
  Migrations: Alembic (from day one — not deferred to Phase 2)
```

---

## 2. Pre-Transformation Checklist — Do This First

```
Before writing a single line of new code, the AI IDE must:

1. Confirm it has ALL of these spec files available in its context /
   placed in the repository root under a /specs/ folder:
     - FEATURES.md
     - TECH_STACK.md
     - PHASE1_CHECKLIST.md
     - FEATURES_PHASE2.md
     - TECH_STACK_PHASE2.md
     - PHASE2_CHECKLIST.md
     - FEATURES_PHASE3.md
     - PRODUCTION_BACKEND.md
     - SECURITY_AUDIT.md
     - MASTER_STATUS_CHECKLIST.md
     - THIS FILE (TRANSFORMATION_PROMPT.md)

   If any of these are missing from the repo, STOP and request them before
   writing any code. Building without the spec files in context is exactly
   how the wrong stack got built the first time.

2. Create a fresh git branch for the rebuild: `git checkout -b python-rebuild`
   — do not rebuild on main/master in case anything in the old app needs
   to be referenced during transition.

3. Archive the old implementation instead of deleting it outright:
   `git mv server.ts backend/database.ts backend/security.ts backend/models
    backend/exceptions src App.tsx package.json _archive_express_version/`
   This preserves any business-logic reasoning (the OOP validation rules in
   the old .ts model files, for example, may still be useful reference even
   though the language changes) without letting old files interfere with
   the new build.

4. Confirm Python 3.11+ is available: `python --version`
5. Confirm Docker is available (for local Postgres + Redis during dev):
   `docker --version`
```

---

## 3. The Master Transformation Prompt

```
Copy everything between the lines below and give it to your AI IDE as one message.
```

---

**BEGIN PROMPT TO AI IDE**

You are rebuilding ArogyaMitra AI from scratch on the correct stack. The
previous implementation in this repository was built on the wrong stack
(Express/TypeScript/JSON-file-database) and must be fully replaced. Do not
reuse, port, or translate any code from `_archive_express_version/` — treat
it as reference material only for validation-rule intent, never as a
starting point for new files.

**Required stack — no substitutions:**
- Backend: Python 3.11+, FastAPI, Uvicorn
- ORM: SQLAlchemy 2.0 + Alembic migrations
- Database: PostgreSQL 16 (connection string will be provided via `DATABASE_URL` in `.env`)
- Cache: Redis 7 (connection string via `REDIS_URL` in `.env`)
- AI: Groq (`llama-3.3-70b-versatile` + `llama-3.1-8b-instant`), LangGraph for agent orchestration
- Vector store: ChromaDB
- OCR: Tesseract (`pytesseract`) + EasyOCR
- Security: `cryptography` (AES-256-GCM), `python-jose` (JWT), `passlib[bcrypt]`
- Frontend: React + Vite + Tailwind CSS + Recharts + Axios

**Your source of truth, in this exact priority order:**
1. `/specs/FEATURES.md` and `/specs/TECH_STACK.md` — the core Phase 1 spec
2. `/specs/PRODUCTION_BACKEND.md` — how every backend concern (logging, DI,
   caching, exceptions, prompt injection, guardrails) must be implemented
3. `/specs/SECURITY_AUDIT.md` — every item here must pass before this is
   considered done, not just "working"
4. `/specs/PHASE1_CHECKLIST.md` — your Phase 1 acceptance test, item by item
5. `/specs/MASTER_STATUS_CHECKLIST.md` — Section 1 and 2 define exactly what
   "tech stack verified" and "Phase 1 feature complete" mean — build toward
   making every row in those tables honestly markable ✅ DONE

**Database specifics for this rebuild:**
- Use PostgreSQL via `DATABASE_URL` env var (format:
  `postgresql://user:pass@host:port/dbname`), never SQLite, starting from
  the very first migration.
- Use Redis via `REDIS_URL` env var for the TTL cache layer specified in
  `PRODUCTION_BACKEND.md` Section 4.3 — replace the `cachetools.TTLCache`
  in-process pattern with `redis-py` (`redis.asyncio` client), keeping the
  exact same cache key convention, TTL values per cache name, and
  invalidation rules already specified. The `ArogyaCache` class interface
  (`get`, `set`, `invalidate`, `invalidate_user`) stays identical — only
  the storage backend changes from an in-process dict to Redis.
- Initialize Alembic on the first commit of this rebuild — do not defer
  migrations to "later." Every schema change from this point forward goes
  through an Alembic revision, never a bare `Base.metadata.create_all()`
  in production code paths (that pattern is for local dev convenience only
  and must be clearly gated behind `if ENVIRONMENT == "development"`).

**Build order — follow exactly, verify each step before moving to the next:**

```
Step 1 — Foundation
  - backend/config.py (Settings class, SUPPORTED_PARAMETERS, all constants
    from TECH_STACK.md)
  - backend/database.py (async SQLAlchemy engine singleton pointed at
    DATABASE_URL, session factory, get_db dependency)
  - backend/core/redis_client.py (Redis connection singleton pointed at
    REDIS_URL)
  - backend/core/cache.py (ArogyaCache class backed by Redis, per
    PRODUCTION_BACKEND.md §4.3, keys/TTLs unchanged from spec)
  - backend/core/logger.py (loguru setup, exact sinks from
    PRODUCTION_BACKEND.md §1.3)
  - backend/exceptions/arogya_errors.py (full exception hierarchy from
    FEATURES.md §4)
  - alembic/ initialized, env.py configured to read DATABASE_URL from
    Settings, first empty migration generated and applied
  - Verify: `uvicorn backend.main:app --reload` boots with zero errors,
    `GET /health` returns 200, Postgres connection confirmed live,
    Redis connection confirmed live

Step 2 — Core Services
  - backend/services/ocr_service.py (Tesseract + EasyOCR wrapper)
  - backend/services/entity_extractor.py (regex + Groq fallback,
    sanitize_for_prompt() applied per PRODUCTION_BACKEND.md §7.2)
  - backend/services/encryption_service.py (AES-256-GCM, exact pattern
    from PRODUCTION_BACKEND.md)
  - backend/core/prompt_guard.py (injection pattern list + sanitize_for_prompt)
  - backend/core/guardrails.py (output guardrail rules + apply_output_guardrails)
  - Verify: upload a sample PDF through a standalone test script (not yet
    via API), confirm OCR extracts text, entities extracted, file encrypts/
    decrypts correctly round-trip

Step 3 — ORM Models + Repositories
  - backend/models/ — all 5 Phase 1 SQLAlchemy ORM models (HealthRecord,
    ClinicalParameter, RiskScore, Reminder, DoctorReport) exactly matching
    FEATURES.md §2 attribute lists and TECH_STACK.md §4 table schemas
  - backend/repositories/ — one repository class per entity, EVERY method
    filters by user_id per PRODUCTION_BACKEND.md §4.2 and
    SECURITY_AUDIT.md §5 (IDOR prevention) — this is non-negotiable,
    verify every single query has the ownership filter before moving on
  - Alembic migration generated for all 5 tables, applied to the Postgres
    instance
  - Verify: `alembic upgrade head` succeeds, all 5 tables exist in Postgres
    (confirm via `psql` or a DB GUI), repository CRUD methods tested via a
    standalone script against the real Postgres connection

Step 4 — Agent Pipeline (LangGraph)
  - backend/agents/graph.py (StateGraph, ArogyaState TypedDict exactly
    matching TECH_STACK.md §3)
  - backend/agents/ingestion_agent.py, trend_agent.py, reminder_agent.py,
    doctor_prep_agent.py — all 4 nodes, each wrapped in try/except per
    PRODUCTION_BACKEND.md §6.2 (errors go into state["errors"], never
    crash the graph)
  - backend/services/risk_engine.py (rule-based scoring per FEATURES.md §3,
    Feature 3)
  - Verify: run the full graph against a sample record via a standalone
    script, confirm RiskScore computed and saved, confirm Reminder created
    for a PRESCRIPTION-type sample

Step 5 — FastAPI Routers + Dependency Injection
  - backend/core/dependencies.py — all dependencies from
    PRODUCTION_BACKEND.md §5.1 that apply to Phase 1 (get_db, get_cache,
    get_record_repo, get_param_repo, get_risk_repo, get_reminder_repo,
    get_report_repo, get_ocr_service, get_encryption_service, get_settings)
  - backend/routers/records_router.py, params_router.py, reminders_router.py,
    reports_router.py, share_router.py — every endpoint from the Section 10
    checklist in PRODUCTION_BACKEND.md, matching that exact checklist
    line by line
  - backend/main.py — FastAPI app assembly: all middleware in the exact
    order from PRODUCTION_BACKEND.md §3.2 (TrustedHost → CORS →
    SecurityHeaders → RequestLogging → RateLimit), global exception
    handlers from §6.1, startup validation from §11
  - Verify: every endpoint in PHASE1_CHECKLIST.md Section "CRUD Operations"
    tested via `/docs` Swagger UI (dev only) or curl/httpie, confirm
    correct status codes and response shapes

Step 6 — Frontend
  - React + Vite + Tailwind project scaffolded fresh (do not reuse
    src/App.tsx from the archived version — build new per TECH_STACK.md
    §5 component map and FEATURES.md §5 feature list)
  - All 7 Phase 1 pages, Axios instance with interceptor, color palette
    exactly as specified (teal #1A6B5A / mint #4ECBA0)
  - Verify: full E2E flow — upload → dashboard updates → timeline renders →
    reminder created → doctor report generates → share link works

Step 7 — Security Audit Pass
  - Run the FULL SECURITY_AUDIT.md checklist against this new build —
    all 62 🔴 critical items must pass before this rebuild is considered
    functionally complete, not just "running"

Step 8 — Final Verification
  - Fill out MASTER_STATUS_CHECKLIST.md Sections 1 and 2 honestly against
    this new codebase
  - Report the real numbers — do not mark anything ✅ DONE without having
    actually tested it as instructed in that file's Section 0
```

**Do not skip verification steps between stages.** Each step above ends with
a "Verify:" line — actually perform that verification and report the result
before proceeding to the next step. If a verification fails, fix it before
moving forward. This is exactly the discipline that was skipped the first
time, which is how the stack mismatch happened undetected.

**END PROMPT TO AI IDE**

---

## 4. Environment Variables for the New Stack

```env
# ── Database (NEW — Postgres, not SQLite) ─────────────
DATABASE_URL=postgresql://user:password@host:5432/arogya_mitra
# Local dev via Docker: postgresql://arogya:arogya_dev@localhost:5432/arogya_mitra

# ── Cache (NEW — Redis, not in-process dict) ──────────
REDIS_URL=redis://default:password@host:6379
# Local dev via Docker: redis://localhost:6379/0

# ── LLM ──────────────────────────────────────────────
GROQ_API_KEY=your_groq_api_key_here

# ── Security ─────────────────────────────────────────
SECRET_KEY=generate_with_openssl_rand_hex_32
ENCRYPTION_KEY=generate_with_python_os_urandom_32_base64

# ── App ──────────────────────────────────────────────
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=["http://localhost:5173"]

# ── Storage ──────────────────────────────────────────
UPLOAD_DIR=./backend/data/records/encrypted
CHROMA_DB_PATH=./backend/data/chroma_db
```

### Local Development Docker Setup

```yaml
# docker-compose.dev.yml — for local Postgres + Redis during development
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: arogya
      POSTGRES_PASSWORD: arogya_dev
      POSTGRES_DB: arogya_mitra
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

```
Run: docker compose -f docker-compose.dev.yml up -d
Then: DATABASE_URL=postgresql://arogya:arogya_dev@localhost:5432/arogya_mitra
      REDIS_URL=redis://localhost:6379/0
```

### Production Hosting (Free Tier Options)

```
PostgreSQL:
  Supabase  → 500MB free, includes connection pooling (pgBouncer) built in
  Neon      → 0.5GB free, serverless Postgres, scales to zero when idle

Redis:
  Upstash   → 10,000 commands/day free, REST + TCP access, serverless-friendly
  Redis Cloud → 30MB free tier

Recommendation: Supabase (Postgres) + Upstash (Redis) — both have generous
free tiers, both integrate cleanly with FastAPI via standard connection
strings, and both have a clear upgrade path when ArogyaMitra needs to scale.
```

---

## 5. Updated requirements.txt (Postgres + Redis additions)

```
# ── Previously specified (unchanged) ──────────────────
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
groq==0.9.0
langchain==0.2.5
langgraph==0.1.14
langchain-groq==0.1.6
pytesseract==0.3.13
easyocr==1.7.1
Pillow==10.3.0
pdf2image==1.17.0
chromadb==0.5.3
sentence-transformers==3.0.1
reportlab==4.2.2
cryptography==42.0.8
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.7.4
pydantic-settings==2.3.3
email-validator==2.2.0
python-dotenv==1.0.1
python-dateutil==2.9.0.post0
loguru==0.7.2
slowapi==0.1.9
python-magic==0.4.27

# ── NEW — PostgreSQL ───────────────────────────────────
sqlalchemy==2.0.30
alembic==1.13.1
psycopg2-binary==2.9.9        # sync driver for Alembic migrations
asyncpg==0.29.0                # async driver for FastAPI runtime queries

# ── NEW — Redis ────────────────────────────────────────
redis==5.0.4
```

---

## 6. Updated database.py Pattern (Postgres + Async)

```
Implementation instructions for the AI IDE:

Use SQLAlchemy 2.0's async engine for runtime queries (FastAPI routes),
and keep a sync engine available specifically for Alembic migrations
(Alembic does not natively support async well — this split is standard
practice, not a compromise).

backend/database.py:

  from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
  from sqlalchemy.orm import declarative_base

  Base = declarative_base()

  _async_engine = None
  _async_session_factory = None

  def get_async_engine():
      global _async_engine
      if _async_engine is None:
          # Convert postgresql:// to postgresql+asyncpg:// for the async driver
          async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
          _async_engine = create_async_engine(
              async_url,
              pool_size=10,
              max_overflow=20,
              pool_pre_ping=True,
              pool_recycle=3600,
              echo=settings.DEBUG,
          )
      return _async_engine

  def get_async_session_factory():
      global _async_session_factory
      if _async_session_factory is None:
          _async_session_factory = async_sessionmaker(
              bind=get_async_engine(),
              expire_on_commit=False,
              class_=AsyncSession,
          )
      return _async_session_factory

  async def get_db() -> AsyncGenerator[AsyncSession, None]:
      factory = get_async_session_factory()
      async with factory() as session:
          try:
              yield session
              await session.commit()
          except Exception:
              await session.rollback()
              raise

alembic/env.py uses the SYNC driver (psycopg2) for running migrations —
this is standard Alembic practice and does not need to match the runtime
async driver:

  sync_url = settings.DATABASE_URL  # plain postgresql:// — psycopg2 compatible
  config.set_main_option("sqlalchemy.url", sync_url)

All repository methods and route handlers switch to `async def` and `await`
on every DB call, since the engine is now async. This is a meaningful
change from the earlier SQLite-based sync pattern — every repository
method signature changes from:
  def get_by_id(self, record_id, user_id) -> Optional[HealthRecord]:
to:
  async def get_by_id(self, record_id, user_id) -> Optional[HealthRecord]:
      result = await self.db.execute(select(HealthRecord).where(...))
      return result.scalar_one_or_none()
```

---

## 7. Updated cache.py Pattern (Redis)

```
Implementation instructions for the AI IDE:

Replace the in-process cachetools.TTLCache with redis.asyncio, keeping the
exact same public interface so every call site (get/set/invalidate/
invalidate_user) stays unchanged — only the backend storage changes.

backend/core/redis_client.py:

  import redis.asyncio as redis

  _redis_client = None

  def get_redis_client():
      global _redis_client
      if _redis_client is None:
          _redis_client = redis.from_url(
              settings.REDIS_URL,
              decode_responses=True,
              max_connections=20,
          )
      return _redis_client

backend/core/cache.py:

  import json

  CACHE_TTL_SECONDS = {
    "risk_score":        300,
    "clinical_params":   180,
    "reminders_today":   60,
    "family_profiles":   600,
    "active_model":      3600,
    "drug_interactions": 300,
  }

  class ArogyaCache:
    def __init__(self, redis_client):
        self.redis = redis_client

    def _key(self, cache_name: str, key: str) -> str:
        return f"arogya:{cache_name}:{key}"

    async def get(self, cache_name: str, key: str) -> Optional[Any]:
        raw = await self.redis.get(self._key(cache_name, key))
        if raw is None:
            logger.debug(f"[Cache] MISS | {cache_name} | {key}")
            return None
        logger.debug(f"[Cache] HIT | {cache_name} | {key}")
        return json.loads(raw)

    async def set(self, cache_name: str, key: str, value: Any) -> None:
        ttl = CACHE_TTL_SECONDS.get(cache_name, 300)
        await self.redis.setex(self._key(cache_name, key), ttl, json.dumps(value))
        logger.debug(f"[Cache] SET | {cache_name} | {key} | ttl={ttl}s")

    async def invalidate(self, cache_name: str, key: str) -> None:
        await self.redis.delete(self._key(cache_name, key))
        logger.debug(f"[Cache] INVALIDATE | {cache_name} | {key}")

    async def invalidate_user(self, user_id: str) -> None:
        # Scan for all keys containing this user_id across all cache namespaces
        pattern = f"arogya:*:*{user_id}*"
        async for k in self.redis.scan_iter(match=pattern):
            await self.redis.delete(k)

  def get_cache() -> ArogyaCache:
      return ArogyaCache(get_redis_client())

IMPORTANT: every call site that used `cache.get(...)` / `cache.set(...)`
synchronously must now `await` these calls — this changes route handler
signatures to async def wherever caching is used (which, since the DB
layer is already async per Section 6, should already be the case).
```

---

## 8. What NOT to Carry Over From the Old Codebase

```
Explicitly discard, do not port, do not translate:

- server.ts in its entirety — the Express routing structure does not map
  cleanly to FastAPI's dependency-injection model; a direct port would
  recreate the architectural problems, not fix them
- backend/database.ts (JSON file storage) — there is no safe migration
  path from a JSON file to Postgres that preserves meaningful data, since
  this was never real production data
- backend/security.ts (Node crypto) — Python's cryptography library has a
  different API surface; do not attempt a line-by-line translation, follow
  PRODUCTION_BACKEND.md §3 and SECURITY_AUDIT.md's Python-specific patterns
  instead
- Any Google GenAI integration code — this project uses Groq + LangGraph
  exclusively per TECH_STACK.md; remove all Google GenAI SDK references
  and API keys entirely
- package.json's Express-specific dependencies (express, cors as an npm
  package, etc.) — the frontend keeps its own package.json for React/Vite
  only; the backend has no package.json at all, only requirements.txt

What MAY be worth a quick read (reference only, not reuse):
- backend/models/*.ts — the validation rule THINKING (what makes a title
  "empty", what date range counts as "future") may match FEATURES.md
  already, since the original build was presumably working from some
  version of the spec. A quick comparison can confirm the Python version's
  validate() methods aren't missing an edge case the old version caught.
  But the CODE itself is not reused — only the validation logic concept,
  cross-checked against FEATURES.md as the authority.
```

---

## 9. Post-Transformation Verification Checklist

```
After the AI IDE completes the rebuild, verify these specifically —
this is the proof that the transformation actually worked, not just that
new files exist:
```

- [ ] 🔴 `requirements.txt` exists with zero Node/npm backend dependencies anywhere in the repo
- [ ] 🔴 `_archive_express_version/` contains the old `server.ts`, old `backend/`, old `App.tsx` — confirm these are NOT imported or referenced by any new Python file
- [ ] 🔴 `uvicorn backend.main:app --reload` boots with zero errors
- [ ] 🔴 `GET /health` returns `200 {"status": "ok"}`
- [ ] 🔴 `DATABASE_URL` points to a real PostgreSQL instance — confirm via `psql $DATABASE_URL -c "\dt"` showing all 5 Phase 1 tables
- [ ] 🔴 `REDIS_URL` points to a real Redis instance — confirm via `redis-cli -u $REDIS_URL ping` returns `PONG`
- [ ] 🔴 `alembic current` shows a valid applied migration head (not empty, not "no migrations")
- [ ] 🔴 A cache test: call an endpoint twice in a row, confirm the second call logs `[Cache] HIT` (proves Redis caching is actually wired, not just imported)
- [ ] 🔴 LangGraph graph compiles: `python -c "from backend.agents.graph import graph; print(graph)"` runs without error
- [ ] 🔴 Full upload → OCR → agent pipeline → risk score E2E test passes against the real Postgres + Redis instances
- [ ] 🟠 `npm run build` (frontend only) completes without error
- [ ] 🟠 All environment variables from Section 4 above are present in `.env` with real (non-placeholder) values
- [ ] 🟠 `pip-audit -r requirements.txt` run and clean (per SECURITY_AUDIT.md §10)
- [ ] 🟡 Old TypeScript backend fully removed from any CI/CD or deployment config (Dockerfile, Procfile, etc. — these must now reference `uvicorn`, not `node`)

**Once every 🔴 item above is checked, re-run `MASTER_STATUS_CHECKLIST.md`
Sections 1 and 2 in full — that is the real, honest measure of where Phase 1
actually stands after this transformation.**

---

*End of TRANSFORMATION_PROMPT.md*
*ArogyaMitra AI — Stack Transformation: Express/JSON → FastAPI/PostgreSQL/Redis*
