import os
import time
import requests
from itertools import islice
from dotenv import load_dotenv
from openai import OpenAI
from truthbrush.api import Api

# ─── 1. Load Credentials ───────────────────────────────────────────────────
load_dotenv()

TRUTH_USERNAME = os.getenv("TRUTH_USERNAME")
TRUTH_PASSWORD = os.getenv("TRUTH_PASSWORD")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")  # <--- CHANGED HERE

# Environment Config
APP_ENV = os.getenv("ENVIRONMENT", "TEST").upper()
WEBHOOK_TEST = os.getenv("DISCORD_WEBHOOK_TEST")
WEBHOOK_PROD = os.getenv("DISCORD_WEBHOOK_PROD")

ACTIVE_WEBHOOK = WEBHOOK_PROD if APP_ENV == "PRODUCTION" else WEBHOOK_TEST

# Check for OPENROUTER_KEY now instead of OPENAI_KEY
if not all([TRUTH_USERNAME, TRUTH_PASSWORD, OPENROUTER_KEY, WEBHOOK_TEST, WEBHOOK_PROD]):
    print("❌ Error: Missing credentials in .env file.")
    print("Make sure you renamed OPENAI_API_KEY to OPENROUTER_API_KEY in your .env file.")
    exit(1)

print(f"⚙️  Running in {APP_ENV} MODE")

# ─── 2. Initialize Clients ─────────────────────────────────────────────────
print("Logging into Truth Social...")
try:
    api = Api(username=TRUTH_USERNAME, password=TRUTH_PASSWORD)
    
    # Initialize OpenRouter Client
    client_OpenAI = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_KEY, # <--- Uses the new variable
        default_headers={
            "HTTP-Referer": "https://github.com/TrumpTracker", 
            "X-Title": "TrumpTracker Script"
        }
    )
    print("✅ Successfully logged in.")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# ─── 3. Helper Functions ───────────────────────────────────────────────────

def fetch_latest():
    try:
        post_gen = api.pull_statuses(username="realDonaldTrump", replies=False, verbose=False)
        return next(islice(post_gen, 1), None)
    except Exception as e:
        print(f"Error fetching post: {e}")
        return None

def generate_post_link(post_id):
    return f"https://truthsocial.com/@realDonaldTrump/posts/{post_id}"

def send_discord_alert(webhook_url, title, description, post_link, color):
    data = {
        "embeds": [{
            "title": title,
            "description": description,
            "url": post_link,
            "color": color,
            "footer": {"text": f"TrumpTracker • {APP_ENV} Mode"}
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
    
    while True:
        try:
            latest = fetch_latest()
            
            if latest is None:
                print("No posts found or connection error.")
            else:
                current_id = latest["id"]
                
                if last_seen_id is None:
                    last_seen_id = current_id
                    print(f"Tracker initialized. Last post ID: {last_seen_id}")
                
                elif current_id != last_seen_id:
                    print(f"[{latest['created_at']}] New post detected.")
                    last_seen_id = current_id
                    
                    post_link = generate_post_link(latest["id"])
                    analysis = analyze_post(latest["content"])
                    print(f"Analysis Result: {analysis[:50]}...")

                    if "Pineapple" not in analysis:
                        # Market Impact
                        send_discord_alert(ACTIVE_WEBHOOK, "🚨 Trump Market Alert", analysis, post_link, 15158332)
                        
                        if APP_ENV == "PRODUCTION":
                            truth_post_text = f"{post_link}\n\n{analysis}"
                            if len(truth_post_text) > 500:
                                truth_post_text = truth_post_text[:497] + "..."
                            try:
                                api.create_status(status=truth_post_text)
                                print("✅ Reposted to Truth Social!")
                            except Exception as e:
                                print(f"❌ Failed repost: {e}")
                        else:
                            print("ℹ️  Skipped Truth Social repost (TEST MODE)")
                    else:
                        # No Impact
                        print("🍍 No market impact.")
                        if APP_ENV == "TEST":
                            send_discord_alert(WEBHOOK_TEST, "🍍 Non-Market Post", f"Content: {latest['content'][:100]}...", post_link, 3447003)

                else:
                    print(f"[{time.strftime('%H:%M:%S')}] No new post.")
                    
        except Exception as e:
            print(f"Loop Error: {e}") 

        time.sleep(120)