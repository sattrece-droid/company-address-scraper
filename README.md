# Company Address Scraping — Utility Site

## What It Is

A utility website where users upload an Excel file of company names (with optional zip codes), the system automatically finds each company's website, locates their physical locations page, scrapes all addresses, and returns a new Excel file with structured address data (street, city, state/province, zip, country).

**Example input Excel format:**

| Company Name | Zip Code (optional) | Website (optional) |
|--------------|---------------------|--------------------|
| ServiceMaster | 90210 | |
| Home Depot | | |
| Starbucks | 30301 | starbucks.com |

**Example output:** Company name + full address per location + status (complete/partial/manual_required/etc.) + match confidence

---

## Business Model

**Free ad-supported tool with optional premium tier**

### Free Tier
- Process up to 5–10 companies per request
- Multi-page flow with ads (upload → processing → preview → download)
- Interstitial ads before download (10-second countdown)
- 4+ ad impressions per session
- Daily rate limit per IP (10 companies/day)

### Premium Tier (Optional)
- $5–10/month subscription
- No ads
- Higher limits (500 companies/month)
- Bulk processing
- Priority support

**Target users:** Finance research, sales teams, market researchers, real estate analysts, BD teams, franchise consultants

**Competitive advantage:** Scrapes from source (fresher than ZoomInfo/Apollo), structures unstructured HTML via AI, outputs ready-to-use Excel

---

## Revenue Strategy

### Primary: Ad Revenue
- **Google AdSense** for display ads (RPM: $2–8 for utility sites)
- **Multi-page flow** maximizes impressions per session
- **Interstitial ads** before download (highest revenue)
- Need ~5–20x more pageviews than processing sessions to break even

### Secondary: SEO Content Pages
- Generate public pages: "Company Name Locations — N addresses"
- Rank on Google for "{company} locations" searches
- Passive ad revenue from organic traffic
- Subsidizes the free tool usage

### Tertiary: Premium Subscriptions
- Even 50 premium users at $10/month covers infrastructure
- Reduces reliance on ads alone

**Break-even target:** 10,000 monthly sessions × 4 pageviews = 40,000 impressions = $80–320/month ad revenue (covers infra + API costs for moderate usage)

---

## Architecture

```
Next.js Frontend (multi-page flow for ad impressions)
    ↓
1. Upload page [AD]
    ↓ multipart POST → create job, return job ID
2. Processing page [AD]
    ↓ progress bar, polling for status (30–60s user engagement)
3. Preview page [AD]
    ↓ show first 5 results, verify accuracy
4. Interstitial / Download page [AD]
    ↓ 10-second countdown, then download link

Python Backend (FastAPI on Lightsail $10/month)
    ↓ async job processing
    ↓ parse Excel (openpyxl/pandas)
    ↓ per-company loop:
        → Check cache (SQLite/Redis, 7-day TTL)
        → SerpAPI (find website, geotargeted if zip provided)
        → Firecrawl (scrape homepage)
        → Nova Micro (extract locations page URL)
        → Firecrawl (scrape locations page)
        → DECISION POINT: interactive form detected?
            NO  → Nova Micro parse addresses → Done
            YES → Playwright (fill zip, click search, extract HTML) → Parse
        → Validate zip match (if provided)
        → Assign status code
        → Cache result (7-day TTL)
    ↓ write output Excel
    ↓ store result (7-day retention)
    ↓ update job status → notify frontend

Cloudflare (free tier)
    → Rate limiting (10 companies/day per IP)
    → Bot protection
    → CDN for static assets
```

---

## Workflow (Per Company)

1. **Parse input** — Extract company name + zip + website (if provided) from Excel
2. **Check cache** — Return cached result if available (7-day TTL)
3. **Find official website** — SerpAPI with geotargeting
   - If zip provided: `"{company_name}" {zip_code}` (improves accuracy, disambiguates chains)
   - If website column provided: skip SerpAPI entirely
4. **Crawl homepage** — Firecrawl (rendered HTML with JS)
5. **Find locations page** — Nova Micro: *"Extract the URL for the page listing physical locations"*
   - Fallback: SerpAPI site-scoped search `site:example.com locations OR offices OR "find a location"`
   - If still not found: try Contact/About page for HQ address only
6. **Scrape locations page** — Firecrawl with pagination handling
   - Detect "Next page" links or paginated URLs
   - Crawl all pages under `/locations/` if needed
   - Detect store locator widgets (Yext, Bullseye) and extract API calls
7. **Interactive detection** — Keyword + regex matching on HTML
   - If form/zip input detected AND zip provided → fall back to Playwright
   - If form detected AND no zip → mark `manual_required`
