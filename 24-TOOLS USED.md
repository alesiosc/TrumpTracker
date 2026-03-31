# TrumpTracker Tools and Libraries

**Last Updated: 2026-03-31 19:30:00**

> **Update (2026-03-31 19:30:00):** Major tools update - Cloudflare bypass implementation
> - **ADDED:** DrissionPage (4.1.0.0b14) - Persistent browser control via CDP
> - **ADDED:** curl_cffi (0.13.0) - TLS fingerprint matching for API calls
> - **REMOVED:** Playwright, scrapling, camoufox, FlareSolverr (no longer needed)
> - **REMOVED:** torch, scipy, matplotlib, pandas, numpy (unused dependencies)
> - **Implementation:** Persistent browser opens once, stays open all week
> - **Result:** EXE size reduced from 712 MB to 38.4 MB

---

## Current Core Technologies (2026-03-31)

### Primary Libraries
- **DrissionPage** (4.1.0.0b14) - Chrome browser control via Chrome DevTools Protocol (CDP)
  - Persistent browser sessions that stay open indefinitely
  - Cookie extraction from live browser
  - Port 9223 configuration to avoid conflicts
  - Real Chrome browser (not detectable automation)
  
- **curl_cffi** (0.13.0) - HTTP client with TLS fingerprint impersonation
  - Chrome TLS fingerprint matching for API calls
  - Works with cookies extracted from DrissionPage browser
  - Bypasses Cloudflare TLS fingerprint detection
  
- **python-dotenv** (1.0.0+) - Environment variable management from .env files
- **requests** (2.32.0) - Standard HTTP client for non-Cloudflare endpoints
- **truthbrush** - Truth Social API wrapper (primary data source when not blocked)

### Development Tools
- **PyInstaller** (6.15.0) - Standalone executable creation for Windows
- **pip** (25.3) - Python package management
- **Git** - Version control system

### External Services
- **Truth Social API** - Primary method for post data access
- **Discord Webhooks** - Notification delivery system

## Implementation Details

### Cloudflare Bypass (tracker.py)
**Current Implementation (2026-03-31):**
- **DrissionPage** opens real Chrome browser once at startup
- Browser navigates to Truth Social and waits 15s for Cloudflare
- Cookies extracted from browser: `cf_clearance`, `__cflb`, `__cf_bm`, `_cfuvid`, `CookieScriptConsent`
- **curl_cffi** uses extracted cookies with Chrome TLS fingerprint to hit API
- Cookies cached and reused every 2-minute poll cycle
- Auto-refresh on 403 errors from still-open browser
- Browser stays open until exe closes (persistent session)

**Port Configuration:**
- Uses port 9223 (not default 9222) to avoid conflicts with other DrissionPage programs

**Previous Implementations (Deprecated):**
- ~~Playwright with Chromium~~ - Blocked by Cloudflare
- ~~Scrapling StealthyFetcher/camoufox~~ - Blocked by Cloudflare "managed" challenge
- ~~FlareSolverr~~ - Worked but opened/closed browser every cycle (wasteful)

### API Integration (tracker.py)
- Two-tier fallback: Truthbrush API → DrissionPage + curl_cffi
- RESTful API calls to Truth Social endpoints
- Error handling for HTTP 403 and Cloudflare blocks
- Automatic fallback to browser method when API blocked

### Build Tools
- PyInstaller for creating standalone Windows executables
- Custom icon embedding (trump_icon.ico at multiple sizes)
- Dependency exclusion for unused packages (torch, scipy, matplotlib, pandas, numpy)
- Console application packaging
- Hidden imports: DrissionPage, curl_cffi

## Version Information
- Python: 3.13.3
- DrissionPage: 4.1.0.0b14
- curl_cffi: 0.13.0
- PyInstaller: 6.15.0
- Requests: 2.32.0
- Chrome: 145.x (system installation)

## Platform Support
- **Primary:** Windows 10/11 (EXE and Python versions)
- **Secondary:** Cross-platform Python (macOS, Linux via portable package)
- **Browser:** Real Chrome via DrissionPage CDP (all platforms)

## Development Environment
- VS Code with Python extensions
- Git for version control
- Windows PowerShell/Command Prompt for execution
- Environment variable configuration via .env files

## Removed Dependencies (2026-03-31)
The following were removed to reduce exe size and eliminate unused code:
- Playwright (replaced by DrissionPage)
- scrapling (replaced by DrissionPage)
- camoufox (replaced by DrissionPage)
- FlareSolverr (replaced by DrissionPage)
- torch (unused ML library)
- scipy (unused scientific computing)
- matplotlib (unused plotting)
- pandas (unused data analysis)
- numpy (unused numerical computing)

This documentation maintains a complete record of all tools, libraries, and technical implementations used in the TrumpTracker project.

---

## Previous Updates

### Core Technologies

## Python Libraries
- **playwright** (1.40.0+) - Browser automation for web scraping fallback
- **python-dotenv** (1.0.0+) - Environment variable management from .env files
- **requests** (2.31.0+) - HTTP client for API calls to Truthbrush
- **beautifulsoup4** (4.12.0+) - HTML parsing utilities
- **lxml** (4.9.0+) - XML/HTML parser for BeautifulSoup

### Development Tools
- **PyInstaller** (6.0.0+) - Standalone executable creation for Windows
- **pip** - Python package management
- **Git** - Version control system

### External Services
- **Truthbrush API** - Primary method for Truth Social data access
- **Discord Webhooks** - Notification delivery system
- **OpenRouter API** - AI analysis service (removed from current implementation)

## Implementation Details

### Browser-Based Scraping (tracker_browser.py, tracker_hybrid.py)
- Playwright with Chromium browser engine
- Anti-detection measures: masked `navigator.webdriver` property
- JavaScript DOM extraction for post content, timestamps, and metadata
- Handles Virtuoso virtual scrollers by collecting posts during scroll operations
- Post deduplication using dictionary-based tracking

### API Integration (tracker.py, tracker_hybrid.py)
- RESTful API calls to Truthbrush service
- Token-based authentication with localStorage extraction
- Fallback mechanisms for API failures (switches to browser mode)
- Error handling for HTTP 403 and rate limiting

### Build Tools
- PyInstaller for creating standalone Windows executables
- Custom icon embedding (trump_icon.ico at multiple sizes)
- Dependency bundling for portable distribution
- Console application packaging with hidden console option

### Testing and Debugging Tools
- Debug scripts for browser state capture (debug_browser.py)
- HTML and screenshot generation for DOM analysis
- API token testing utilities (test_api_token.py)
- Manual login scripts for token extraction (manual_login.py)

## Version Information
- Python: 3.7+ (tested on 3.8-3.11)
- Playwright: 1.40+ (with Chromium browser)
- PyInstaller: 6.0+ (for EXE builds)
- Requests: 2.31+ (for API calls)

## Platform Support
- **Primary:** Windows 10/11 (EXE and Python versions)
- **Secondary:** Cross-platform Python (macOS, Linux via portable package)
- **Browser:** Chromium via Playwright (all platforms)

## Development Environment
- VS Code with Python extensions
- Git for version control
- Windows PowerShell/Command Prompt for execution
- Environment variable configuration via .env files

This documentation maintains a complete record of all tools, libraries, and technical implementations used in the TrumpTracker project.