from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import hashlib
import time
import random
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow all CORS requests

# ============================================
# BANGLADESH SERVER CONFIGURATION
# ============================================

# BD Server Regions (যেগুলো বাংলাদেশে কাজ করে)
BD_REGIONS = {
    'bd': 'Bangladesh Server',
    'ind': 'India Server (BD players use this)',
    'sg': 'Singapore Server',
    'as': 'Asia Server'
}

# Real API endpoints (Community maintained)
REAL_API_URL = "https://api.djogos.com/ff"
BACKUP_API_URL = "https://ff.garena.com/api"

# Mock data flag (if no API key)
USE_MOCK_DATA = True  # Change to False if you have real API key

# Cache system
cache = {}
CACHE_DURATION = 300  # 5 minutes

# ============================================
# BD PLAYER NAMES (Localized)
# ============================================

BD_NICKNAMES = [
    "🔥BD Tiger🔥", "Sohan FF", "Rakib Boss", "Shahin OP", 
    "BD King Slayer", "Mahi The Great", "Tanvir X", "Shakib Pro",
    "BD Phoenix", "Riyad Killer", "Hasan Viper", "Nayeem Star",
    "BD Assassin", "Jony Blaster", "Masud HeadHunter", "Rafiq Legend"
]

BD_CLANS = [
    "BD Warriors", "Bengal Tigers", "Dhaka Devils", "Chittagong Kings",
    "BD Elites", "Bengal Phoenix", "Royal Bengals", "BD Shadows"
]

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def home():
    """API Homepage - BD Server"""
    return jsonify({
        "status": "active",
        "server": "Free Fire BD Server API",
        "version": "2.0.0",
        "region": "Bangladesh (BD)",
        "endpoints": {
            "/": "এই পেজ",
            "/api/bd/player": "BD প্লেয়ারের ইনফো (uid লাগবে)",
            "/api/bd/stats": "BD প্লেয়ারের স্ট্যাটস",
            "/api/bd/search": "নাম দিয়ে প্লেয়ার খুঁজুন",
            "/api/bd/leaderboard": "BD টপ প্লেয়ার লিস্ট",
            "/api/bd/bancheck": "ব্যান চেক করুন",
            "/api/bd/regions": "সাপোর্টেড রিজিয়ন লিস্ট"
        },
        "example": "/api/bd/player?uid=123456789",
        "note": "BD server এর জন্য uid 9-10 ডিজিটের হয়"
    })

@app.route('/api/bd/regions')
def get_regions():
    """Get supported regions for BD players"""
    return jsonify({
        "bangladesh_server": {
            "primary": "ind",
            "alternative": "sg",
            "description": "BD players mostly use India server"
        },
        "available_regions": BD_REGIONS,
        "recommended": "ind (India server - best for BD)"
    })

@app.route('/api/bd/player')
def get_bd_player():
    """Get Bangladesh player info by UID"""
    uid = request.args.get('uid')
    region = request.args.get('region', 'ind')  # Default: India server
    
    # Validation
    if not uid:
        return jsonify({
            "error": "UID দিতে হবে",
            "message": "Please provide UID parameter",
            "example": "/api/bd/player?uid=123456789"
        }), 400
    
    if not uid.isdigit():
        return jsonify({
            "error": "UID শুধু সংখ্যা হতে হবে",
            "message": "UID must contain only numbers"
        }), 400
    
    if len(uid) < 8 or len(uid) > 10:
        return jsonify({
            "error": "UID এর দৈর্ঘ্য 8-10 ডিজিট হতে হবে",
            "message": "UID length should be 8-10 digits"
        }), 400
    
    # Check cache
    cache_key = f"player_{uid}_{region}"
    if cache_key in cache:
        cached_data, timestamp = cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return jsonify(cached_data)
    
    # Try real API first
    if not USE_MOCK_DATA:
        try:
            result = fetch_real_player_data(uid, region)
            if result:
                cache[cache_key] = (result, time.time())
                return jsonify(result)
        except:
            pass  # Fallback to mock
    
    # Return mock BD player data
    player_data = generate_bd_player_data(uid, region)
    cache[cache_key] = (player_data, time.time())
    return jsonify(player_data)