8. **Playwright fallback** (interactive sites only) — Fill zip form, click search, wait for results, extract HTML
9. **Parse addresses** — Nova Micro via Bedrock: *"Extract all addresses, return JSON: [{name, address, city, state, zip, country}]"*
   - Fallback to Claude Haiku 4.5 for messy/unusual HTML
10. **Validate results** — If input zip provided, check if scraped addresses cluster nearby
    - Flag mismatches: "Input zip not found among locations"
11. **Assign status code** — See Edge Case Handling section
12. **Cache result** — Store in SQLite/Redis for 7 days
13. **Assemble** → write output Excel with status + confidence scores

**Processing:** Background job with progress updates (not synchronous HTTP)

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | **Next.js** (routing, SEO, ad optimization) |
| Backend | Python/FastAPI on AWS Lightsail $10/month |
| Excel I/O | openpyxl or pandas |
| Web search | SerpAPI |
| Scraping (default) | Firecrawl SDK (~80% of sites) |
| Scraping (fallback) | Playwright headless Chromium (~20% of sites, interactive) |
| Address parsing | Amazon Nova Micro via Bedrock (default) |
| AI fallback | Claude Haiku 4.5 via Bedrock |
| Cache | SQLite with WAL mode (MVP) → Redis (production) |
| Ads | Google AdSense (Mediavine at 50k sessions/month) |
| Rate limiting / CDN | Cloudflare (free tier) |
| Auth (premium) | Clerk |
| Billing (premium) | Stripe |
| Deployment | Docker + docker-compose on Lightsail |

---

## Project Structure

```
company-address-scraping/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment variables, API keys
│   ├── api/
│   │   ├── routes.py           # Upload, status, download endpoints
│   │   └── models.py           # Pydantic schemas
│   ├── services/
│   │   ├── job_processor.py    # Main orchestration + cost tracking
│   │   ├── search.py           # SerpAPI integration
│   │   ├── scraper.py          # Firecrawl integration
│   │   ├── browser.py          # Playwright integration
│   │   ├── parser.py           # Nova Micro/Bedrock integration
│   │   └── cache.py            # SQLite/Redis cache layer
│   ├── utils/
│   │   ├── excel.py            # openpyxl read/write
│   │   ├── validators.py       # Zip validation, status assignment
│   │   └── detectors.py        # Form/interactive site detection
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Upload page [AD]
│   │   ├── processing/page.tsx # Progress polling [AD]
│   │   ├── preview/page.tsx    # Results preview [AD]
│   │   └── download/page.tsx   # Interstitial + download [AD]
│   ├── components/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

---

## Key Implementation Details

### Form Detection (detectors.py)

```python
import re

def is_interactive_locator(html: str) -> bool:
    keywords = [
        "enter your zip", "enter zip code", "find nearby",
        "search by location", "enter your address", "select your state",
        r'<input.*type="text".*zip', r'<input.*placeholder=".*zip.*code',
        "store locator"
    ]
    html_lower = html.lower()
    return any(re.search(kw, html_lower) for kw in keywords)
```

### Playwright Automation (browser.py)

```python
from playwright.async_api import async_playwright

async def scrape_with_playwright(url: str, zip_code: str) -> str | None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)

            zip_selectors = [
                'input[name*="zip"]', 'input[id*="zip"]',
                'input[placeholder*="zip"]', 'input[type="text"]'
            ]
            for selector in zip_selectors:
                try:
                    await page.fill(selector, zip_code, timeout=2000)
                    break
                except Exception:
                    continue

            submit_selectors = [
                'button[type="submit"]', 'input[type="submit"]',
                'button:has-text("Search")', 'button:has-text("Find")'
            ]
            for selector in submit_selectors:
                try:
                    await page.click(selector, timeout=2000)
                    break
                except Exception:
                    continue

            # Wait for results element rather than fixed sleep
            await page.wait_for_selector(".location-result, .store-result, [class*='result']", timeout=5000)
            return await page.content()
        except Exception as e:
            print(f"Playwright error for {url}: {e}")
            return None
        finally:
            await browser.close()
```

### Cache Layer (cache.py)

```python
# Cache key format
cache_key = f"{company_name.lower().strip()}:{zip_code or ''}"

# SQLite with WAL mode to handle concurrent FastAPI workers
# PRAGMA journal_mode=WAL

