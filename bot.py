import os
import time
import requests
from PIL import Image, ImageDraw

# --- কনফিগারেশন ---
TELEGRAM_BOT_TOKEN = "6941432294:AAHNxdm6YPCtsZ4tZTYCVx8bylxhXRsT0Bw"
TELEGRAM_CHAT_ID = "7504616242"
FIREBASE_URL = "https://ictex-trade-default-rtdb.firebaseio.com"

# টাইমফ্রেম সেকেন্ডস ম্যাপিং
TF_MAP = {
    "1m": 60,
    "2m": 120,
    "3m": 180,
    "4m": 240,
    "5m": 300,
    "10m": 600,
    "15m": 900
}

# ডাটাবেজ থেকে অ্যাক্টিভ মার্কেট লিস্ট সংগ্রহ করা
def get_active_markets():
    url = f"{FIREBASE_URL}/admin/markets.json"
    try:
        response = requests.get(url)
        data = response.json()
        if not data:
            return []
        
        active_list = []
        for m_id, m_info in data.items():
            if m_info.get("status") == "active":
                active_list.append({
                    "id": m_id,
                    "name": m_info.get("name", m_id),
                    "type": m_info.get("type", "real")
                })
        # নাম অনুযায়ী বর্ণানুক্রমিকভাবে সাজানো
        active_list.sort(key=lambda x: x["name"])
        return active_list
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []

