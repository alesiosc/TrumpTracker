# TrumpTracker - How to Run

**Last Updated: 2026-03-31 19:30:00**

> **Update (2026-03-31 19:30:00):** Cloudflare bypass fixed with persistent browser:
> - **DrissionPage** now used instead of FlareSolverr/Playwright/Scrapling
> - **Browser opens once** at startup and stays open all week
> - **Cookies cached** and reused for API calls (only refreshed on 403)
> - **Port 9223** used to avoid conflicts with other DrissionPage programs
> - **EXE size reduced** from 712 MB to 38.4 MB
> - **No manual intervention** needed - Cloudflare auto-solves or 15s wait

> **Update (2026-03-31 18:55:00):** Project status files updated:
> - Executed continuation update prompt to maintain current documentation
> - Updated change log, project status, and tools documentation files
> - No changes to running instructions or code

> **Update (2026-03-23 13:52:49):** Project status files updated:
> - Executed continuation update prompt to maintain current documentation
> - Updated change log, project status, and tools documentation files
> - No changes to running instructions or code

> **Update (2026-03-23 12:00:00):** Project status files updated:
> - Executed continuation update prompt to maintain current documentation
> - Updated change log, project status, and created new documentation files
> - No changes to running instructions or code

> **Update (2026-02-18):** Retruth (RT) filtering fixed:
> - **Browser-based scrapers now skip retruths** - Checks `aria-label` for `, RT:` pattern
> - **Pinned Truths filtered** - Posts marked as "Pinned Truth" are skipped
> - **Files affected:** `tracker_browser.py`, `tracker_hybrid.py`

> **Update (2026-02-16):** Browser-based fallback implemented:
> - **NEW: `tracker_browser.py`** - Uses Playwright to scrape Truth Social directly
> - **BYPASSES HTTP 403** - Works when truthbrush API fails with authentication errors
> - **REQUIRES:** `pip install playwright` and `playwright install chromium`

> **Update (2025-12-16):** Complete removal of AI analysis:
> - **NO AI ANALYSIS** - Tracker no longer uses OpenRouter or any AI service
> - **NO PINEAPPLE LOGIC** - All valid posts sent immediately without filtering
> - **SIMPLIFIED POSTING** - If post is valid (has text, not reblog), it's sent to Discord and Truth Social
> - **EXE Rebuilt:** New executable at `TrumpTracker.exe` (480,917,618 bytes)

> **Update (2025-12-15):** Fixed critical bug where pineapple posts were not being sent to Discord:
> - **Pineapple Logic Fix:** ALL valid posts are now sent to Discord regardless of AI market impact analysis
> - **Improved Output:** Console now clearly shows market impact vs. pineapple classification
> - **EXE Rebuilt:** New standalone executable at `dist/TrumpTracker.exe` (480,917,962 bytes)

> **Update (2025-12-13):** The tracker now includes:
> - **Initial Post Processing:** Automatically processes and sends the first valid post on startup.
> - **EST Footer:** Discord alerts now show the post time in EST (e.g., `Dec 13, 10:52 EST`).
> - **Intelligent Filtering:** Skips URL-only, media-only, and reblog posts.
> - **Standalone EXE:** Available in `dist/TrumpTracker.exe` (or copy to main folder).

## Updated Running Instructions

The project now has multiple ways to run:

### 🚀 Quick Launch (Recommended)

**Option 1: Double-click `TrumpTracker.exe`** - Standalone executable with Trump icon in taskbar!

**Option 2: Double-click `TrumpTracker.lnk`** - Shortcut that runs the BAT file.

**Option 3:** Run `TrumpTracker.bat` directly from command line.

### 1. Original Development Version (Main Directory)

**Prerequisites:**
- Python 3.7+
- All dependencies installed (`pip install -r requirements.txt`)
- Environment variables configured in `.env` file

**To Run:**
```bash
python tracker.py
```

### 2. Portable Package Version (TrumpTracker_Portable/)

**NEW: Simplified Setup Process**

The portable version offers multiple running options:

#### Option A: Automated Setup (Recommended)
**Windows Users:**
1. Double-click `run.bat`
2. Follow prompts to configure settings if needed

**Mac/Linux Users:**
1. Open terminal in TrumpTracker_Portable directory
2. Run: `./run.sh`
3. Follow prompts to configure settings if needed

#### Option B: Interactive Setup Only
Run the configuration wizard separately:
```bash
python setup_config.py
```

#### Option C: Manual Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and configure
3. Run: `python tracker.py`

## Environment Configuration

Both versions require a `.env` file with the following variables:

```env
TRUTH_USERNAME=your_truth_social_username
TRUTH_PASSWORD=your_truth_social_password
OPENROUTER_API_KEY=your_openrouter_api_key
ENVIRONMENT=TEST  # or PRODUCTION
DISCORD_WEBHOOK_TEST=your_test_webhook_url
DISCORD_WEBHOOK_PROD=your_production_webhook_url
```

## Key Differences Between Versions

### Original Version:
- Direct access to development environment
- Manual dependency management
- Requires manual environment setup

### Portable Version:
- Self-contained with automated setup
- Interactive configuration wizard
- Cross-platform run scripts
- Comprehensive documentation included

## Testing Status

Both versions have been tested and verified to work independently. The portable version can run simultaneously with the original version if needed.

---

**For detailed setup instructions, see README.md in the portable package.**