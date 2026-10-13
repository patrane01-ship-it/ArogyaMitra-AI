# ArogyaMitra AI — Phase 2 & Phase 3 Validation Report

Date: 2026-10-13  
Scope: Codebase audit vs `specs/FEATURES_PHASE2.md`, `specs/PHASE2_CHECKLIST.md`, `specs/FEATURES_PHASE3.md`, `specs/MASTER_STATUS_CHECKLIST.md`

---

## 1) Execution & Build/Test Results

### What was executed
- Backend syntax compile: `python -m compileall backend main.py` ✅
- Frontend dependency install + build: `npm install`, `npm run build` ✅ (with large chunk warning)
- Python dependency install from `requirements.txt` ❌
- Backend runtime smoke (`/health` via TestClient) ❌
- Prompt-injection/guardrail function smoke checks ✅

### Key failures observed
1. `requirements.txt` contains invalid package entry:
   - `itertools-more==0.4.0` (no matching distribution)
   - This blocks full clean environment setup.
2. Backend startup smoke still fails after partial installs because required deps are missing (e.g., `langgraph`), so full app boot was not validated end-to-end in this run.
3. No backend test suite is wired in current environment (`pytest` not configured in repo/tooling by default).

---

## 2) Phase 2 Status (Against Spec)

## High-level status: **PARTIAL**

### Confirmed implemented areas
- Auth stack exists (`/api/auth/*`, JWT auth service, password hashing).
- ML/anomaly/drug code paths exist in backend.
- File-upload encryption and basic upload guardrails are present.
- User-scoped repository access pattern exists for key record access paths (IDOR defense pattern visible in repositories).

### Gaps / mismatches vs Phase 2 spec
1. **Endpoint contract mismatch from spec**
   - Spec expects admin model endpoints like `/api/admin/models/*`.
   - Code exposes `/api/ml/*` paths instead.
   - Anomaly and drug endpoints also diverge from expected checklist contracts.
2. **Auth UI/Backend flow mismatch**
   - Backend register returns message+user (no access token).
   - Frontend `register()` flow assumes `access_token` and sets auth state immediately.
3. **Required rate limiting for auth endpoints is not implemented as specced**
   - `slowapi` is listed in deps but no route-level limiter usage found for `/api/auth/login` or `/api/auth/register`.
4. **Mobile Phase 2 requirements are incomplete**
   - Checklist items like BottomNav, camera capture flow, pull-to-refresh, and swipeable reminder behavior are not fully evident in current frontend implementation.
5. **.gitignore hardening gaps**
   - No explicit ignore for model `.pkl` files and drug DB CSV as required by Phase 2 security/code-quality checklist.

---

## 3) Injection Attack / Guardrail Handling

## Current status: **PARTIAL (good base, incomplete coverage)**

### What is working
- `backend/core/prompt_guard.py` includes prompt-injection pattern detection and blocking (`PromptInjectionDetectedError`).
- `backend/core/guardrails.py` applies output safety rules (redaction/blocking).
- Smoke checks confirmed:
  - injection-like prompt content is blocked,
  - PII patterns are redacted,
  - instruction-echo output can be blocked.

### Red-flag gaps
1. **Prompt sanitization is not consistently applied before all Groq calls**
   - Some paths sanitize via `sanitize_for_prompt`, others use general `sanitize_string` only.
2. **Guardrail application is not uniformly enforced on all LLM outputs**
   - Several LLM integrations need a consistent mandatory pre/post pattern across services.
3. **Upload guardrails are partial**
   - Basic magic-byte and size checks exist, but checklist-level validations like strict PDF structure/image-dimension guardrails are not fully covered.

---

## 4) Phase 3 Status (Against Spec)

## High-level status: **PARTIAL / IN-PROGRESS**

### Implemented foundation
- Phase 3 models/services/routers are present for family, prediction, ABDM, wearables, subscription, doctor access, API keys, WhatsApp, and voice modules.

### Structural gaps
1. **Feature exposure gap**
   - `voice_router.py` and `whatsapp_router.py` exist but are not mounted in `main.py`; those APIs are effectively inaccessible.
2. **Mock/deferred integrations remain**
   - ABDM uses mock adapter flow.
   - Wearable support is partial (Fitbit path plus deferred adapters).
   - Some external-provider flows are still placeholder-level for production usage.
3. **Production readiness not met**
   - Multiple Phase 3 modules appear development-stage rather than launch-ready (expected for in-progress phase, but important for planning claims).

---

## 5) Is codebase/structure broken?

## Verdict: **Not fully broken, but not release-stable for full Phase 2/3 claims.**

- Core code organization is present and fairly modular.
- However, there are **critical readiness blockers** (dependency setup break, contract mismatches, missing route wiring, incomplete security controls).
- Current implementation should be treated as **partially working** with significant red flags before production or “spec-complete” declaration.

---

## 6) Top Priority Red Flags (Immediate)

1. **Dependency/install blocker in `requirements.txt`** (`itertools-more==0.4.0`) breaks clean setup and CI reproducibility.
2. **Auth rate limiting missing on `/api/auth/login` and `/api/auth/register`** (spec/security mismatch).
3. **Phase 2 API contract drift** (ML/anomaly/drug endpoints differ from spec/checklist).
4. **Frontend/backend auth registration contract mismatch** (register flow likely breaks seamless onboarding).
5. **Phase 3 routers not mounted (`voice`, `whatsapp`)** causing dead/inaccessible implemented code.
6. **Prompt-injection/guardrail enforcement inconsistent across all LLM call sites**.
7. **Missing `.gitignore` protections for model/data artifacts required by checklist**.

---

## 7) Practical Completion View

- **Phase 2:** Implemented in large parts, but not checklist-complete due to endpoint/spec mismatches, missing rate limits, and UI/security gaps.
- **Phase 3:** Significant scaffolding and multiple working modules exist, but still in partial/integration stage; not fully productionized.

---

## 8) Recommended Next Fix Order

1. Fix dependency manifest and ensure clean environment bootstrap works end-to-end.
2. Implement/verify auth rate limiting exactly as spec.
3. Reconcile API contracts with Phase 2 spec (or update specs and clients consistently).
4. Fix auth register flow mismatch between frontend and backend.
5. Mount missing routers and run full route smoke suite.
6. Enforce mandatory prompt sanitization + output guardrails for every LLM pathway.
7. Close remaining checklist security hygiene gaps (`.gitignore`, upload guardrails, full E2E validation).