# TTL: 7 days
# First request for "Starbucks:90210" → Full pipeline (~$0.03)
# Second request within 7 days → Served from cache ($0.00)
```

### Cost Tracking (job_processor.py)

```python
cost_tracker = {
    "serpapi_calls": 0,
    "firecrawl_calls": 0,
    "playwright_calls": 0,
    "bedrock_input_tokens": 0,
    "bedrock_output_tokens": 0
}
# Increment per service call, log daily
```

---

## Cost Estimates & Cost Control

### Per-Company Costs (verified April 2026)

- **Infrastructure:** $10/month flat (Lightsail 2GB) — new accounts get 3 months free
- **SerpAPI:** ~$0.025/search ($25/month Hobby tier)
- **Firecrawl:** ~$0.005/page ($16/month Hobby tier, 3,000 credits)
- **Playwright:** $0 (self-hosted, ~80MB RAM per browser instance)
- **Nova Micro via Bedrock:** ~$0.0005–0.002/company ($0.035 input / $0.14 output per 1M tokens)
- **Per-company total:** ~$0.03–0.04

**Ad-supported economics:**
- 5 companies/request = ~$0.15–0.20 cost
- Ad revenue per session (4 pageviews): $0.008–0.032
- Loss per session: ~$0.12–0.17 → subsidized by SEO content page traffic

### AI Model Options (address parsing only)

| Model | Input/1M | Output/1M | Notes |
|-------|----------|-----------|-------|
| **Nova Micro** ✅ | $0.035 | $0.14 | Default — text-only, clean HTML |
| Nova Lite | $0.06 | $0.24 | Alternative — structured output |
| Claude Haiku 4.5 | $1.00 | $5.00 | Fallback for messy HTML |

### Cost Control Strategies

1. **Nova Micro by default** (cheapest Bedrock model)
2. **Aggressive caching** — 7-day TTL on all SerpAPI + Firecrawl + parsed results
3. **Rate limiting** — 10 companies/day per IP (Cloudflare)
4. **Batch limits** — max 5–10 companies per free request
5. **1 concurrent Playwright session max** on Lightsail 2GB (queue the rest)
6. **Premium tier** — $5–10/month covers ~150–300 companies of API costs

Sources: [Lightsail](https://aws.amazon.com/lightsail/pricing/) · [SerpAPI](https://serpapi.com/pricing) · [Firecrawl](https://www.firecrawl.dev/pricing) · [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)

---

## Edge Case Handling

### Output Status Codes

| Status | Meaning | Condition |
|--------|---------|-----------|
| `complete` | All locations found and parsed | 5+ locations, zip match if provided |
| `partial` | Some locations found, possible pagination gaps | 1–4 locations scraped |
| `hq_only` | No locations page — HQ from Contact/About page | Single address from Contact page |
| `manual_required` | Interactive locator, no zip provided or extraction failed | Form detected, can't enumerate |
| `blocked` | Anti-scraping protection prevented access | HTTP 403/429 or CAPTCHA |
| `not_found` | No website found or wrong company match | SerpAPI returned no results |
| `zip_mismatch` | Input zip not found among scraped locations | Zip validation failed |

### Nuances Handled

| Nuance | MVP Solution |
|--------|--------------|
| Store locator widgets (Yext, Bullseye) | Firecrawl network capture + Playwright fallback |
| Search-based locators | Playwright fills zip if provided, else `manual_required` |
| Google Maps embeds | Extract place IDs (post-MVP: Places API reverse geocode) |
| Multiple domains / regional sites | Zip-geotargeted SerpAPI search |
| Anti-scraping protections | Firecrawl handles most; mark `blocked` if failed |
| Wrong company match | Optional "website" column skips SerpAPI |
| No locations page | Fall back to Contact/About page, mark `hq_only` |
| Paginated location lists | Crawl all pages under `/locations/` path |

### Optional Input Columns

| Column | Purpose | Impact |
|--------|---------|--------|
| Zip Code | Geotargeting, validation, disambiguation | **Recommended** — major accuracy boost |
| Website | Skip SerpAPI entirely, use provided URL | Saves $0.025/company |
| Country | Force country-specific search | Useful for international companies |

---

## Abuse Prevention

Critical for the free ad-supported model:

- **IP-based rate limiting** — 10 companies/day per IP (Cloudflare)
- **CAPTCHA** on upload (prevents bots)
- **Email verification** for download link (builds email list)
- **Session limits** — max 1 concurrent job per session
- **Cache-first** — serve cached results when possible (reduces API costs)

Without these, one bot could cost $100+/day in API fees.

---

## Testing Plan

### Test Cases

| # | Scenario | Company Example | Expected Status |
|---|----------|----------------|-----------------|
| 1 | Simple site (no forms, paginated list) | ServiceMaster, Home Depot | `complete` |
| 2 | Zip-gated interactive locator | Starbucks, Target | `complete` (via Playwright) |
| 3 | HQ only (no locations page) | Small B2B company | `hq_only` |
| 4 | Ambiguous company name | Generic name | `zip_mismatch` or `not_found` |
| 5 | 50+ location pagination | Large retail chain | `complete` or `partial` |
| 6 | Cache hit (repeat request) | Any previously run | Instant return |
| 7 | Blocked site | Site with Cloudflare protection | `blocked` |

### Local Dev Setup

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload

# Frontend
cd frontend
npm install && npm run dev
```

