from flask import Flask, jsonify, abort
from flask_cors import CORS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os, time, random, logging, json

# ------------------------
# CONFIGURATION
# ------------------------
load_dotenv()
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- YOUTUBE API KEY ---
# Removed hardcoded fallback key — will use environment variable set via Jenkins and Docker build arg
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()

if not YOUTUBE_API_KEY:
    logging.warning("⚠️ No YouTube API key found in environment; CrowdPulse will use fallback data.")

try:
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY) if YOUTUBE_API_KEY else None
    if youtube:
        logging.info("✅ YouTube API client initialized successfully (live data enabled).")
except Exception as e:
    youtube = None
    logging.error(f"Failed to initialize YouTube client: {e}")

analyzer = SentimentIntensityAnalyzer()

CITY_MAP = {
    "DEL": "Delhi", "BOM": "Mumbai", "CCU": "Kolkata", "MAA": "Chennai", "GOI": "Goa",
    "HYD": "Hyderabad", "HKT": "Phuket", "SUB": "Juanda", "NRT": "Narita", "HND": "Haneda",
    "DXB": "Dubai", "SYD": "Sydney", "MEL": "Melbourne", "AKL": "Auckland",
    "LHR": "London", "NYC": "New York", "LAX": "Los Angeles", "CDG": "Paris", "TOK": "Tokyo"
}

CACHE = {}
TTL = 900  # 15 minutes

# Static fallback data (minimal but attractive)
STATIC_VLOGS = {
    "GOA": [
        {"title": "Exploring Goa 2024 | Best Beaches & Food", "url": "https://www.youtube.com/watch?v=PfAoO4RVmV0",
         "thumbnail": "https://i.ytimg.com/vi/PfAoO4RVmV0/hqdefault.jpg"},
        {"title": "Goa Nightlife & Beaches | Complete Vlog", "url": "https://www.youtube.com/watch?v=gw2YV2vR3NI",
         "thumbnail": "https://i.ytimg.com/vi/gw2YV2vR3NI/hqdefault.jpg"},
    ],
    "DXB": [
        {"title": "Dubai in 48 Hours | Desert Safari & Skyline", "url": "https://www.youtube.com/watch?v=R4R6nUgZngE",
         "thumbnail": "https://i.ytimg.com/vi/R4R6nUgZngE/hqdefault.jpg"},
        {"title": "Dubai Travel Guide 2024", "url": "https://www.youtube.com/watch?v=FHTaBCgZghM",
         "thumbnail": "https://i.ytimg.com/vi/FHTaBCgZghM/hqdefault.jpg"}
    ]
}

# ------------------------
# UTILITY FUNCTIONS
# ------------------------

def get_social_posts(city_name: str):
    """Generate pseudo-random social media sentiment posts."""
    posts = []
    for _ in range(random.randint(6, 12)):
        adj = random.choice(["amazing", "terrible", "beautiful", "crowded", "peaceful", "exciting"])
        text = f"My experience in {city_name} was {adj}!"
        score = analyzer.polarity_scores(text)["compound"]
        sentiment = "neutral"
        if score >= 0.05:
            sentiment = "positive"
        elif score <= -0.05:
            sentiment = "negative"
        posts.append({
            "text": text,
            "source": random.choice(["Twitter", "Reddit"]),
            "sentiment": sentiment
        })
    return posts


def get_youtube_videos(city_name: str):
    """
    Fetch actual YouTube vlog data for the given city.
    Falls back to static samples or placeholders if API quota is exceeded.
    """
    code = next((k for k, v in CITY_MAP.items() if v.lower() == city_name.lower()), None)
    videos = []

    # First, return static known vlogs if available
    if code and code in STATIC_VLOGS:
        return STATIC_VLOGS[code]

    # If YouTube API unavailable
    if not youtube:
        logging.warning("YouTube client unavailable. Using static fallback.")
        return STATIC_VLOGS.get(code, [{
            "title": f"Top sights in {city_name}",
            "url": "https://www.youtube.com",
            "thumbnail": "https://placehold.co/200x120/6c2bd9/white?text=Vlog"
        }])

    try:
        search_query = f"{city_name} travel vlog 2024 tourism"
        req = youtube.search().list(
            q=search_query,
            part="snippet",
            type="video",
            order="viewCount",
            maxResults=5
        )
        res = req.execute()

        for item in res.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            videos.append({
                "title": snippet["title"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": snippet["thumbnails"]["high"]["url"]
            })

        # If API returned nothing, fallback to static
        if not videos:
            raise ValueError("Empty response")

    except Exception as e:
        logging.warning(f"[YouTube API Fallback for {city_name}] {e}")
        videos = STATIC_VLOGS.get(code, [{
            "title": f"Explore {city_name} | Travel Highlights",
            "url": "https://www.youtube.com",
            "thumbnail": "https://placehold.co/200x120/6c2bd9/white?text=Vlog"
        }])
    return videos


# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def home():
    return "<h3>🌍 CrowdPulse API running</h3>", 200

@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/api/crowdpulse/health")
def health_check():
    return "OK", 200

@app.route("/api/crowdpulse/<string:city_code>")
def get_city_pulse(city_code):
    city_code = city_code.upper()
    now = time.time()

    # Cached
    cached = CACHE.get(city_code)
    if cached and now - cached["timestamp"] < TTL:
        logging.info(f"Returning cached data for {city_code}")
        return jsonify(cached["data"])

    city_name = CITY_MAP.get(city_code)
    if not city_name:
        abort(404, description="City code not found")

    logging.info(f"Fetching live data for {city_name}")
    social_posts = get_social_posts(city_name)
    youtube_videos = get_youtube_videos(city_name)

    data = {
        "city_code": city_code,
        "city_name": city_name,
        "social_media_posts": social_posts,
        "youtube_videos": youtube_videos,
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    CACHE[city_code] = {"data": data, "timestamp": now}
    return jsonify(data)


# ------------------------
# ENTRY POINT
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=False)
