# ArogyaMitra AI — Full Security Audit & Hardening Guide
> Scope: Pre-launch security lockdown — every item below must pass before going live
> Target: AI IDE context file — implementation guide + line-item checklist
> Severity key: 🔴 CRITICAL (blocks launch) | 🟠 HIGH | 🟡 MEDIUM

---

## 0. How to Use This File

Give this file to your AI IDE with the instruction: *"Audit the codebase against every section below. For each unchecked item, fix it and mark it done."* Run this audit before every production deploy, not just once. Treat 🔴 items as non-negotiable — the app does not go live with any 🔴 unchecked.

---

## 1. Secrets & API Key Protection

### 1.1 Implementation Guide

```
RULE: No secret ever appears in source code, client-side JS, logs, or git history.
A "secret" = API keys, SECRET_KEY, ENCRYPTION_KEY, DB credentials, JWT signing keys,
Razorpay keys, Twilio auth tokens, any password.

Steps:
1. Every secret lives ONLY in .env — loaded via pydantic-settings (Settings class)
2. .env is in .gitignore from the FIRST commit — verify before any code is written
3. Create .env.example with placeholder values ("your_key_here") — this IS committed,
   so collaborators know what variables exist without seeing real values
4. NEVER pass a secret into:
   - A React component prop
   - A URL query parameter
   - A client-visible API response
   - console.log() or logger.debug() anywhere
5. Frontend NEVER holds a real secret. If frontend needs to call Groq/Razorpay,
   it calls YOUR backend, which holds the key and proxies the call server-side.
   VITE_ prefixed env vars are bundled into client JS and PUBLIC — never put a
   secret behind VITE_*. Only VITE_API_BASE_URL (a URL, not a secret) is safe there.
6. Secrets manager for production (choose one):
   - Railway/Render: built-in environment variable vault (encrypted at rest)
   - Docker: secrets mounted as files, not env vars, in production
   - Never: secrets baked into a Docker image layer
```

### 1.2 Checklist

- [ ] 🔴 `.env` is listed in `.gitignore` — confirm with `git check-ignore .env` (should print the path)
- [ ] 🔴 `.env` has never been committed — run `git log --all --full-history -- .env` (must be empty)
- [ ] 🔴 No API key, password, or secret appears as a literal string anywhere in `.py`, `.jsx`, `.js`, `.json`, `.yaml`, or `.md` files (except `.env.example` placeholders)
- [ ] 🔴 `GROQ_API_KEY` only ever read via `settings.GROQ_API_KEY` — never hardcoded, never in a comment
- [ ] 🔴 No secret is prefixed with `VITE_` in `.env` (anything `VITE_*` ships to the browser)
- [ ] 🔴 Frontend code contains zero references to `GROQ_API_KEY`, `SECRET_KEY`, `ENCRYPTION_KEY`, Razorpay secret, or Twilio auth token
- [ ] 🟠 `.env.example` exists with every required variable name and a placeholder value (no real values)
- [ ] 🟠 Production secrets differ from development secrets (never reuse a dev `SECRET_KEY` in prod)
- [ ] 🟠 `SECRET_KEY` is 64+ random characters — generate with `openssl rand -hex 32`
- [ ] 🟠 `ENCRYPTION_KEY` is a freshly generated 32-byte base64 value — generate with `python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"`
- [ ] 🟡 Secrets rotated if this project was ever public/shared before this audit (assume any previously-exposed key is compromised — regenerate ALL of them)
- [ ] 🟡 Razorpay/Twilio keys (Phase 3) stored as separate env vars, never combined into a single string

---

## 2. Environment Variable Audit

### 2.1 Implementation Guide

```
Every variable in config.py's Settings class must be:
  a) Required (no silent default for anything security-sensitive)
  b) Validated at startup — app refuses to boot if malformed

Add a startup validation function in main.py (lifespan event):

def validate_environment():
    errors = []
    if len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY must be at least 32 characters")
    try:
        key_bytes = base64.b64decode(settings.ENCRYPTION_KEY)
        if len(key_bytes) != 32:
            errors.append("ENCRYPTION_KEY must decode to exactly 32 bytes")
    except Exception:
        errors.append("ENCRYPTION_KEY is not valid base64")
    if not settings.GROQ_API_KEY.startswith("gsk_"):
        errors.append("GROQ_API_KEY does not match expected Groq key format")
    if settings.DEBUG and settings.ENVIRONMENT == "production":
        errors.append("DEBUG=True is not allowed when ENVIRONMENT=production")
    if "*" in settings.CORS_ORIGINS:
        errors.append("CORS_ORIGINS must not contain wildcard '*' in production")
    if errors:
        for e in errors:
            logger.critical(f"[StartupValidation] {e}")
        raise SystemExit("Startup aborted — fix .env before running. See logs.")
```

### 2.2 Checklist

