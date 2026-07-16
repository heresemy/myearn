from flask import Flask, request, jsonify
import requests
import random
import string
from datetime import datetime, timedelta

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
    service = request.args.get('service', 'isgd')  # Default: isgd
    
    if not original_url:
        return jsonify({
            "error": "URL nahi diya!",
            "example": "/done?url=https://example.com",
            "services": "isgd, vgd, tinyurl, 1ptco"
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
    
    # Step 2: Choose service
    service_functions = {
        'isgd': hit_isgd,
        'vgd': hit_vgd,
        'tinyurl': hit_tinyurl,
        '1ptco': hit_1ptco
    }
    
    hit_func = service_functions.get(service, hit_isgd)
    second_result = hit_func(arolink_short)
    
    if 'error' in second_result:
        return jsonify({
            "error": f"{service} failed",
            "arolink_url": arolink_short,
            "details": second_result
        }), 500
    
    return jsonify({
        "success": True,
        "original_url": original_url,
        "service_used": service,
        "generated_aliases": {
            "arolink": arolink_alias
        },
        "step_1_arolink": {
            "short_url": arolink_short,
            "expires_in": "30 minutes",
            "full_response": arolink_result
        },
        f"step_2_{service}": {
            "short_url": second_result.get('url'),
            "service": second_result.get('service'),
            "full_response": second_result
        },
        "final_links": {
            "arolink": arolink_short,
            "second": second_result.get('url')
        },
        "redirect_info": {
            "both_links_will_redirect": True,
            "arolink_expires": "30 minutes",
            "second_link": "Permanent"
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
    """is.gd - Fastest redirect"""
    try:
        params = {
            "format": "json",
            "url": url
        }
        response = requests.get("https://is.gd/create.php", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'shorturl' in data:
                return {
                    "url": data['shorturl'],
                    "status": "success",
                    "service": "is.gd"
                }
            else:
                return {"error": data.get('error', 'Unknown error')}
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def hit_vgd(url):
    """v.gd"""
    try:
        params = {
            "format": "json",
            "url": url
        }
        response = requests.get("https://v.gd/create.php", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'shorturl' in data:
                return {
                    "url": data['shorturl'],
                    "status": "success",
                    "service": "v.gd"
                }
            else:
                return {"error": data.get('error', 'Unknown error')}
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def hit_tinyurl(url):
    """TinyURL"""
    try:
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
                return {"error": "Invalid response"}
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def hit_1ptco(url):
    """1pt.co"""
    try:
        response = requests.post(
            "https://1pt.co/api/v1/create",
            json={"url": url},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'shortened' in data:
                return {
                    "url": data['shortened'],
                    "status": "success",
                    "service": "1pt.co"
                }
            else:
                return {"error": "Invalid response"}
        else:
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "service": "Double URL Shortener 🚀",
        "flow": "Original URL → Arolink (30 min) → Second Shortener",
        "how_to_use": "/done?url=YOUR_URL&service=isgd",
        "example": "/done?url=https://google.com&service=isgd",
        "services": {
            "isgd": "Fastest redirect (Recommended)",
            "vgd": "is.gd alternative",
            "tinyurl": "Popular & reliable",
            "1ptco": "Short & clean"
        },
        "alias_format": "Semy + 3 CAPITAL Letters + 3 Numbers",
        "features": [
            "✅ All services redirect directly",
            "✅ No API key needed",
            "✅ Arolink expires in 30 minutes",
            "✅ Second link is permanent"
        ]
    })

@app.route('/health')
def health():
    return jsonify({"status": "OK", "time": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True)
