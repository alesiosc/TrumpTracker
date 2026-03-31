import os
import sys
import re
import html
import time
import requests
from itertools import islice
from dotenv import load_dotenv
from openai import OpenAI
from truthbrush.api import Api

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ─── 1. Load Credentials ───────────────────────────────────────────────────
load_dotenv()

TRUTH_USERNAME = os.getenv("TRUTH_USERNAME")
TRUTH_PASSWORD = os.getenv("TRUTH_PASSWORD")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")  # <--- CHANGED HERE
TRUTH_TOKEN = os.getenv("TRUTH_TOKEN")  # Optional: Pre-authenticated token

# Environment Config
APP_ENV = os.getenv("ENVIRONMENT", "TEST").upper()
WEBHOOK_TEST = os.getenv("DISCORD_WEBHOOK_TEST")
WEBHOOK_PROD = os.getenv("DISCORD_WEBHOOK_PROD")
WEBHOOK_SECONDARY = os.getenv("DISCORD_WEBHOOK_SECONDARY")  # Additional webhook

# Check required credentials based on environment
# Note: OPENROUTER_KEY is no longer required since AI analysis was removed
required_creds = [TRUTH_USERNAME, TRUTH_PASSWORD]

# Only require the webhook for the active environment
if APP_ENV == "PRODUCTION":
    if not WEBHOOK_PROD:
        print("❌ Error: DISCORD_WEBHOOK_PROD not set (required for PRODUCTION mode)")
        exit(1)
    ACTIVE_WEBHOOK = WEBHOOK_PROD
else:
    if not WEBHOOK_TEST:
        print("❌ Error: DISCORD_WEBHOOK_TEST not set (required for TEST mode)")
        exit(1)
    ACTIVE_WEBHOOK = WEBHOOK_TEST

# Build list of all webhooks to post to
WEBHOOKS = [ACTIVE_WEBHOOK]
if WEBHOOK_SECONDARY:
    WEBHOOKS.append(WEBHOOK_SECONDARY)
    print(f"📡 Secondary webhook configured")

if not all(required_creds):
    print("❌ Error: Missing credentials in .env file.")
    print("Required: TRUTH_USERNAME, TRUTH_PASSWORD")
    exit(1)

print(f"⚙️  Running in {APP_ENV} MODE")

# ─── 2. Initialize Clients ─────────────────────────────────────────────────
print("Logging into Truth Social...")
try:
    # Try using token first if available (bypasses 403 errors)
    if TRUTH_TOKEN:
        print("🔑 Using pre-authenticated token...")
        api = Api(username=TRUTH_USERNAME, password=TRUTH_PASSWORD, token=TRUTH_TOKEN)
    else:
        api = Api(username=TRUTH_USERNAME, password=TRUTH_PASSWORD)
    
    # Initialize OpenRouter Client (optional - not used since AI removal)
    if OPENROUTER_KEY:
        client_OpenAI = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_KEY,
            default_headers={
                "HTTP-Referer": "https://github.com/TrumpTracker", 
                "X-Title": "TrumpTracker Script"
            }
        )
    print("✅ Successfully logged in.")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n💡 TIP: If you're getting HTTP 403 errors, try one of these solutions:")
    print("   1. Use the browser-based tracker: python tracker_browser.py")
    print("   2. Get a fresh token from your browser and add TRUTH_TOKEN to .env")
    print("   3. Wait a few hours and try again (rate limiting may have reset)")
    exit(1)

# ─── 3. Helper Functions ───────────────────────────────────────────────────

def clean_html(raw_html):
    """Remove HTML tags and decode HTML entities from content."""
    if not raw_html:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', raw_html)
    # Decode HTML entities (e.g., &amp; -> &)
    clean = html.unescape(clean)
    # Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def is_url_only(text):
    """
    Check if the text content is just a URL or link.
    Matches patterns like:
    - http://example.com
    - https://example.com/path
    - example.com/path
    - justthenews.com/politics-polic...
    """
    if not text:
        return False
    
    text = text.strip()
    
    # Pattern for URLs (with or without protocol)
    url_pattern = r'^(https?://)?[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(/[^\s]*)?$'
    
    # Check if the entire content matches a URL pattern
    if re.match(url_pattern, text, re.IGNORECASE):
        return True
    
    # Also check for truncated URLs (ending with ...)
    truncated_pattern = r'^(https?://)?[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(/[^\s]*)?\.{2,}$'
    if re.match(truncated_pattern, text, re.IGNORECASE):
        return True
    
    return False