# ১ মিনিটের ক্যান্ডেলকে রিকোয়েস্ট করা টাইমফ্রেমে রূপান্তর করার লজিক
def aggregate_candles(candles, tf_seconds):
    if tf_seconds == 60:
        return candles
        
    aggregated = []
    current_group = []
    
    for c in candles:
        group_start = (c['timestamp'] // (tf_seconds * 1000)) * (tf_seconds * 1000)
        
        if current_group and current_group[0]['timestamp'] != group_start:
            open_p = current_group[0]['open']
            close_p = current_group[-1]['close']
            high_p = max(item['high'] for item in current_group)
            low_p = min(item['low'] for item in current_group)
            
            aggregated.append({
                "timestamp": current_group[0]['timestamp'],
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p
            })
            current_group = []
            
        c_copy = c.copy()
        c_copy['timestamp'] = group_start
        current_group.append(c_copy)
        
    if current_group:
        open_p = current_group[0]['open']
        close_p = current_group[-1]['close']
        high_p = max(item['high'] for item in current_group)
        low_p = min(item['low'] for item in current_group)
        aggregated.append({
            "timestamp": current_group[0]['timestamp'],
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p
        })
        
    return aggregated

# সরাসরি ডাটাবেজ থেকে ক্যান্ডেল ডেটা নিয়ে চার্ট ইমেজ তৈরি করার ফাংশন
def generate_chart_image(market_path, tf_seconds, output_path="chart_signal.png"):
    # রিকোয়েস্ট করা টাইমফ্রেম অনুযায়ী পর্যাপ্ত ক্যান্ডেল নিয়ে আসা (সর্বোচ্চ ৪০টি বার দেখানোর জন্য)
    limit_count = 40 * (tf_seconds // 60)
    url = f"{FIREBASE_URL}/markets/{market_path}/candles/60s.json?orderBy=\"$key\"&limitToLast={limit_count}"
    
    try:
        response = requests.get(url)
        data = response.json()
        if not data:
            return False
        
        raw_candles = [data[key] for key in sorted(data.keys())]
        # ক্যান্ডেলগুলোকে সিলেক্টেড টাইমফ্রেমে কনভার্ট করা
        candles = aggregate_candles(raw_candles, tf_seconds)[-40:]
    except Exception as e:
        print(f"Data fetch error: {e}")
        return False

    # চার্টের সাইজ ও ব্যাকগ্রাউন্ড কালার নির্ধারণ
    w, h = 800, 420
    img = Image.new("RGB", (w, h), "#080B0F")
    draw = ImageDraw.Draw(img)

    padding_right = 90
    padding_top = 40
    padding_bottom = 45
    chart_w = w - padding_right
    chart_h = h - padding_top - padding_bottom

    # সর্বোচ্চ ও সর্বনিম্ন প্রাইস বের করা
    prices = [c['high'] for c in candles] + [c['low'] for c in candles]
    min_p, max_p = min(prices), max(prices)
    p_range = (max_p - min_p) or 0.0001

    # ওপরে নিচে কিছুটা মার্জিন যোগ করা
    min_p -= p_range * 0.1
    max_p += p_range * 0.1
    p_range = max_p - min_p

    # গ্রিড লাইন এবং প্রাইস লেবেল আঁকা
    grid_lines = 5
    for i in range(grid_lines + 1):
        y = padding_top + (i / grid_lines) * chart_h
        price = max_p - (i / grid_lines) * p_range
        draw.line([(0, y), (chart_w, y)], fill="#1C1F26", width=1)
        draw.text((chart_w + 10, y - 6), f"{price:.5f}", fill="#707A8A")

    # ক্যান্ডেলস্টিক আঁকা (সবুজ ও লাল)
    num_candles = len(candles)
    candle_w = chart_w / num_candles
    body_w = candle_w * 0.7

    for i, c in enumerate(candles):
        x = i * candle_w + (candle_w / 2)
        y_open = padding_top + ((max_p - c['open']) / p_range) * chart_h
        y_close = padding_top + ((max_p - c['close']) / p_range) * chart_h
        y_high = padding_top + ((max_p - c['high']) / p_range) * chart_h
        y_low = padding_top + ((max_p - c['low']) / p_range) * chart_h

        color = "#0CCF56" if c['close'] >= c['open'] else "#FF4D5E"

        # শলতে (Wick) আঁকা
        draw.line([(x, y_high), (x, y_low)], fill=color, width=2)

        # বডি (Body) আঁকা
        y1, y2 = min(y_open, y_close), max(y_open, y_close)
        if abs(y1 - y2) < 2:
            y2 = y1 + 2
        draw.rectangle([x - body_w/2, y1, x + body_w/2, y2], fill=color)

    # ইমেজটি সংরক্ষণ করা
    img.save(output_path)
    return True

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'caption': caption,
            'parse_mode': 'Markdown'
        }
        try:
            response = requests.post(url, files=files, data=data)
            return response.json()
        except Exception as e:
            print(f"Telegram error: {e}")
            return {}

def main():
    print("ডাটাবেজ থেকে অ্যাক্টিভ মার্কেট লিস্ট লোড করা হচ্ছে...")
    markets = get_active_markets()
    if not markets:
        print("কোনো অ্যাক্টিভ মার্কেট পাওয়া যায়নি বা কানেকশন এরর!")
        return

    print("\n--- AVAILABLE MARKETS ---")
    for idx, m in enumerate(markets, 1):
        otc_tag = " (OTC)" if m["type"] == "otc" and "(OTC)" not in m["name"] else ""
        print(f"[{idx}] {m['name']}{otc_tag}")

    # কিবোর্ড থেকে সংখ্যা সিলেক্ট করা হচ্ছে
    while True:
        try:
            choice = int(input("\nSelect Market Number: "))
            if 1 <= choice <= len(markets):
                selected_market = markets[choice - 1]
                break
            else:
                print("ভুল সংখ্যা! আবার চেষ্টা করুন।")
        except ValueError:
            print("অনুগ্রহ করে একটি সঠিক সংখ্যা টাইপ করুন।")

    market_name = selected_market["name"]
    market_path = selected_market["id"]
    otc_tag = " (OTC)" if selected_market["type"] == "otc" and "(OTC)" not in market_name else ""
    full_market_display = f"{market_name}{otc_tag}"

    timeframe = input("Enter Timeframe (1m, 2m, 3m, 4m, 5m, 10m, 15m): ").strip().lower()
    direction = input("Enter Direction (BUY / SELL / CALL / PUT): ").strip().upper()

    if timeframe not in TF_MAP:
        print("ভুল টাইমফ্রেম সিলেক্ট করা হয়েছে!")
        return

    tf_seconds = TF_MAP[timeframe]

    # ক্যান্ডেল জেনারেট করা হচ্ছে
    print(f"ডাটাবেজ থেকে '{full_market_display}' এর চার্ট ইমেজ তৈরি করা হচ্ছে...")
    if not generate_chart_image(market_path, tf_seconds):
        print("ডাটাবেজে এই মার্কেটের কোনো ক্যান্ডেল ডেটা পাওয়া যায়নি!")
        return

    if direction in ["BUY", "CALL", "UP"]:
        direction_formatted = "🟢 *BUY / CALL (UP)* 📈"
    elif direction in ["SELL", "PUT", "DOWN"]:
        direction_formatted = "🔴 *SELL / PUT (DOWN)* 📉"
    else:
        direction_formatted = f"⚡ *{direction}*"

    # টেলিগ্রাম মেসেজ সাজানো
    caption = (
        f"📊 *ICTEX PREMIUM SIGNAL* 📊\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Asset:* {full_market_display.upper()}\n"
        f"⏱ *Duration:* {timeframe.upper()}\n"
        f"🚀 *Action:* {direction_formatted}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ _Proper money management ব্যবহার করুন।_"
    )

    print("টেলিগ্রামে সিগন্যাল ও চার্ট পাঠানো হচ্ছে...")
    res = send_telegram_photo("chart_signal.png", caption)
    if res.get("ok"):
        print("সফলভাবে টেলিগ্রামে সিগন্যাল ও চার্ট পাঠানো হয়েছে!")
    else:
        print(f"ব্যর্থ হয়েছে: {res}")

if __name__ == "__main__":
    main()