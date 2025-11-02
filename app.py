from flask import Flask, request, jsonify
import requests
import re
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
]

def get_random_ua():
    return random.choice(USER_AGENTS)

def extract_share_code(url):
    match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
    if not match:
        raise ValueError("Invalid Terabox URL. Must contain '/s/...'")
    return match.group(1)

def get_download_link(share_code, ua):
    info_url = f"https://terabox.hnn.workers.dev/api/get-info-new?shorturl={share_code}&pwd="
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=1, i",
        "referer": "https://terabox.hnn.workers.dev/",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": ua
    }

    resp1 = requests.get(info_url, headers=headers)
    if resp1.status_code != 200:
        raise Exception(f"Info request failed: {resp1.status_code}")
    
    data = resp1.json()
    if data.get("errno", 0) != 0:
        raise Exception(f"API Error: {data.get('errmsg', 'Unknown')}")

    file_list = data.get("list", [])
    if not file_list:
        raise Exception("No files found.")
    
    fs_id = file_list[0]["fs_id"]
    shareid = data["shareid"]
    uk = data["uk"]
    sign = data["sign"]
    timestamp = data["timestamp"]

    download_url = "https://terabox.hnn.workers.dev/api/get-downloadp"
    payload = {
        "shareid": shareid,
        "uk": uk,
        "sign": sign,
        "timestamp": timestamp,
        "fs_id": fs_id
    }
    headers["origin"] = "https://terabox.hnn.workers.dev"
    headers["content-type"] = "application/json"

    resp2 = requests.post(download_url, json=payload, headers=headers)
    if resp2.status_code != 200:
        raise Exception(f"Download request failed: {resp2.status_code}")

    result = resp2.json()
    download_link = result.get("downloadLink")
    if not download_link:
        raise Exception("Download link not found.")
    return download_link

# --- Flask API ---
app = Flask(__name__)

@app.route('/get-link', methods=['GET'])
def api_get_link():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' query parameter"}), 400
    
    try:
        share_code = extract_share_code(url)
        ua = get_random_ua()
        link = get_download_link(share_code, ua)
        return jsonify({"success": True, "download_link": link})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/', methods=['GET'])
def home():
    return '''
    <h2>Terabox Direct Link Resolver</h2>
    <p>Use: <code>/get-link?url=YOUR_TERABOX_URL</code></p>
    <form action="/get-link" method="get">
        <input type="text" name="url" placeholder="Paste Terabox URL" size="60" required>
        <button type="submit">Get Direct Link</button>
    </form>
    '''

# ONLY run the interactive CLI when run locally (NOT on Render)
if __name__ == '__main__':
    # Check if running in a terminal (local dev)
    import sys
    if sys.stdin.isatty():
        # Local mode: run interactive CLI
        def main():
            print("🔗 Terabox Direct Link Generator")
            print("📌 Supported format: https://teraboxlink.com/s/18Csd4bznvs0e6RPoIYKKnQ")
            print("-" * 60)
            while True:
                user_url = input("\nEnter Terabox URL (or 'q' to quit): ").strip()
                if user_url.lower() == 'q':
                    print("👋 Goodbye!")
                    break
                if not user_url:
                    print("⚠️  Please enter a valid URL.")
                    continue
                try:
                    share_code = extract_share_code(user_url)
                    print(f"✅ Extracted code: {share_code}")
                    ua = get_random_ua()
                    print("📡 Fetching download link...")
                    link = get_download_link(share_code, ua)
                    print("\n✅ Direct Download Link:")
                    print(link)
                except Exception as e:
                    print(f"\n❌ Error: {e}")
        main()
    else:
        # Server mode: start Flask (this runs on Render)
        app.run(host='0.0.0.0', port=8000)