def is_valid_post(post):
    """
    Check if post is valid for extraction:
    - SKIP if link-only (card present but no real text content)
    - SKIP if URL-only (content is just a URL)
    - SKIP if media-only (has media but no text content)
    - VALID if has text content (with or without media)
    """
    if not post:
        return False, "No post data"
    
    # Get and clean content
    raw_content = post.get('content', '')
    clean_content = clean_html(raw_content)
    
    # Check if it's a reblog (repost of someone else's content)
    if post.get('reblog'):
        return False, "Reblog/repost of another user"
    
    # Check for link-only post (card present, no meaningful text)
    card = post.get('card')
    has_card = card is not None
    
    # Check for media
    media = post.get('media_attachments', [])
    has_media = len(media) > 0
    
    # Check for meaningful text content
    has_text = len(clean_content) > 0
    
    # NEW: Check if content is just a URL (link immediately after time element)
    if has_text and is_url_only(clean_content):
        return False, f"URL-only post: {clean_content[:50]}..."
    
    # Decision logic based on Cameron's rules:
    # 1. Link immediately after time = SKIP (handled above with is_url_only)
    # 2. Only image/video (no text) = SKIP
    # 3. Text (with or without image/video) = VALID
    
    if has_card and not has_text:
        return False, "Link-only post (no text)"
    
    if has_media and not has_text:
        return False, "Media-only post (no text)"
    
    if not has_text:
        return False, "Empty content"
    
    return True, "Valid post with text content"

# --- Persistent browser session (stays open all week) ---
# Uses DrissionPage to keep one Chrome tab open permanently.
# You can manually login or clear Cloudflare once at startup.
# The tab stays open and cookies are reused for all API calls.
_browser_page = None            # DrissionPage Chromium instance
_browser_cookies = None         # Cached cookies from the browser
_browser_user_agent = None      # User-Agent from the browser


def _ensure_persistent_browser():
    """
    Open a Chrome browser tab ONCE that stays open until you close it.
    Returns True if browser is ready, False on error.
    """
    global _browser_page, _browser_cookies, _browser_user_agent
    
    if _browser_page is not None:
        return True  # Already open
    
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
        
        print("  🌐 Opening Chrome browser (will stay open until you close it)...")
        
        # Configure Chrome to look like a real user
        # Use port 9223 to avoid conflicts with other DrissionPage programs
        options = ChromiumOptions()
        options.set_argument('--disable-blink-features=AutomationControlled')
        options.set_argument('--disable-dev-shm-usage')
        options.set_argument('--no-sandbox')
        options.set_local_port(9223)  # Different port from default 9222
        
        # Open browser (visible window)
        _browser_page = ChromiumPage(addr_or_opts=options)
        
        # Navigate to Truth Social
        print("  🔗 Navigating to Truth Social...")
        _browser_page.get("https://truthsocial.com/@realDonaldTrump")
        
        # Wait for user to clear Cloudflare if needed
        print("  ⏳ Waiting for page to load (clear Cloudflare manually if prompted)...")
        import time
        time.sleep(15)  # Give time for Cloudflare to clear
        
        # Check if we're past Cloudflare
        title = _browser_page.title
        if "just a moment" in title.lower() or "cloudflare" in title.lower():
            print("  ⚠️  Cloudflare challenge detected - please solve it in the browser")
            print("     The tracker will wait 60 seconds...")
            time.sleep(60)
        
        # Get cookies and user agent
        _refresh_browser_cookies()
        
        print("  ✅ Browser ready! Tab will stay open for the week.")
        return True
        
    except Exception as e:
        print(f"  ❌ Could not open browser: {e}")
        return False


def _refresh_browser_cookies():
    """Extract cookies from the open browser tab."""
    global _browser_cookies, _browser_user_agent
    
    if _browser_page is None:
        return False
    
    try:
        # Get all cookies from the browser
        cookies = _browser_page.cookies(all_domains=True)
        _browser_cookies = {}
        for cookie in cookies:
            if 'truthsocial.com' in cookie.get('domain', ''):
                _browser_cookies[cookie['name']] = cookie['value']
        
        # Get user agent
        _browser_user_agent = _browser_page.run_js('return navigator.userAgent')
        
        print(f"  🍪 Extracted {len(_browser_cookies)} cookies from browser")
        return True
    except Exception as e:
        print(f"  ⚠️  Could not extract cookies: {e}")
        return False


