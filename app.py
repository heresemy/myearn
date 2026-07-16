from flask import Flask, request, jsonify
import requests
import json
import random
import string
from datetime import datetime

app = Flask(__name__)

# API Config
AROLINK_API = "https://arolinks.com/api"
AROLINK_TOKEN = "82288e6f415eb47c5e596a29d2f1df044ed42620"
ULVIS_API = "https://ulvis.net/API/write/get"

def generate_semy_alias():
    """Semy + 3 CAPITAL letters + 3 numbers"""
    # 3 random capital letters
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    # 3 random numbers
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"Semy{letters}{numbers}"

@app.route('/done', methods=['GET'])
def process_url():
    # 1. User se URL lo
    original_url = request.args.get('url')
    
    if not original_url:
        return jsonify({
            "error": "URL nahi diya!",
            "example": "/done?url=https://example.com"
        }), 400
    
    print(f"📥 Original URL: {original_url}")
    
    # 2. Generate Semy alias
    semy_alias = generate_semy_alias()
    print(f"🔑 Generated Alias: {semy_alias}")
    
    # 3. Pehle Arolink ko hit karo
    arolink_result = hit_arolink(original_url, semy_alias)
    
    if arolink_result.get('status') != 'success':
        return jsonify({
            "error": "Arolink mein problem",
            "details": arolink_result
        }), 500
    
    # 4. Arolink se short URL lo
    arolink_short = arolink_result.get('shortenedUrl')
    print(f"🔗 Arolink Short URL: {arolink_short}")
    
    # 5. Generate another Semy alias for Ulvis
    ulvis_alias = generate_semy_alias()
    print(f"🔑 Ulvis Alias: {ulvis_alias}")
    
    # 6. Ab is Arolink URL ko Ulvis mein daalo
    ulvis_result = hit_ulvis(arolink_short, ulvis_alias)
    
    if 'error' in ulvis_result:
        return jsonify({
            "error": "Ulvis mein problem",
            "arolink_url": arolink_short,
            "ulvis_error": ulvis_result
        }), 500
    
    # 7. Final response show karo
    return jsonify({
        "success": True,
        "original_url": original_url,
        "generated_aliases": {
            "arolink_alias": semy_alias,
            "ulvis_alias": ulvis_alias
        },
        "step_1_arolink": {
            "api_response": arolink_result,
            "short_url": arolink_short,
            "expires_in": "30 minutes"
        },
        "step_2_ulvis": {
            "api_response": ulvis_result,
            "short_url": ulvis_result.get('data', {}).get('url') if 'data' in ulvis_result else ulvis_result.get('url'),
            "id": ulvis_result.get('data', {}).get('id') if 'data' in ulvis_result else ulvis_result.get('id')
        },
        "final_links": {
            "arolink": arolink_short,
            "ulvis": ulvis_result.get('data', {}).get('url') if 'data' in ulvis_result else ulvis_result.get('url')
        },
        "timestamp": datetime.now().isoformat()
    })

def hit_arolink(url, alias):
    """Arolink API hit karo with Semy alias"""
    try:
        params = {
            "api": AROLINK_TOKEN,
            "url": url,
            "alias": alias  # SemyXXX123 format
        }
        
        response = requests.get(AROLINK_API, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Arolink Response: {data}")
            return data
        else:
            return {"error": f"Status {response.status_code}", "raw": response.text}
            
    except Exception as e:
        return {"error": str(e)}

def hit_ulvis(url, alias):
    """Ulvis API hit karo with Semy alias"""
    try:
        params = {
            "url": url,  # Yeh Arolink ki short URL hai
            "custom": alias,  # SemyXXX123 format
            "type": "json",
            "private": "1"
        }
        
        response = requests.get(ULVIS_API, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ulvis Response: {data}")
            return data
        else:
            return {"error": f"Status {response.status_code}", "raw": response.text}
            
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "service": "URL Shortener Chain - SEMY Edition",
        "how_to_use": "/done?url=YOUR_URL",
        "example": "/done?url=https://google.com",
        "alias_format": "Semy + 3 CAPITAL Letters + 3 Numbers (e.g., SEMYABC123)",
        "flow": "Original URL → Arolink (Semy Alias) → Ulvis (Semy Alias)"
    })

@app.route('/health')
def health():
    return jsonify({"status": "OK", "time": datetime.now().isoformat()})