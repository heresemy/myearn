from flask import Flask, request, jsonify
import requests
import random
import string
from datetime import datetime, timedelta
import time

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
    
    # Step 1: Arolink se short karo
    arolink_alias = generate_semy_alias()
    arolink_result = hit_arolink(original_url, arolink_alias)
    
    if arolink_result.get('status') != 'success':
        return jsonify({
            "error": "Arolink failed",
            "details": arolink_result
        }), 500
    
    arolink_short = arolink_result.get('shortenedUrl')
    print(f"🔗 Arolink: {arolink_short}")
    
    # Step 2: Arolink URL ko TinyURL se short karo (NO API KEY)
    tinyurl_result = hit_tinyurl(arolink_short)
    
    if 'error' in tinyurl_result:
        return jsonify({
            "error": "TinyURL failed",
            "arolink_url": arolink_short,
            "details": tinyurl_result
        }), 500
    
    print(f"🔗 TinyURL: {tinyurl_result.get('url')}")
    
    # Final response
    return jsonify({
        "success": True,
        "original_url": original_url,
        "generated_aliases": {
            "arolink": arolink_alias
        },
        "step_1_arolink": {
            "short_url": arolink_short,
            "expires_in": "30 minutes",
            "full_response": arolink_result
        },
        "step_2_tinyurl": {
            "short_url": tinyurl_result.get('url'),
            "full_response": tinyurl_result
        },
        "final_links": {
            "arolink": arolink_short,
            "tinyurl": tinyurl_result.get('url')
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

def hit_tinyurl(url):
    """TinyURL - No API key needed!"""
    try:
        # TinyURL simple API
        response = requests.get(
            f"https://tinyurl.com/api-create.php?url={url}",
            timeout=10
        )
        
        if response.status_code == 200:
            short_url = response.text.strip()
            if short_url and short_url.startswith('https://tinyurl.com/'):
                return {
                    "url": short_url,
                    "status": "success",
                    "service": "TinyURL"
                }
            else:
                return {"error": "Invalid response from TinyURL"}
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "service": "Double URL Shortener 🚀",
        "flow": "Original URL → Arolink (30 min) → TinyURL",
        "how_to_use": "/done?url=YOUR_URL",
        "example": "/done?url=https://google.com",
        "alias_format": "Semy + 3 CAPITAL Letters + 3 Numbers",
        "features": [
            "✅ No API key required",
            "✅ Arolink expires in 30 minutes",
            "✅ TinyURL permanent"
        ]
    })

@app.route('/health')
def health():
    return jsonify({"status": "OK", "time": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True)
