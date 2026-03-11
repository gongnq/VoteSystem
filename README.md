# 2026 Asia Demo Crawl - Voting System

A mobile-first voting system for live demo crawl events. Judges scan QR codes at each booth and vote by tapping category-specific options on their phones/tablets.

## How It Works

### Judge Flow

```
Login --> Scan QR Code at Booth --> Select Vote Options --> Submit --> Next Booth
```

1. **Login** - Judge selects their name from the dropdown
2. **Scan QR** - Tap the large "Scan QR Code" button, point camera at the booth's QR code
3. **Vote** - The voting panel opens with 3 large option buttons. Tap one or more to select (turns green). Tap again to deselect.
4. **Submit** - Tap "Submit Vote" to confirm
5. **Repeat** - Scan the next booth's QR code (or tap a group card manually)

### Vote Categories & Options

| Category | Full Name | Options |
|----------|-----------|---------|
| **NTI** | New Innovation Pipeline | Product Concept, Accelerator, Think Big |
| **NPI** | New Product Concepts | PRFAQ (Product Maker), PRE-ORDER, Customer Delight |
| **AI** | AI & Automation | PRFAQ (Product Maker), PRE-ORDER, Customer Delight |

Judges can **select multiple options** per group. Each selected option adds +1 to that group's tally.

### Admin Dashboard

Access via the "Admin Dashboard" button on the login page (PIN required).

- **Results by category** - Tables showing vote counts per option for each group
- **Judge completion** - Grid showing how many groups each judge has voted on
- **QR Codes tab** - Generate and print QR codes for all booths

## Groups (11 total)

| # | Group | Category |
|---|-------|----------|
| 1 | An Inner Spider Speaker Construction | NTI |
| 2 | Edge to Edge Display Cover Lens | NTI |
| 3 | BOBArtender - AI-Powered Bubble Tea | NTI |
| 4 | Echo Frames Reimagined | NPI |
| 5 | Alexa UI Plus - Fire TV Smart Scene | NPI |
| 6 | Pulse ID | NPI |
| 7 | Stratos | AI |
| 8 | Multi-Modal Competitive Intelligence | AI |
| 9 | Hercules: Cloud-based AI/ML Platform | AI |
| 10 | Manufacturing Smart Assistant | AI |
| 11 | Intelligent Quality: AI Battery Mfg | AI |

## Tech Stack

- **Backend**: Python / Flask / SQLite
- **Frontend**: Single-page HTML with vanilla JS (no framework)
- **QR Scanning**: [html5-qrcode](https://github.com/mebjas/html5-qrcode) (camera-based, works on mobile)
- **QR Generation**: [qrcodejs](https://github.com/davidshimjs/qrcodejs) (admin prints QR codes for booths)
- **Hosting**: Render (free tier) / AWS App Runner

## Setup

### Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

### Deploy to Render

Push to GitHub. Render auto-deploys from `render.yaml`:

```yaml
services:
  - type: web
    name: democrawl-vote
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: ADMIN_PIN
        value: "2026"
```

### QR Code Setup

1. Login as Admin
2. Go to the "QR Codes" tab
3. Click "Print QR Codes"
4. Cut and place each QR code at the corresponding booth

Each QR code contains the group ID (e.g. `NPI-1`). When scanned, the app opens the voting panel for that group.

## Configuration

All config is at the top of `app.py`:

| Setting | Location | Description |
|---------|----------|-------------|
| `JUDGES` | Line ~21 | List of judge names |
| `GROUPS` | Line ~26 | (id, display_name, category) tuples |
| `VOTE_OPTIONS_BY_CATEGORY` | Line ~44 | Vote button labels per category |
| `CATEGORY_DESCRIPTIONS` | Line ~62 | Description text shown on vote page |
| `ADMIN_PIN` | Line ~70 | Admin dashboard PIN (env var or default) |

## Key Features

- **QR Code Scanning** - Fast booth selection via phone camera
- **Multi-Select Voting** - Judges can pick multiple options per group
- **Session Locking** - One device per judge, prevents duplicate logins
- **Real-Time Admin** - Auto-refreshing results dashboard (5s interval)
- **PWA Support** - Installable on mobile home screen
- **Responsive** - Optimized for phone, tablet portrait, and tablet landscape
- **Printable QR Codes** - Generate all booth QR codes from admin panel
- **Zero Dependencies** - No npm, no build step. Just Flask + SQLite