def fetch_latest_valid_flaresolverr(max_scan=10):
    """
    Uses persistent Chrome browser (DrissionPage) to bypass Cloudflare.
    
    - Browser opens ONCE at first call and stays open
    - You can manually login or clear Cloudflare in the browser window
    - Cookies are extracted and reused with curl_cffi for API calls
    - Only refreshes cookies when they expire (403)
    """
    global _browser_cookies, _browser_user_agent
    
    try:
        from curl_cffi import requests as cffi_requests
        from datetime import datetime, timezone
        
        # Ensure browser is open (no-op if already open)
        if not _ensure_persistent_browser():
            return None
        
        # Get cookies if we don't have any cached
        if not _browser_cookies:
            if not _refresh_browser_cookies():
                return None
        else:
            print("  🔄 Using cached browser cookies...")
        
        # Use curl_cffi with cookies to hit API (TLS fingerprint must match)
        session = cffi_requests.Session(impersonate="chrome")
        for name, value in _browser_cookies.items():
            session.cookies.set(name, value, domain=".truthsocial.com")
        
        headers = {
            "User-Agent": _browser_user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://truthsocial.com/@realDonaldTrump",
        }
        
        # Fetch posts from API
        api_url = "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses"
        resp = session.get(api_url, params={
            "limit": max_scan,
            "exclude_replies": "true",
            "exclude_reblogs": "true"
        }, headers=headers, timeout=30)
        
        # If cookies expired, refresh once and retry
        if resp.status_code == 403:
            print("  ⚠️  Cookies expired, refreshing from browser...")
            if not _refresh_browser_cookies():
                return None
            # Retry with fresh cookies
            session = cffi_requests.Session(impersonate="chrome")
            for name, value in _browser_cookies.items():
                session.cookies.set(name, value, domain=".truthsocial.com")
            resp = session.get(api_url, params={
                "limit": max_scan,
                "exclude_replies": "true",
                "exclude_reblogs": "true"
            }, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            print(f"  ⚠️  API returned {resp.status_code} even with cookies")
            return None
        
        posts = resp.json()
        print(f"  ✅ Got {len(posts)} posts from API")
        
        for i, post in enumerate(posts[:max_scan]):
            is_valid_result, reason = is_valid_post(post)
            
            if is_valid_result:
                post['clean_content'] = clean_html(post.get('content', ''))
                media = post.get('media_attachments', [])
                post['media_urls'] = [m.get('url', '') for m in media] if media else []
                post['url'] = f"https://truthsocial.com/@realDonaldTrump/posts/{post['id']}"
                print(f"  ✅ Post #{i+1} is valid: {post['clean_content'][:80]}...")
                return post
            else:
                print(f"  ⏭️  Post #{i+1} skipped: {reason}")
        
        print(f"  ⚠️  No valid posts found in {max_scan} posts")
        return None
        
    except Exception as e:
        print(f"  ❌ Browser method failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def fetch_latest_valid(max_scan=10):
    """
    Fetch posts and return the first valid one based on filtering rules.
    Scans up to max_scan posts to find a valid one.
    """
    try:
        post_gen = api.pull_statuses(username="realDonaldTrump", replies=False, verbose=False)
        
        for i, post in enumerate(islice(post_gen, max_scan)):
            is_valid, reason = is_valid_post(post)
            
            if is_valid:
                # Clean the content before returning
                post['clean_content'] = clean_html(post.get('content', ''))
                
                # Also extract media URLs if present
                media = post.get('media_attachments', [])
                if media:
                    post['media_urls'] = [m.get('url', '') for m in media]
                else:
                    post['media_urls'] = []
                    
                print(f"  ✅ Post #{i+1} is valid: {reason}")
                return post
            else:
                print(f"  ⏭️  Post #{i+1} skipped: {reason}")
        
        print(f"  ⚠️  No valid posts found in last {max_scan} posts")
        return None
        
    except Exception as e:
        error_msg = str(e).lower()
        # Check if it's a Cloudflare block
        if 'cloudflare' in error_msg or 'just a moment' in error_msg or 'nonetype' in error_msg:
            print(f"⚠️  API blocked by Cloudflare, will try FlareSolverr...")
            return None
        print(f"Error fetching post: {e}")
        return None



def generate_post_link(post_id):
    return f"https://truthsocial.com/@realDonaldTrump/posts/{post_id}"

def send_discord_alert(webhook_url, post_content, post_link, post_timestamp, color, is_market_impact=True):
    """
    Send formatted Discord alert with:
    - Date/Time at top
    - Clickable author header linking to the post
    - Text body
    - Post link at bottom
    - Footer with EST time
    """
    from datetime import datetime, timezone, timedelta
    
    # Parse timestamp and convert to EST
    try:
        # Parse ISO timestamp: 2025-12-13T14:00:37.465Z
        dt = datetime.fromisoformat(post_timestamp.replace('Z', '+00:00'))
        # Convert to EST (UTC-5)
        est = timezone(timedelta(hours=-5))
        dt_est = dt.astimezone(est)
        formatted_time_est = dt_est.strftime("%b %d, %H:%M EST")
    except:
        formatted_time_est = post_timestamp
    
    if is_market_impact:
        title = "🚨 Trump Market Alert"
        header_text = f"**New post from @realDonaldTrump**"
    else:
        title = "📬 New Trump Post"
        header_text = f"**New post from @realDonaldTrump**"
    
    # Build description with link at bottom
    description = f"{header_text}\n\n{post_content}\n\n🔗 {post_link}"
    
    data = {
        "embeds": [{
            "title": title,
            "description": description,
            "url": post_link,  # Makes the title clickable
            "color": color,
            "author": {
                "name": "Donald J. Trump @realDonaldTrump",
                "url": post_link,
                "icon_url": "https://pbs.twimg.com/profile_images/874276197357596672/kUuht00m_400x400.jpg"
            },
            "footer": {"text": f"TrumpTracker • {formatted_time_est}"}
        }]
    }
    try:
        requests.post(webhook_url, json=data)
        print(f"📨 Sent Discord notification to {'PROD' if webhook_url == WEBHOOK_PROD else 'TEST'}")
    except Exception as e:
        print(f"❌ Failed to send Discord alert: {e}")

def analyze_post(input_text):
    user_prompt = f"""
You are a senior equity research analyst. Analyze this Truth Social post by Donald Trump.
1. Determine if it contains credible, market-relevant info.
2. If yes, explain why technically.
3. List 3 affected tickers.

⚠️ IMPORTANT:
- If NO credible market impact, output exactly: **Pineapple**
- Do NOT speculate.

Input:
{input_text}
"""
    system_prompt = "You are a factual equity research assistant. If no market impact, return 'Pineapple'."

    try:
        response = client_OpenAI.chat.completions.create(
            model="openai/gpt-4o-mini", # OpenRouter Model ID
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        return "Pineapple"

# ─── 4. Main Execution Loop ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting Truth Social tracker. Checking every 2 minutes...\n")
    
    last_seen_id = None
    api_failure_count = 0
    
    while True:
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Scanning for valid posts...")
            
            # Two-tier fallback:
            # 1. Try standard API first (truthbrush library)
            latest = fetch_latest_valid(max_scan=10)
            
            # 2. If API blocked by Cloudflare, use FlareSolverr + curl_cffi
            #    FlareSolverr runs locally, solves Cloudflare with real Chrome,
            #    then we use the cookies with curl_cffi to hit the API.
            if latest is None:
                api_failure_count += 1
                print(f"  API blocked ({api_failure_count}), using FlareSolverr...")
                latest = fetch_latest_valid_flaresolverr(max_scan=10)
            else:
                api_failure_count = 0  # Reset on success
            
            if latest is None:
                print("No valid posts found or connection error.")
            else:
                current_id = latest["id"]
                
                if last_seen_id is None:
                    # First run: Process the initial post (don't just store it as baseline)
                    last_seen_id = current_id
                    print(f"Tracker initialized. Processing first valid post ID: {last_seen_id}")
                    print(f"  Content preview: {latest['clean_content'][:100]}...")
                    
                    # Send post directly without AI analysis
                    post_link = latest.get('url') or generate_post_link(latest["id"])
                    print("📬 Sending post to Discord and Truth Social...")
                    
                    # Send to all Discord webhooks
                    for webhook in WEBHOOKS:
                        send_discord_alert(webhook, latest['clean_content'], post_link, latest['created_at'], 15158332, is_market_impact=False)
                    
                    # Repost to Truth Social (only if API is working)
                    if APP_ENV == "PRODUCTION":
                        truth_post_text = f"{post_link}"
                        try:
                            if hasattr(api, 'create_status'):
                                api.create_status(status=truth_post_text)
                                print("✅ Reposted to Truth Social!")
                            else:
                                print("ℹ️  Truth Social repost skipped (API not available)")
                        except Exception as e:
                            print(f"⚠️  Failed repost: {e}")
                    else:
                        print("ℹ️  Skipped Truth Social repost (TEST MODE)")
                    
                    print(f"\n✅ Initial post processed. Now watching for new posts...\n")
                
                elif current_id != last_seen_id:
                    print(f"[{latest['created_at']}] New valid post detected!")
                    last_seen_id = current_id
                    
                    post_link = latest.get('url') or generate_post_link(latest["id"])
                    print("📬 Sending post to Discord and Truth Social...")
                    
                    # Send to all Discord webhooks
                    for webhook in WEBHOOKS:
                        send_discord_alert(webhook, latest['clean_content'], post_link, latest['created_at'], 15158332, is_market_impact=False)
                    
                    # Repost to Truth Social (only if API is working)
                    if APP_ENV == "PRODUCTION":
                        truth_post_text = f"{post_link}"
                        try:
                            if hasattr(api, 'create_status'):
                                api.create_status(status=truth_post_text)
                                print("✅ Reposted to Truth Social!")
                            else:
                                print("ℹ️  Truth Social repost skipped (API not available)")
                        except Exception as e:
                            print(f"⚠️  Failed repost: {e}")
                    else:
                        print("ℹ️  Skipped Truth Social repost (TEST MODE)")

                else:
                    print(f"  No new posts since last check.")
                    
        except Exception as e:
            print(f"Loop Error: {e}") 

        time.sleep(120)