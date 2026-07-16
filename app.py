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
ULVIS_API = "https://ulvis.net/api.php"  # ✅ YEH SAHI HAI

def generate_semy_alias():
    """Semy + 3 CAPITAL letters + 3 numbers"""
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
    
    # 1. Generate Semy alias for Arolink
    arolink_alias = generate_semy_alias()
    print(f"🔑 Arolink Alias: {arolink_alias}")
    
    # 2. Arolink hit
    arolink_result = hit_arolink(original_url, arolink_alias)
    
    if arolink_result.get('status') != 'success':
        return jsonify({
            "error": "Arolink mein problem",
            "details": arolink_result
        }), 500
    
    arolink_short = arolink_result.get('shortenedUrl')
    print(f"🔗 Arolink Short URL: {arolink_short}")
    
    # 3. Generate Semy alias for Ulvis
    ulvis_alias = generate_semy_alias()
    print(f"🔑 Ulvis Alias: {ulvis_alias}")
    
    # 4. Ulvis hit with CORRECT API
    ulvis_result = hit_ulvis(arolink_short, ulvis_alias)
    
    if 'error' in ulvis_result:
        return jsonify({
            "error": "Ulvis mein problem",
            "arolink_url": arolink_short,
            "ulvis_error": ulvis_result
        }), 500
    
    # 5. Final response
    return jsonify({
        "success": True,
        "original_url": original_url,
        "generated_aliases": {
            "arolink_alias": arolink_alias,
            "ulvis_alias": ulvis_alias
        },
        "step_1_arolink": {
            "short_url": arolink_short,
            "expires_in": "30 minutes",
            "full_response": arolink_result
        },
        "step_2_ulvis": {
            "short_url": ulvis_result.get('url'),
            "id": ulvis_result.get('id'),
            "full_response": ulvis_result
        },
        "final_links": {
            "arolink": arolink_short,
            "ulvis": ulvis_result.get('url')
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
            data = response.json()
            print(f"✅ Arolink Response: {data}")
            return data
        else:
            return {"error": f"Status {response.status_code}", "raw": response.text}
    except Exception as e:
        return {"error": str(e)}

def hit_ulvis(url, alias):
    try:
        params = {
            "url": url,  # Arolink ki short URL
            "custom": alias,  # Semy alias
            "private": "1"  # Private URL
        }
        
        # ✅ SAHI API ENDPOINT
        response = requests.get(ULVIS_API, params=params, timeout=10)
        
        print(f"🌐 Ulvis URL: {response.url}")
        
        if response.status_code == 200:
            # Ulvis ka response XML mein aata hai, parse karo
            data = parse_ulvis_response(response.text)
            print(f"✅ Ulvis Response: {data}")
            return data
        else:
            return {"error": f"Status {response.status_code}", "raw": response.text}
    except Exception as e:
        return {"error": str(e)}

def parse_ulvis_response(xml_response):
    """Ulvis ke XML response ko parse karo"""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_response)
        
        success = root.find('success').text
        data = root.find('data')
        
        if success == '1':
            return {
                "success": "1",
                "id": data.find('id').text if data.find('id') is not None else None,
                "url": data.find('url').text if data.find('url') is not None else None,
                "full": data.find('full').text if data.find('full') is not None else None,
                "hits": data.find('hits').text if data.find('hits') is not None else None,
                "status": data.find('status').text if data.find('status') is not None else None,
                "via": data.find('via').text if data.find('via') is not None else None
            }
        else:
            return {"error": "Ulvis API returned failure"}
    except Exception as e:
        return {"error": f"Parse error: {str(e)}", "raw": xml_response}

@app.route('/')
def home():
    return jsonify({
        "service": "URL Shortener Chain - SEMY Edition",
        "how_to_use": "/done?url=YOUR_URL",
        "example": "/done?url=https://google.com",
        "alias_format": "Semy + 3 CAPITAL Letters + 3 Numbers",
        "flow": "Original URL → Arolink (30 min expiry) → Ulvis"
    })

@app.route('/health')
def health():
    return jsonify({"status": "OK", "time": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True)
