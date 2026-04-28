# Company Address Scraper — Frontend

Next.js 14+ frontend for the company address scraping tool.

## Quick Start

### Installation

```bash
cd frontend
npm install
```

### Configuration

```bash
cp .env.local.example .env.local
# Edit .env.local with your API URL and AdSense ID (optional)
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Upload page
│   ├── processing/page.tsx   # Progress polling
│   ├── preview/page.tsx      # Results preview
│   ├── download/page.tsx     # Interstitial + download
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/
│   ├── AdPlaceholder.tsx     # Ad placeholder
│   ├── FileUpload.tsx        # Drag-drop upload
│   ├── ProgressBar.tsx       # Progress indicator
│   ├── Spinner.tsx           # Loading spinner
│   └── StatusBadge.tsx       # Status display
├── lib/
│   ├── api.ts                # API client
│   └── utils.ts              # Utility functions
├── package.json
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

## Features

- ✓ 4-page multi-step flow (Upload → Processing → Preview → Download)
- ✓ Drag-and-drop Excel file upload
- ✓ Real-time progress polling
- ✓ Results preview with status indicators
- ✓ 10-second countdown interstitial ad
- ✓ Excel file download
- ✓ Google AdSense integration
- ✓ Responsive design (mobile + desktop)
- ✓ Error handling and validation

## API Integration

The frontend communicates with the backend FastAPI server:

```
Backend: http://localhost:8000
Frontend: http://localhost:3000
```

**Endpoints:**

- `POST /api/jobs/upload` — Create job from Excel file
- `GET /api/jobs/{job_id}` — Poll job status
- `GET /api/jobs/{job_id}/download` — Download result Excel

See `lib/api.ts` for the API client.

## Styling

Uses Tailwind CSS for styling. Global styles are in `app/globals.css`.

### Colors

- Primary: `#2563eb` (Blue)
- Success: `#10b981` (Green)
- Warning: `#f59e0b` (Amber)
- Danger: `#ef4444` (Red)

## Environment Variables

Required:

- `NEXT_PUBLIC_API_URL` — Backend API URL (default: http://localhost:8000)

Optional:

- `NEXT_PUBLIC_ADSENSE_ID` — Google AdSense publisher ID

## Development Tips

- Use `npm run dev` to run with hot reload
- Check browser console for API errors
- Ad placeholders show development notices when ADSENSE_ID is not set
- All pages support SSR (server-side rendering)

## Building for Production

```bash
npm run build    # Creates optimized production build
npm start        # Runs production server
npm run lint     # Run ESLint
```