- [ ] 🔴 `ENVIRONMENT` variable exists (`development` | `staging` | `production`) and is checked at startup
- [ ] 🔴 App refuses to start if `DEBUG=True` AND `ENVIRONMENT=production` simultaneously
- [ ] 🔴 `CORS_ORIGINS` contains zero wildcards (`*`) when `ENVIRONMENT=production`
- [ ] 🔴 `SECRET_KEY` length validated (≥32 chars) at startup — app exits with clear error if too short
- [ ] 🔴 `ENCRYPTION_KEY` validated as proper base64 decoding to exactly 32 bytes at startup
- [ ] 🟠 All DB connection strings use the `postgresql://` or `sqlite:///` scheme explicitly — no bare paths
- [ ] 🟠 No environment variable has a hardcoded fallback value for anything security-related (`os.getenv("SECRET_KEY", "default123")` is forbidden — must raise if missing)
- [ ] 🟠 `.env` file permissions restricted on the server: `chmod 600 .env` (owner read/write only)
- [ ] 🟡 A documented list of every required env var exists in README or `.env.example` with a one-line description of what breaks if it's missing

---

## 3. Admin Route Protection

### 3.1 Implementation Guide

```
Add an is_admin boolean to the User model (default False).
Create a dedicated dependency — never reuse get_current_user alone for admin routes.

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        logger.warning(f"[AdminAccess] DENIED | user_id={current_user.user_id} | not_admin")
        raise HTTPException(status_code=404)  # 404, NOT 403 — don't reveal the route exists
    return current_user

Apply to every /api/admin/* route:
  current_admin: User = Depends(require_admin)

Why 404 instead of 403: a 403 confirms to an attacker that the route exists and
they just lack permission — inviting further probing (credential stuffing, etc).
A 404 makes the admin route indistinguishable from a route that doesn't exist.

Additional hardening:
  - Admin routes live under a non-obvious prefix in production, e.g. not /api/admin
    but something unguessable, OR kept at /api/admin but protected by BOTH
    require_admin AND IP allowlist if your hosting supports it
  - No admin account is ever seeded with a default/known password — the first
    admin is promoted manually via direct DB access or a one-time secure CLI script,
    never via a public signup flow with an "admin" checkbox
  - Admin actions (model activation, user deactivation) are logged at INFO level
    with admin's user_id for audit trail
```

### 3.2 Checklist

