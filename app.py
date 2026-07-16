from flask import Flask, request, jsonify
import requests
import random
import string
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Config
AROLINK_API = "https://arolinks.com/api"
AROLINK_TOKEN = "82288e6f415eb47c5e596a29d2f1df044ed42620"

def generate_semy_alias():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"Semy{letters}{numbers}"

@app.route('/done', methods=['GET'])
def process_url():
    original_url = request.args.get('url')
    
    if not original_url:
        return jsonify({
            "error": "URL nahi diya!",
            "example": "/done?url=https://example.com"
        }), 400
    
    print(f"📥 Original URL: {original_url}")
    
    # Step 1: Arolink
    arolink_alias = generate_semy_alias()
    arolink_result = hit_arolink(original_url, arolink_alias)
    
    if arolink_result.get('status') != 'success':
        return jsonify({
            "error": "Arolink failed",
            "details": arolink_result
        }), 500
    
    arolink_short = arolink_result.get('shortenedUrl')
    print(f"🔗 Arolink: {arolink_short}")
    
    # Step 2: is.gd se short karo (FIXED)
    isgd_result = hit_isgd(arolink_short)
    
    if 'error' in isgd_result:
        return jsonify({
            "error": "is.gd failed",
            "arolink_url": arolink_short,
            "details": isgd_result
        }), 500
    
    print(f"🔗 is.gd: {isgd_result.get('url')}")
    
    return jsonify({
        "success": True,
        "original_url": original_url,
        "generated_aliases": {
            "arolink": arolink_alias
        },
        "step_1_arolink": {
            "short_url": arolink_short,
            "expires_in": "30 minutes"
        },
        "step_2_isgd": {
            "short_url": isgd_result.get('url'),
            "full_response": isgd_result
        },
        "final_links": {
            "arolink": arolink_short,
            "isgd": isgd_result.get('url')
        },
        "timestamp": datetime.now().isoformat()
    })

def hit_arolink(url, alias):
    try:
        params = {
            "api": AROLINK_TOKEN,
            "url": url,
            "alias": alias
        }
        response = requests.get(AROLINK_API, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def hit_isgd(url):
    """is.gd - FIXED: No JSON, direct text response"""
    try:
        # is.gd ka API simple text return karta hai
        params = {
            "format": "simple",  # Simple text response
            "url": url
        }
        
        response = requests.get("https://is.gd/create.php", params=params, timeout=10)
        
        print(f"🌐 is.gd Response: {response.text}")
        
        if response.status_code == 200:
            short_url = response.text.strip()
            
            # Check if it's a valid URL
            if short_url.startswith('https://is.gd/'):
                return {
                    "url": short_url,
                    "status": "success",
                    "service": "is.gd"
                }
            elif "error" in short_url.lower():
                return {"error": short_url}
            else:
                return {"error": f"Unexpected response: {short_url}"}
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "service": "Double URL Shortener 🚀",
        "flow": "Original URL → Arolink (30 min) → is.gd (Permanent)",
        "how_to_use": "/done?url=YOUR_URL",
        "example": "/done?url=https://google.com",
        "alias_format": "Semy + 3 CAPITAL Letters + 3 Numbers",
        "features": [
            "✅ is.gd - Fastest redirect",
            "✅ No API key needed",
            "✅ Arolink expires in 30 minutes",
            "✅ is.gd link permanent"
        ]
    })

@app.route('/health')
def health():
    return jsonify({"status": "OK", "time": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True)
