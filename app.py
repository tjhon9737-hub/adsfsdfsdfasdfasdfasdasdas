import requests
import re
import random

# List of User-Agents
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
        raise ValueError("❌ Invalid Terabox URL. Please make sure it contains '/s/...' part.")
    return match.group(1)

def get_download_link(share_code, ua):
    # Step 1: Get file info
    info_url = f"https://terabox.hnn.workers.dev/api/get-info-new?shorturl={share_code}&pwd="
    headers = {
        "host": "terabox.hnn.workers.dev",
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
        raise Exception(f"❌ Info request failed: {resp1.status_code}")

    data = resp1.json()
    if "errno" in data and data["errno"] != 0:
        raise Exception(f"❌ API Error: {data.get('errmsg', 'Unknown error')}")

    # Extract required fields
    shareid = data.get("shareid")
    uk = data.get("uk")
    sign = data.get("sign")
    timestamp = data.get("timestamp")
    file_list = data.get("list", [])
    if not file_list:
        raise Exception("❌ No files found in the share.")
    
    fs_id = file_list[0].get("fs_id")
    if not all([shareid, uk, sign, timestamp, fs_id]):
        raise Exception("❌ Missing required file metadata.")

    # Step 2: Get download link
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
        raise Exception(f"❌ Download request failed: {resp2.status_code}")

    try:
        result = resp2.json()
        download_link = result.get("downloadLink")
        if download_link:
            return download_link
        else:
            raise Exception("❌ 'downloadLink' not found in response.")
    except ValueError:
        # Fallback regex if not valid JSON
        match = re.search(r'"downloadLink":"(.*?)"', resp2.text)
        if match:
            return match.group(1).replace(r"\/", "/")
        else:
            raise Exception("❌ Could not parse download link.")

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

if __name__ == "__main__":
    main()