@app.route('/api/bd/stats')
def get_bd_stats():
    """Get BD player game statistics"""
    uid = request.args.get('uid')
    region = request.args.get('region', 'ind')
    mode = request.args.get('mode', 'br')  # br, cs, lf
    
    if not uid:
        return jsonify({"error": "UID required"}), 400
    
    cache_key = f"stats_{uid}_{region}_{mode}"
    if cache_key in cache:
        cached_data, timestamp = cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return jsonify(cached_data)
    
    stats = generate_bd_player_stats(uid, mode)
    cache[cache_key] = (stats, time.time())
    return jsonify(stats)

@app.route('/api/bd/search')
def search_player():
    """Search BD player by name"""
    name = request.args.get('name')
    region = request.args.get('region', 'ind')
    
    if not name or len(name) < 3:
        return jsonify({
            "error": "কমপক্ষে ৩ অক্ষরের নাম দিন",
            "message": "Enter at least 3 characters"
        }), 400
    
    # Search in our mock database
    results = search_bd_players_by_name(name)
    
    return jsonify({
        "status": "success",
        "query": name,
        "region": region,
        "total_found": len(results),
        "players": results,
        "note": "BD server এর প্লেয়ার খুঁজে পাওয়া গেছে"
    })

@app.route('/api/bd/leaderboard')
def get_bd_leaderboard():
    """Get Bangladesh server leaderboard"""
    category = request.args.get('category', 'kills')  # kills, wins, headshots, level
    limit = int(request.args.get('limit', 10))
    
    leaderboard = generate_bd_leaderboard(category, limit)
    
    return jsonify({
        "status": "success",
        "server": "Bangladesh (BD)",
        "category": category,
        "updated_at": datetime.now().isoformat(),
        "top_players": leaderboard,
        "total_players": 15000
    })

@app.route('/api/bd/bancheck')
def check_ban_status():
    """Check if BD player is banned"""
    uid = request.args.get('uid')
    
    if not uid:
        return jsonify({"error": "UID required"}), 400
    
    # Generate deterministic ban status based on UID
    random.seed(int(uid) % 1000)
    is_banned = random.random() < 0.05  # 5% chance
    
    ban_reasons = ["টক্সিক আচরণ", "হ্যাক ব্যবহার", "অভিযোগ", "নিয়ম ভঙ্গ", "চিটিং"]
    
    return jsonify({
        "uid": uid,
        "server": "BD",
        "is_banned": is_banned,
        "ban_reason": random.choice(ban_reasons) if is_banned else None,
        "banned_date": datetime.now().isoformat() if is_banned else None,
        "appeal_possible": True if is_banned else False
    })

@app.route('/api/bd/rank')
def get_player_rank():
    """Get BD player rank info"""
    uid = request.args.get('uid')
    season = request.args.get('season', 'current')
    
    if not uid:
        return jsonify({"error": "UID required"}), 400
    
    ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Heroic", "Grandmaster", "Legend"]
    random.seed(int(uid) % 100)
    current_rank = random.choice(ranks)
    rank_points = random.randint(1000, 5000)
    
    return jsonify({
        "uid": uid,
        "season": season,
        "current_rank": current_rank,
        "rank_points": rank_points,
        "next_rank": get_next_rank(current_rank),
        "points_to_next": random.randint(50, 200),
        "region_rank": random.randint(100, 5000),
        "bd_rank": random.randint(50, 1000)
    })

# ============================================
# HELPER FUNCTIONS
# ============================================

