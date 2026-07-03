import os
import time
import requests
from PIL import Image, ImageDraw

# --- কনফিগারেশন ---
TELEGRAM_BOT_TOKEN = "6941432294:AAHNxdm6YPCtsZ4tZTYCVx8bylxhXRsT0Bw"
TELEGRAM_CHAT_ID = "7504616242"
FIREBASE_URL = "https://ictex-trade-default-rtdb.firebaseio.com"

# মার্কেট আইডিকে ডাটাবেজ পাথে রূপান্তর করার ফাংশন (আপনার সার্ভার ফাইল অনুযায়ী)
def get_market_path(market_id):
    return String_clean(market_id).replace(".", "-").replace("/", "-").replace(" ", "-").lower()

def String_clean(val):
    return str(val) if val is not None else ""

# সরাসরি ডাটাবেজ থেকে ক্যান্ডেল ডেটা নিয়ে চার্ট ইমেজ তৈরি করার ফাংশন
def generate_chart_image(market_path, output_path="chart_signal.png"):
    # ফায়ারবেস থেকে শেষ ৪০টি ক্যান্ডেল রিড করা হচ্ছে
    url = f"{FIREBASE_URL}/markets/{market_path}/candles/60s.json?orderBy=\"$key\"&limitToLast=40"
    try:
        response = requests.get(url)
        data = response.json()
        if not data:
            return False
        
        # টাইমস্ট্যাম্প অনুযায়ী ক্যান্ডেল সাজানো
        candles = [data[key] for key in sorted(data.keys())]
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
    market = input("Enter Market Name (e.g., USD/BDT (OTC)): ").strip()
    timeframe = input("Enter Timeframe (e.g., 1m, 5m): ").strip()
    direction = input("Enter Direction (BUY / SELL / CALL / PUT): ").strip().upper()

    # ডাটাবেজ পাথ তৈরি
    market_path = get_market_path(market)

    # চার্ট জেনারেট করা হচ্ছে
    print("ডাটাবেজ থেকে চার্ট ইমেজ তৈরি করা হচ্ছে...")
    if not generate_chart_image(market_path):
        print("ভুল মার্কেট নাম দেওয়া হয়েছে অথবা ডাটাবেজে এই মার্কেটের কোনো ডেটা নেই!")
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
        f"🎯 *Asset:* {market.upper()}\n"
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