- [ ] 🔴 Every route under `/api/admin/*` has `Depends(require_admin)` — grep the router file to confirm no route is missing it
- [ ] 🔴 `require_admin` returns `404`, not `403`, to non-admin authenticated users
- [ ] 🔴 No admin account exists with a default or predictable password
- [ ] 🔴 No public registration endpoint allows a user to self-assign `is_admin=True` (verify the registration Pydantic schema does not accept an `is_admin` field from the client)
- [ ] 🟠 Admin actions are logged with the acting admin's `user_id` and the action taken
- [ ] 🟠 `is_admin` field is excluded from the `User.to_dict()` output shown to the user themselves (don't leak role info unnecessarily)
- [ ] 🟡 Admin session timeout is shorter than regular user session (e.g. 10 min access token vs 15 min) if feasible
- [ ] 🟡 Consider 2FA for admin accounts in Phase 2+ (TOTP via `pyotp`)

---

## 4. Authentication Hardening

### 4.1 Implementation Guide

```
Already specified in TECH_STACK_PHASE2.md and PRODUCTION_BACKEND.md — this section
is the audit pass to confirm it was built correctly, not new design.

Verify these exact behaviors exist:

1. Password hashing: passlib[bcrypt], rounds >= 12
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

2. Login timing-safe comparison:
   User.verify_password() uses pwd_context.verify() — bcrypt is constant-time by design,
   but ALSO verify that when email doesn't exist, the code still runs a dummy bcrypt
   check (prevents timing attack revealing whether an email is registered):

   def login(email, password, db):
       user = db.query(User).filter(User.email == email).first()
       if user:
           valid = pwd_context.verify(password, user.hashed_password)
       else:
           pwd_context.verify(password, DUMMY_HASH)  # constant-time decoy
           valid = False
       if not valid:
           raise InvalidCredentialsError("Invalid credentials")  # same message either way

3. JWT access token: 15 min expiry, HS256, in-memory only on client
4. Refresh token: 7 day expiry, httpOnly + Secure + SameSite=Strict cookie
5. Logout invalidates refresh_jti_hash server-side (not just client-side token deletion)
6. Account lockout: after 10 failed logins within 1 hour for the SAME email
   (separate from the IP-based rate limit), temporarily lock that account for 15 min
   — log this as a WARNING, notify user via email if email service exists
```

### 4.2 Checklist

- [ ] 🔴 Passwords hashed with bcrypt, cost factor ≥ 12 — confirm in `auth_service.py`
- [ ] 🔴 No password ever appears in a log line (grep logs for "password" after a test login attempt — should find zero matches of actual password values)
- [ ] 🔴 Login failure message is identical for "wrong password" and "email not found" — confirm by testing both cases return the same JSON body
- [ ] 🔴 Access token stored in React state/memory only — confirm zero `localStorage.setItem` or `sessionStorage.setItem` calls for tokens anywhere in frontend code
- [ ] 🔴 Refresh token cookie has `HttpOnly`, `Secure`, `SameSite=Strict` flags set — confirm in the `Set-Cookie` response header during a login test
- [ ] 🔴 JWT `SECRET_KEY` is never the same value as `ENCRYPTION_KEY` (separate keys for separate purposes)
- [ ] 🟠 Account lockout after repeated failed logins implemented (per-email, not just per-IP)
- [ ] 🟠 Logout endpoint invalidates the refresh token server-side (`refresh_jti_hash = None`), not just client-side cookie clearing
- [ ] 🟠 Password reset flow (if implemented) uses a single-use, time-limited token — never emails the password itself
- [ ] 🟡 Consider adding `pwned-passwords` check (HaveIBeenPwned API, k-anonymity model) to reject known-breached passwords at registration

---

## 5. Authorization — Users Only Access What They're Supposed To

### 5.1 Implementation Guide

```
This is the single most common health-app vulnerability: a correctly authenticated
user accessing ANOTHER user's data by changing an ID in the URL (IDOR — Insecure
Direct Object Reference).

THE RULE, with no exceptions: every single repository method that reads, updates,
or deletes a row MUST filter by the current user's ownership — never trust a
record_id/profile_id/reminder_id from the URL alone.

WRONG (vulnerable):
  def get_record(record_id: str, db: Session):
      return db.query(HealthRecord).filter(HealthRecord.record_id == record_id).first()
      # Any logged-in user can read ANY record by guessing/incrementing IDs

RIGHT (safe):
  def get_record(record_id: str, user_id: str, db: Session):
      return db.query(HealthRecord).filter(
          HealthRecord.record_id == record_id,
          HealthRecord.user_id == user_id,   # ← the mandatory ownership filter
          HealthRecord.is_deleted == False
      ).first()
      # Returns None if record exists but belongs to someone else → route returns 404

The 404 (not 403) rule applies here too: if the record belongs to another user,
return "not found", never "forbidden" — don't confirm the record's existence to
someone who shouldn't see it.

Apply this pattern to EVERY repository: HealthRecordRepository, ClinicalParameterRepository,
RiskScoreRepository, ReminderRepository, DoctorReportRepository, FamilyProfileRepository,
DoctorAccessRepository, WearableTokenRepository — every single one, no exceptions.

For Phase 3 family profiles: the filter is profile_id AND profile.owner_user_id == current_user.user_id
— a two-hop check, since records belong to a profile, and profiles belong to a user.

For nested resources (ClinicalParameter belongs to HealthRecord which belongs to User):
verify ownership through the JOIN, not just by trusting the child ID:
  db.query(ClinicalParameter).join(HealthRecord).filter(
      ClinicalParameter.param_id == param_id,
      HealthRecord.user_id == user_id
  ).first()
```

### 5.2 Checklist

- [ ] 🔴 Every repository `get_by_id`, `update`, `delete` method includes a `user_id` (or `profile_id` with ownership chain) filter in its query — audit each repository file line by line
- [ ] 🔴 Write a test: User A creates a record, note its `record_id`. Log in as User B, call `GET /api/records/{A's record_id}`. Must return `404`, not the data.
- [ ] 🔴 Repeat the IDOR test for: reminders, risk scores, doctor reports, clinical parameters, family profiles (Phase 3), wearable readings (Phase 3)
- [ ] 🔴 Share link endpoints (`/share/{token}`, `/doctor-view/{token}`) derive the record/report from the TOKEN's signed payload — never from a separate URL parameter that could be tampered with
- [ ] 🔴 File download endpoints re-verify ownership on every request — not just at upload time
- [ ] 🟠 Pydantic request schemas never accept `user_id` or `owner_user_id` as a client-settable field — these are always derived server-side from the JWT, never trusted from the request body
- [ ] 🟠 Admin endpoints that operate on a specific user's data (if any exist) are separately audited — admin bypass of ownership checks must be intentional and logged, not accidental
- [ ] 🟡 Rate limit IDOR probing specifically: if a user receives >10 `404`s on `/api/records/{id}` within a minute, log as WARNING (possible ID enumeration attempt)

---

## 6. Form Input Sanitization

### 6.1 Implementation Guide

```
Two layers required: Pydantic validation (structural) + explicit sanitization (content).
Pydantic alone is NOT sanitization — it validates types/formats, not malicious content.

Layer 1 — Pydantic schemas (every request body):
  class ReminderCreateSchema(BaseModel):
      title: str = Field(..., min_length=3, max_length=200)
      due_date: datetime
      recurrence: Literal["NONE", "DAILY", "WEEKLY", "MONTHLY"]
      reminder_type: Literal["MEDICATION", "TEST_DUE", "DOCTOR_VISIT", "REFILL"]

      @field_validator("title")
      @classmethod
      def sanitize_title(cls, v):
          return sanitize_string(v, max_length=200)

Layer 2 — Explicit sanitize_string() (already specified in PRODUCTION_BACKEND.md
Section 3.4) applied to EVERY free-text field before it touches the DB or an LLM prompt:
  - Reminder title/description
  - Manual entry notes
  - FamilyProfile member_name
  - DoctorAccess doctor_name
  - Any "notes" or "description" field anywhere in the schema

Layer 3 — Output encoding (XSS prevention):
  React auto-escapes JSX content by default — this is your primary XSS defense.
  NEVER use dangerouslySetInnerHTML with user-provided or LLM-generated content.
  If you must render HTML (e.g. a formatted doctor report), sanitize server-side
  first with a library like bleach (Python) before sending to frontend, and still
  avoid dangerouslySetInnerHTML — prefer rendering as structured data the React
  component formats itself.

Layer 4 — SQL injection: already prevented by using SQLAlchemy ORM exclusively.
Confirm there is ZERO raw SQL string concatenation anywhere in the codebase:
  FORBIDDEN: db.execute(f"SELECT * FROM users WHERE email = '{email}'")
  REQUIRED:  db.query(User).filter(User.email == email).first()
```

### 6.2 Checklist

- [ ] 🔴 Every POST/PUT/PATCH endpoint has a Pydantic schema with explicit `min_length`/`max_length` on every string field — no bare `str` without constraints
- [ ] 🔴 `sanitize_string()` applied to every free-text field before DB storage: reminder title, manual entry notes, family member names, doctor names
- [ ] 🔴 Zero raw SQL string concatenation anywhere — grep for `execute(f"` and `.format(` near any SQL-looking string, confirm zero matches
- [ ] 🔴 Zero use of `dangerouslySetInnerHTML` in frontend code — grep confirms no matches, or if used, content is server-side sanitized with `bleach` first
- [ ] 🔴 File upload sanitization from Section 8.2 of `PRODUCTION_BACKEND.md` confirmed implemented: MIME verification via magic bytes, not just `Content-Type` header
- [ ] 🟠 Numeric fields (ClinicalParameter `value`, Reminder dates) validated as actual numbers/dates by Pydantic, not accepted as strings and parsed later
- [ ] 🟠 Enum fields (`record_type`, `recurrence`, `severity`) use Pydantic `Literal[...]` types — invalid values are rejected at the schema layer before reaching business logic
- [ ] 🟠 Email fields use `pydantic[email]`'s `EmailStr` type, not a bare `str` with manual regex
- [ ] 🟡 Unicode normalization (`NFC`) applied to all free-text to prevent homoglyph/lookalike-character tricks

---

## 7. XSS & CSRF Protection

### 7.1 Implementation Guide

```
XSS (Cross-Site Scripting):
  Primary defense: React's JSX auto-escaping (default behavior — don't fight it
  with dangerouslySetInnerHTML).
  Secondary defense: Content-Security-Policy header (see Section 9) restricts
  which script sources can execute even if an injection somehow occurs.
  Tertiary: sanitize all LLM-generated content before display, since an LLM
  output is semi-untrusted (could echo injected content from a malicious document).

CSRF (Cross-Site Request Forgery):
  Your refresh token cookie is the CSRF attack surface (access token in memory
  isn't vulnerable since it's not auto-sent by the browser like a cookie is).
  Defense: SameSite=Strict on the refresh_token cookie (already specified) —
  this alone blocks the cookie from being sent on cross-site requests, which
  neutralizes most CSRF scenarios for the refresh endpoint.
  Additional layer for state-changing endpoints (POST/PUT/DELETE):
  Verify the Origin or Referer header matches your expected domain:

  def verify_origin(request: Request):
      origin = request.headers.get("origin") or request.headers.get("referer")
      if origin and settings.ENVIRONMENT == "production":
          if not any(origin.startswith(o) for o in settings.CORS_ORIGINS):
              logger.warning(f"[CSRF] Origin mismatch: {origin}")
              raise HTTPException(status_code=403, detail="Invalid origin")

  Apply as middleware or dependency on all state-changing routes.
```

### 7.2 Checklist

- [ ] 🔴 Zero instances of `dangerouslySetInnerHTML` rendering unsanitized user or LLM content
- [ ] 🔴 `refresh_token` cookie has `SameSite=Strict` — confirmed in Section 4
- [ ] 🟠 `Content-Security-Policy` header restricts `script-src` to `'self'` only (no `unsafe-inline`, no `unsafe-eval`) — see Section 9 for exact value
- [ ] 🟠 Origin/Referer header verification implemented on state-changing endpoints (POST/PUT/PATCH/DELETE) in production
- [ ] 🟡 Any third-party embedded content (if added later) uses `sandbox` attribute on iframes

---

## 8. Rate Limiting

### 8.1 Implementation Guide

```
Already specified in detail in PRODUCTION_BACKEND.md Section 8.3 — this is the
audit confirmation pass. Verify every limit below is actually wired up with
slowapi's @limiter.limit() decorator, not just documented.

Two layers:
  Layer 1 (edge/CDN): Cloudflare rate limiting rules — blocks before it even
    reaches your server (cheapest defense)
  Layer 2 (application): slowapi — per-endpoint granular control

Confirm the RateLimitExceeded exception handler returns 429 with a Retry-After
header and does NOT leak internal details.

Also add a global default rate limit as a safety net for any endpoint that
doesn't have an explicit one:
  limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
```

### 8.2 Checklist

- [ ] 🔴 `POST /api/auth/login` limited to 5 requests per 15 minutes per IP
- [ ] 🔴 `POST /api/auth/register` limited to 3 requests per hour per IP
- [ ] 🔴 A global default rate limit exists covering any endpoint without an explicit override (prevents gaps)
- [ ] 🟠 `POST /api/records/upload` limited to 20 requests per hour per user
- [ ] 🟠 `POST /api/report/generate` limited to 10 requests per hour per user
- [ ] 🟠 `GET /share/{token}` limited to 30 requests per hour per IP (prevents brute-force token guessing)
- [ ] 🟠 `429` responses include a `Retry-After` header and a generic message — no internal rate-limit config exposed
- [ ] 🟡 Rate limit violations logged at WARNING with IP + endpoint for monitoring abuse patterns
- [ ] 🟡 Cloudflare (or equivalent CDN) edge rate limiting configured as a first line of defense, independent of the application layer

---

## 9. Security Headers & Core Settings

### 9.1 Implementation Guide

```
Exact header values to set via SecurityHeadersMiddleware (already specified in
PRODUCTION_BACKEND.md Section 3.2) — this is the precise CSP value to use:

Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.yourdomain.com;
  font-src 'self' https://fonts.gstatic.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self'

(style-src allows 'unsafe-inline' only because Tailwind's JIT sometimes needs it —
 tighten this if you pre-compile all Tailwind CSS at build time, which you should
 in production anyway via `npm run build`)

Other headers:
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(self), microphone=(self), payment=(self)

Remove identifying headers:
  Server header — suppress with uvicorn --no-server-header flag, or strip via
  reverse proxy (nginx: `server_tokens off;`)

Swagger/ReDoc exposure:
  In production: app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
  These interactive API docs are a reconnaissance goldmine for attackers —
  disable entirely in production, keep them only in development.
```

### 9.2 Checklist

- [ ] 🔴 `DEBUG=False` confirmed set in production `.env`
- [ ] 🔴 `/docs`, `/redoc`, `/openapi.json` all return `404` in production (confirm `docs_url=None, redoc_url=None, openapi_url=None` when `ENVIRONMENT=production`)
- [ ] 🔴 `Content-Security-Policy` header present on every response with the exact value above (no `unsafe-eval` anywhere)
- [ ] 🔴 `X-Frame-Options: DENY` present (prevents clickjacking via iframe embedding)
- [ ] 🔴 `Strict-Transport-Security` header present with `max-age=31536000`
- [ ] 🟠 `Server` header suppressed or genericized — doesn't reveal "uvicorn" or Python version
- [ ] 🟠 `X-Content-Type-Options: nosniff` present
- [ ] 🟠 `Referrer-Policy: strict-origin-when-cross-origin` present
- [ ] 🟠 `Permissions-Policy` explicitly denies `geolocation` (ArogyaMitra doesn't need it) and scopes `camera`/`microphone` to `self` only
- [ ] 🟡 HTTPS enforced at the reverse proxy / hosting layer — HTTP requests redirect to HTTPS (never served over plain HTTP in production)
- [ ] 🟡 TLS certificate auto-renews (Let's Encrypt via Caddy, or hosting platform's managed TLS)

---

## 10. Dependency Audit & Updates

### 10.1 Implementation Guide

```
Python:
  pip install pip-audit
  pip-audit -r requirements.txt
  → Lists every known CVE in your installed package versions.
  Fix: pin to the patched version in requirements.txt, re-run pip-audit until clean.

  Also run: pip list --outdated
  → Review each outdated package — update patch/minor versions freely,
    test thoroughly before major version bumps (breaking changes).

Node/npm:
  npm audit
  → Lists vulnerabilities in frontend dependencies.
  npm audit fix
  → Auto-fixes what it safely can.
  For anything npm audit can't auto-fix: manually review the advisory,
  decide if the vulnerable code path is actually reachable in your app,
  update the dependency or replace it.

Ongoing (not one-time):
  Add a scheduled check — GitHub Dependabot (free, built into GitHub) opens
  automatic PRs when a dependency has a security patch available. Enable it
  on the repo: Settings → Security → Dependabot → enable both "Dependabot alerts"
  and "Dependabot security updates".

Remove unused dependencies:
  Python: pip install pipreqs → pipreqs --force . → compare generated
  requirements.txt against your actual one, remove anything not truly imported
  npm: npx depcheck → lists unused packages in package.json, remove them

  Every unused dependency is attack surface with zero benefit — if you installed
  a library for OCR exploration early on and switched approaches, remove it.
```

### 10.2 Checklist

- [ ] 🔴 `pip-audit` run against `requirements.txt` — zero HIGH or CRITICAL severity findings remain unresolved
- [ ] 🔴 `npm audit` run against frontend — zero HIGH or CRITICAL severity findings remain unresolved
- [ ] 🟠 Every package in `requirements.txt` is pinned to an exact version (`==`), not a loose range (`>=`) — prevents an unreviewed future update from silently introducing a vulnerability
- [ ] 🟠 Every package in `package.json` has its version locked via `package-lock.json` committed to the repo
- [ ] 🟠 `pipreqs`/`depcheck` run to identify unused dependencies — any package not actually imported anywhere is removed
- [ ] 🟠 GitHub Dependabot alerts enabled on the repository for ongoing monitoring
- [ ] 🟡 No dependency is more than 2 major versions behind latest without a documented reason (e.g. "pinned due to breaking API change — tracked in issue #X")
- [ ] 🟡 `easyocr`, `tesseract`, `chromadb` (the heaviest dependencies) specifically checked for known CVEs given their C-library bindings

---

## 11. Exposed File Check

### 11.1 Implementation Guide

```
Confirm nothing sensitive is servable as a static file or accessible via a
predictable URL path.

Checks to run:
1. Confirm the FastAPI app does NOT mount a StaticFiles directory pointing at:
   - /backend/data/ (contains encrypted records + SQLite DB)
   - /backend/ml/models/ (contains trained .pkl files — not secret, but shouldn't
     be publicly downloadable either)
   - The project root (would expose .env, .git, source code)

2. If serving the React build, StaticFiles should ONLY mount /frontend/dist/
   — nothing else.

3. .git directory must never be deployed to a public web root. If using a
   platform that deploys the whole repo, add a .dockerignore / deployment
   exclusion for .git, .env, /backend/data/, /logs/

4. Common exposed-file scan — manually verify these return 404 on your deployed app:
   https://yourdomain.com/.env
   https://yourdomain.com/.git/config
   https://yourdomain.com/backend/data/arogya_mitra.db
   https://yourdomain.com/requirements.txt
   https://yourdomain.com/.env.example  (this one CAN be 200 — it's meant to be
     informational and contains no real secrets, but confirm it truly has only
     placeholders)
   https://yourdomain.com/logs/arogya_2026-01-01.log
   https://yourdomain.com/backend/config.py

5. robots.txt should disallow crawling of any admin or API paths you don't
   want indexed:
   User-agent: *
   Disallow: /api/admin/
   Disallow: /doctor-view/
```

### 11.2 Checklist

- [ ] 🔴 `GET /.env` returns `404` on the deployed app — test this directly
- [ ] 🔴 `GET /.git/config` returns `404` — test this directly
- [ ] 🔴 `GET /backend/data/arogya_mitra.db` (or equivalent DB path) returns `404`
- [ ] 🔴 `StaticFiles` mount in `main.py` points ONLY to the frontend build directory — confirm no mount covers `/backend/` or project root
- [ ] 🔴 `.dockerignore` (or platform deployment exclusions) excludes `.env`, `.git/`, `/backend/data/`, `/logs/`, `__pycache__/`
- [ ] 🟠 `GET /requirements.txt` and `GET /package.json` return `404` (even though these aren't deeply secret, they reveal your exact dependency versions to an attacker planning a version-specific exploit)
- [ ] 🟠 `robots.txt` disallows crawling of `/api/admin/` and `/doctor-view/`
- [ ] 🟡 Directory listing is disabled on the web server / hosting platform (no auto-generated file index for any directory)

---

## 12. Database Security

### 12.1 Implementation Guide

```
SQLite (Phase 1):
  - DB file (arogya_mitra.db) stored OUTSIDE the web-servable directory —
    never in /frontend/public/ or anywhere StaticFiles could reach
  - File permissions: chmod 600 arogya_mitra.db (owner read/write only)
  - WAL mode enabled (already in your database.py) — also improves crash safety
  - Regular backups: a cron job copying the DB file to encrypted cloud storage
    daily, retained 30 days

PostgreSQL (Phase 2+):
  - Connection uses TLS: ?sslmode=require in the connection string
  - DB user has LEAST PRIVILEGE — the app's DB role should NOT be a superuser;
    create a dedicated role with only SELECT/INSERT/UPDATE/DELETE on the
    arogya_mitra database, nothing else (no CREATE DATABASE, no role management)
  - Connection pooling via SQLAlchemy's QueuePool (already specified) prevents
    connection exhaustion attacks
  - Automated daily backups via your hosting provider (Supabase/Railway/Render
    all offer this) with point-in-time recovery if available
  - Database NEVER directly internet-accessible — only your backend's IP/network
    can reach it (use the hosting platform's private networking, not a public
    DB endpoint with just a password)

Both:
  - Sensitive columns (hashed_password, refresh_jti_hash, encryption-related
    fields) are never returned in any SELECT that feeds an API response —
    enforce this at the Pydantic response-schema layer, which acts as an
    allowlist (only fields explicitly in the schema are serialized, everything
    else is dropped automatically — this is a built-in safety net, confirm
    you're actually using response_model= on every route, not returning raw
    ORM objects or dicts)
  - SQL injection: already prevented via ORM-only queries (Section 6)
```

### 12.2 Checklist

- [ ] 🔴 Database file/connection is NOT reachable via any public URL
- [ ] 🔴 Every FastAPI route that returns user data specifies `response_model=` with a Pydantic schema — confirm no route returns a raw SQLAlchemy object or unfiltered dict
- [ ] 🔴 `hashed_password` and `refresh_jti_hash` are absent from every response schema — grep all schema files to confirm these field names don't appear in any `*ResponseSchema`
- [ ] 🔴 (Phase 2+ Postgres) DB connection string uses `sslmode=require`
- [ ] 🔴 (Phase 2+ Postgres) The app's DB role has least-privilege grants — not a superuser/admin role
- [ ] 🟠 (Phase 1 SQLite) DB file permissions set to `600`
- [ ] 🟠 Automated backups configured and tested — actually restore a backup once to confirm it works, don't assume
- [ ] 🟠 Backup files are themselves encrypted at rest (not plain `.db` files sitting in open cloud storage)
- [ ] 🟡 (Phase 2+) Database audit logging enabled at the hosting-platform level for anomaly detection

---

## 13. Password Hashing Verification

### 13.1 Implementation Guide

```
This duplicates part of Section 4 deliberately — password hashing is critical
enough to double-check in isolation as its own audit pass.

Confirm the exact configuration:

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

NEVER:
  - MD5, SHA1, SHA256 alone (fast hashes — brute-forceable at billions/sec on GPUs)
  - A hand-rolled hashing scheme
  - Storing even a hint, partial password, or password history
  - Logging the plaintext password at any point, even in a DEBUG log line
    during development (easy to forget to remove before shipping)

Test it directly:
  Register a test user with password "TestPassword123"
  Query the DB directly: SELECT hashed_password FROM users WHERE email = '...'
  Confirm the value:
    - Starts with $2b$ (bcrypt identifier)
    - Is ~60 characters long
    - Is NOT "TestPassword123" or any recognizable transformation of it
```

### 13.2 Checklist

- [ ] 🔴 `bcrypt` is the hashing algorithm — confirm via `passlib.context.CryptContext(schemes=["bcrypt"])`
- [ ] 🔴 Cost factor (rounds) is `12` or higher
- [ ] 🔴 Direct DB query confirms stored `hashed_password` values start with `$2b$` and are ~60 chars
- [ ] 🔴 Zero occurrences of plaintext password in any log file — grep `/logs/*.log` for a test password used during manual testing
- [ ] 🟠 Password change/reset flow re-hashes with the current `CryptContext` config (not reusing an old hash)
- [ ] 🟡 `passlib`'s `deprecated="auto"` setting confirmed — this allows future algorithm migration (e.g. to Argon2) without breaking existing hashes

---

## 14. Git History Secret Scan

### 14.1 Implementation Guide

```
Even if .env is correctly gitignored NOW, a secret may have been committed
earlier in the project's history before the .gitignore was added — and
`git log` preserves that forever unless the history is rewritten.

Step 1 — Scan the full history:
  Install trufflehog (most thorough open-source option):
    pip install truffleHog3
    OR
    brew install trufflehog   (macOS)

  Run against the full git history:
    trufflehog3 --no-entropy --repo_path . --branch main

  Alternative: gitleaks (also excellent, faster)
    brew install gitleaks
    gitleaks detect --source . --verbose

Step 2 — If a secret IS found in history:
  a) IMMEDIATELY rotate that secret — assume it is compromised the moment it's
     found, regardless of whether the repo was ever public. A leaked key in
     private-repo history is still a risk (contributor machines, CI logs,
     accidental repo visibility changes, etc.)
  b) Remove it from history using git-filter-repo (NOT the deprecated
     git filter-branch):
       pip install git-filter-repo
       git filter-repo --path .env --invert-paths
     This rewrites history to remove the file entirely from every commit.
  c) Force-push the cleaned history: git push origin --force --all
  d) Everyone with a clone must re-clone fresh (old clones still have the
     secret in their local history)
  e) If the repo was ever public or shared with anyone outside your direct
     control, treat the secret as permanently compromised even after removal
     — rotation (step a) is what actually protects you, not the history cleanup

Step 3 — Prevent recurrence:
  Install a pre-commit hook that blocks commits containing secret patterns:
    pip install pre-commit
    Create .pre-commit-config.yaml:
      repos:
        - repo: https://github.com/gitleaks/gitleaks
          rev: v8.18.0
          hooks:
            - id: gitleaks
    pre-commit install
  Now every commit is scanned BEFORE it's created — secrets never enter history again.
```

### 14.2 Checklist

- [ ] 🔴 Full git history scanned with `trufflehog3` or `gitleaks` — command actually run, not assumed clean
- [ ] 🔴 If any secret found in history: that exact secret has been rotated (new `GROQ_API_KEY`, new `SECRET_KEY`, etc. generated and deployed)
- [ ] 🔴 If any secret found in history: history rewritten with `git-filter-repo` and force-pushed
- [ ] 🔴 `.env` file itself confirmed absent from `git log --all --full-history -- .env` (empty output)
- [ ] 🟠 Pre-commit hook (`gitleaks` via `pre-commit`) installed and active to prevent future secret commits
- [ ] 🟠 Any collaborator who cloned the repo before history-rewriting has re-cloned fresh
- [ ] 🟡 Repository visibility (public/private) reviewed — confirm it's set to the intended visibility on GitHub/GitLab
- [ ] 🟡 Check for secrets accidentally left in commit messages, PR descriptions, or issue comments — these are NOT removed by `git-filter-repo` and need manual review/deletion via the platform's UI

---

## 15. CORS & Network-Level Hardening

### 15.1 Implementation Guide

```
Already specified in PRODUCTION_BACKEND.md Section 3.3 — audit confirmation:

CORS_ORIGINS in production = EXACTLY your frontend domain(s), nothing else:
  ["https://arogyamitra.app"]
  NOT: ["*"], NOT including any localhost entry, NOT including a staging
  domain unless staging genuinely needs it.

TrustedHostMiddleware — add this if not already present, prevents Host header
injection attacks:
  app.add_middleware(TrustedHostMiddleware, allowed_hosts=["arogyamitra.app", "*.arogyamitra.app"])

Reverse proxy (nginx/Caddy) in front of uvicorn — don't expose uvicorn directly
to the internet:
  - Terminates TLS
  - Adds an additional layer of request filtering
  - Can rate-limit at the proxy level before requests even reach FastAPI
```

### 15.2 Checklist

- [ ] 🔴 `CORS_ORIGINS` in production contains only your actual frontend domain(s) — zero wildcards, zero localhost entries
- [ ] 🔴 `TrustedHostMiddleware` configured with your exact production domain(s)
- [ ] 🟠 uvicorn is not directly internet-facing — a reverse proxy (nginx/Caddy) or the hosting platform's edge handles incoming traffic
- [ ] 🟠 TLS/HTTPS is enforced end-to-end, including between the reverse proxy and uvicorn if they're on different hosts
- [ ] 🟡 WebSocket connections (if used for real-time features later) also validate Origin header

---

## 16. Final Full Audit Sign-Off

Run through every section above in order. Do not mark the project launch-ready until every 🔴 item across all 15 sections is checked. 🟠 items should be checked before public launch; 🟡 items are strong hardening to complete within the first month post-launch.

| Section | 🔴 Critical | 🟠 High | 🟡 Medium | Total |
|---------|------------|---------|-----------|-------|
| 1. Secrets & API Keys | 6 | 4 | 2 | 12 |
| 2. Environment Variables | 5 | 3 | 1 | 9 |
| 3. Admin Routes | 4 | 2 | 2 | 8 |
| 4. Authentication | 6 | 3 | 1 | 10 |
| 5. Authorization (IDOR) | 6 | 2 | 1 | 9 |
| 6. Form Sanitization | 5 | 3 | 1 | 9 |
| 7. XSS & CSRF | 2 | 2 | 1 | 5 |
| 8. Rate Limiting | 3 | 4 | 2 | 9 |
| 9. Security Headers | 5 | 4 | 2 | 11 |
| 10. Dependency Audit | 2 | 4 | 2 | 8 |
| 11. Exposed Files | 4 | 2 | 1 | 7 |
| 12. Database Security | 4 | 3 | 1 | 8 |
| 13. Password Hashing | 4 | 1 | 1 | 6 |
| 14. Git History | 4 | 2 | 2 | 8 |
| 15. CORS & Network | 2 | 2 | 1 | 5 |
| **TOTAL** | **62** | **41** | **21** | **124** |

**Launch gate: all 62 🔴 items checked. No exceptions, no "we'll fix it after launch" on any 🔴 item.**

---

## 17. One-Time Setup Commands Reference

```bash
# Generate a strong SECRET_KEY
openssl rand -hex 32

# Generate a valid ENCRYPTION_KEY (32 bytes, base64)
python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"

# Scan Python dependencies for known CVEs
pip install pip-audit && pip-audit -r requirements.txt

# Scan npm dependencies for known CVEs
npm audit

# Find unused Python dependencies
pip install pipreqs && pipreqs --force .

# Find unused npm dependencies
npx depcheck

# Scan full git history for leaked secrets
pip install truffleHog3 && trufflehog3 --no-entropy --repo_path . --branch main

# Confirm .env was never committed
git log --all --full-history -- .env

# Set up pre-commit secret scanning (prevents future leaks)
pip install pre-commit
pre-commit install

# Rewrite git history if a secret WAS found (last resort, rotates key first!)
pip install git-filter-repo
git filter-repo --path .env --invert-paths
git push origin --force --all

# Restrict DB file permissions (SQLite, Phase 1)
chmod 600 backend/data/arogya_mitra.db
chmod 600 .env
```

---

*End of SECURITY_AUDIT.md*
*ArogyaMitra AI — Full Security Audit & Hardening Guide*