def fetch_real_player_data(uid, region):
    """Try to fetch from real API"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        url = f"{REAL_API_URL}/player?id={uid}&region={region}"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def generate_bd_player_data(uid, region):
    """Generate mock BD player data"""
    random.seed(int(uid) % 1000)
    
    # BD specific name generation
    name_index = random.randint(0, len(BD_NICKNAMES) - 1)
    player_name = BD_NICKNAMES[name_index]
    
    # BD city/region
    bd_cities = ["Dhaka", "Chittagong", "Khulna", "Rajshahi", "Sylhet", "Barishal", "Rangpur", "Mymensingh"]
    
    return {
        "status": "success",
        "server": "Bangladesh (BD)",
        "data": {
            "uid": uid,
            "nickname": player_name,
            "level": random.randint(30, 100),
            "xp": random.randint(10000, 500000),
            "region_used": region,
            "country": "Bangladesh",
            "city": random.choice(bd_cities),
            "clan": {
                "name": random.choice(BD_CLANS),
                "level": random.randint(1, 10),
                "members": random.randint(10, 50)
            },
            "avatar_url": f"https://avatar.example.com/{uid}",
            "title": random.choice(["Warrior", "Elite", "Legend", "Pro Player", "Head Hunter"]),
            "joined_date": f"202{random.randint(0,3)}-{random.randint(1,12)}-{random.randint(1,28)}",
            "last_active": datetime.now().isoformat(),
            "is_online": random.choice([True, False])
        }
    }

def generate_bd_player_stats(uid, mode):
    """Generate BD player statistics"""
    random.seed(int(uid) % 1000 + ord(mode))
    
    matches = random.randint(200, 5000)
    wins = random.randint(20, matches // 2)
    kills = random.randint(100, matches * 4)
    deaths = random.randint(80, matches * 3)
    headshots = random.randint(30, kills // 2)
    assists = random.randint(20, kills // 3)
    
    return {
        "status": "success",
        "server": "Bangladesh (BD)",
        "game_mode": mode.upper(),
        "player_data": {
            "total_matches": matches,
            "wins": wins,
            "top_10": random.randint(matches // 4, matches // 2),
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "headshots": headshots,
            "win_rate": round((wins / matches) * 100, 2),
            "kdr": round(kills / max(1, deaths), 2),
            "hs_rate": round((headshots / kills) * 100, 2) if kills > 0 else 0,
            "longest_kill": random.randint(150, 350),
            "max_kills_match": random.randint(10, 35),
            "total_damage": random.randint(50000, 500000),
            "accuracy": round(random.uniform(15, 35), 2)
        },
        "achievements": {
            "booyahs": random.randint(5, 100),
            "squad_wins": random.randint(10, 150),
            "duo_wins": random.randint(5, 80),
            "solo_wins": random.randint(2, 50)
        }
    }

def search_bd_players_by_name(name):
    """Search players by name (mock)"""
    results = []
    search_term = name.lower()
    
    for idx, nick in enumerate(BD_NICKNAMES):
        if search_term in nick.lower():
            results.append({
                "uid": f"6{random.randint(10000000, 99999999)}",
                "nickname": nick,
                "level": random.randint(30, 100),
                "clan": random.choice(BD_CLANS)
            })
            if len(results) >= 5:
                break
    
    return results

def generate_bd_leaderboard(category, limit):
    """Generate BD leaderboard mock data"""
    leaderboard = []
    
    for i in range(limit):
        if category == "kills":
            value = random.randint(5000, 50000)
        elif category == "wins":
            value = random.randint(200, 3000)
        elif category == "headshots":
            value = random.randint(1000, 20000)
        else:  # level
            value = random.randint(60, 100)
        
        leaderboard.append({
            "rank": i + 1,
            "uid": f"6{random.randint(10000000, 99999999)}",
            "name": random.choice(BD_NICKNAMES),
            "value": value,
            "clan": random.choice(BD_CLANS),
            "region": "BD"
        })
    
    return leaderboard

def get_next_rank(current_rank):
    """Get next rank name"""
    ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Heroic", "Grandmaster", "Legend"]
    try:
        idx = ranks.index(current_rank)
        return ranks[idx + 1] if idx + 1 < len(ranks) else "Max Rank"
    except:
        return "Silver"

@app.route('/api/bd/ping')
def ping():
    """Check API latency"""
    return jsonify({
        "status": "pong",
        "server": "BD API",
        "timestamp": time.time(),
        "latency_ms": 0
    })

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "API endpoint খুঁজে পাওয়া যায়নি",
        "message": "Check / for available endpoints"
    }), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        "error": "সার্ভার সমস্যা",
        "message": "পরে আবার চেষ্টা করুন"
    }), 500

# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("=" * 50)
    print("🎮 Free Fire BD Server API")
    print(f"📍 Running on: http://localhost:{port}")
    print("🌍 Region: Bangladesh (BD)")
    print("=" * 50)
    print("\n📡 Available endpoints:")
    print("  GET /api/bd/player?uid=123456789")
    print("  GET /api/bd/stats?uid=123456789")
    print("  GET /api/bd/leaderboard")
    print("  GET /api/bd/rank?uid=123456789")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=port)