---

## Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libasound2 libpangocairo-1.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium --with-deps

COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SERPAPI_KEY=${SERPAPI_KEY}
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}
    volumes:
      - ./backend:/app
      - ./data:/app/data  # SQLite + output Excel files

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Lightsail Deployment

```bash
ssh ubuntu@<lightsail-ip>
sudo apt update && sudo apt install docker.io docker-compose -y
git clone <your-repo> && cd company-address-scraping
cp .env.example .env  # fill in API keys
sudo docker-compose up -d
```

---

## MVP Scope (4 Weeks)

### Week 1 — Core Backend Pipeline
- FastAPI app skeleton + Pydantic models
- Excel parsing (openpyxl) with optional zip/website columns
- Pipeline: SerpAPI → Firecrawl → Nova Micro → Excel output
- SQLite cache (WAL mode) with 7-day TTL
- Status code assignment + zip validation
- Cost tracking per job

### Week 2 — Interactive Site Support + Polish
- Form detection (detectors.py)
- Playwright integration (browser.py) — async, 1 concurrent instance
- Pagination handling for large location lists
- Partial result support + error handling
- End-to-end test with real company data (7 test cases above)

### Week 3 — Frontend
- Next.js 4-page flow (upload → processing → preview → download)
- Progress polling (SSE or polling endpoint)
- Google AdSense placeholders on all pages
- Interstitial ad with 10-second countdown before download

### Week 4 — Deploy + Monetize
- Docker deploy to Lightsail
- Cloudflare setup (rate limiting + CDN + bot protection)
- Google AdSense integration (live ads)
- Email verification for download link
- Analytics (conversion funnel: upload → preview → download)
- Premium tier signup flow (Stripe + Clerk, basic)

**Post-MVP:** SEO location pages, bulk CSV support, API access, Google Maps Places integration, Mediavine upgrade at 50k sessions

---

## Processing Alternatives Considered

| Option | Notes |
|--------|-------|
| n8n | Fastest prototype, good for MVP but limited parallelism |
| AWS Lambda + Step Functions | More complex, pay-per-use, no time limits |
| Modal.com | Clean Python DX, built-in parallelism, pay-per-second |
| Inngest | Durable jobs with retries, good Next.js integration |
| Vercel Functions | 60s limit, needs external queue for long batches |
| **Lightsail Python app** ✅ | Chosen: simple, fixed cost, no orchestration overhead |

---

## Status

- [x] Architecture decided (ad-supported + premium hybrid)
- [x] Tech stack chosen (Next.js + FastAPI + Firecrawl + Playwright + Bedrock)
- [x] Hybrid scraping approach validated (Firecrawl default, Playwright fallback)
- [x] Cost model validated
- [x] MVP scope defined (4 weeks)
- [x] Core Backend Pipeline (Week 1) completed:
    - [x] Project structure and scaffolding
    - [x] SQLite Cache with WAL mode and 7-day TTL
    - [x] Excel I/O (openpyxl/pandas) for input parsing and output generation
    - [x] SerpAPI integration for company search and locations page discovery
    - [x] Firecrawl integration for JS-rendered web scraping
    - [x] Amazon Bedrock (Nova Micro) integration for structured address parsing
    - [x] Orchestration logic (JobProcessor) with cost tracking and fallbacks
    - [x] FastAPI REST endpoints (upload, status polling, download)

## Next Steps

1. **Playwright Integration (Week 2)**: Implement `browser.py` for interactive locators.
2. **Pagination Handling**: Support scraping all pages of a location list.
3. **End-to-End Testing**: Test with real company data (Starbucks, Home Depot, etc.).
4. **Next.js Frontend (Week 3)**: Build the 4-page flow with ad placeholders.
5. **Deployment (Week 4)**: Dockerize and deploy to Lightsail.
6. **Google AdSense**: Integrate live ads.
7. **Monetization**: Add premium tier flow with Stripe.
