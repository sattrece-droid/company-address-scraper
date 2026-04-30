# Security Review — Pending Issues

Last reviewed: 2026-04-29

## Status Summary

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | No authentication on API endpoints | 🔴 High | ✅ Fixed — X-API-Key header required |
| 2 | User-supplied filename in temp file path | 🔴 High | ✅ Fixed — Path().name sanitisation |
| 3 | CORS wide open (allow_origins=["*"]) | 🔴 High | ⏳ Pending |
| 4 | No file size limit on backend | 🟡 Medium | ⏳ Pending |
| 5 | No rate limiting on /upload | 🟡 Medium | ⏳ Pending |
| 6 | job_id not validated before use in file path | 🟡 Medium | ✅ Fixed — UUID regex validation |

---

## Pending Issues

### 3. CORS Wide Open
**File:** `backend/main.py:21`
```python
allow_origins=["*"]  # current — allows any website
```
**Risk:** Any malicious website can make cross-origin requests to the API on behalf of a user who has the API key stored in their browser.

**Fix:** Lock to specific origins before deploying publicly.
```python
allow_origins=["http://localhost:3000"]  # dev
# or for production:
allow_origins=["https://your-domain.com"]
```

---

### 4. No File Size Limit on Backend
**File:** `backend/api/routes.py` — `/upload` endpoint

**Risk:** The frontend enforces a 5MB limit in JavaScript, but this is trivially bypassed by posting directly to the API. A large upload could exhaust memory or disk.

**Fix:** Add a size check after reading the file content:
```python
content = await file.read()
if len(content) > 5 * 1024 * 1024:  # 5MB
    raise HTTPException(status_code=413, detail="File exceeds 5MB limit.")
```

---

### 5. No Rate Limiting on /upload
**File:** `backend/api/routes.py` — `/upload` endpoint

**Risk:** The endpoint can be hammered to exhaust paid API quotas (Serper, Firecrawl, Bedrock) with no throttling at any layer. A single bad actor could drain credits quickly.

**Fix:** Add `slowapi` rate limiting:
```bash
pip install slowapi
```
```python
# main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# routes.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

@router.post("/upload")
@limiter.limit("10/hour")
async def upload_file(request: Request, ...):
    ...
```

---

## Notes
- `backend/.env` is gitignored — API keys are not committed
- `LightsailDefaultKey.pem` is untracked — not committed
- SQLite cache uses parameterised queries — no SQL injection risk
- Job files use UUID-only filenames — no user input in output paths
