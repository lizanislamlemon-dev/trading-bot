import os
import time
import json
import requests
from PIL import Image, ImageDraw, ImageFont

# --- কনফিগারেশন ---
TELEGRAM_BOT_TOKEN = "6941432294:AAHNxdm6YPCtsZ4tZTYCVx8bylxhXRsT0Bw"
TELEGRAM_CHAT_ID = "7504616242"
SITE_URL = "https://ictex.iceiy.com"

# প্রিমিয়াম নিয়ন থিমযুক্ত সিগন্যাল কার্ড (Image) তৈরি করার ফাংশন
def generate_premium_signal_card(market, timeframe, direction, trade_time, output_path="signal_card.png"):
    w, h = 800, 480
    # প্রিমিয়াম ডার্ক থিম ব্যাকগ্রাউন্ড
    img = Image.new("RGB", (w, h), "#070B12")
    draw = ImageDraw.Draw(img)

    # নিয়ন কালার থিম নির্ধারণ
    is_up = direction.upper() in ["BUY", "CALL", "UP", "GREEN", "🟢"]
    theme_color = "#00E676" if is_up else "#FF1744"  # নিয়ন গ্রিন অথবা নিয়ন রেড
    action_text = "CALL / BUY (UP)" if is_up else "PUT / SELL (DOWN)"

    # সিস্টেমে থাকা ডেজাভু ফন্ট লোড করা
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_title = ImageFont.truetype(font_path, 24)
        font_label = ImageFont.truetype(font_path, 13)
        font_value = ImageFont.truetype(font_path, 30)
        font_time = ImageFont.truetype(font_path, 42)
        font_footer = ImageFont.truetype(font_path, 12)
    except:
        font_title = font_label = font_value = font_time = font_footer = ImageFont.load_default()

    # ১. বাম পাশে নিয়ন কালার স্ট্রিপ আঁকা
    draw.rectangle([0, 0, 16, h], fill=theme_color)

    # ২. চারপাশের সূক্ষ্ম ডাবল ফ্রেম
    draw.rounded_rectangle([45, 30, w - 30, h - 30], radius=15, outline="#1E293B", width=3)

    # ৩. হেডার টাইটেল
    draw.text((70, 50), "🏆 IX BROKER VIP SIGNAL 🏆", fill="#94A3B8", font=font_title)

    # ৪. গ্লাস ইফেক্ট সাব-প্যানেল (বাম পাশের প্যারামিটার বক্স)
    draw.rounded_rectangle([70, 100, 420, 390], radius=10, fill="#0F172A", outline="#1E293B", width=2)
    
    # ৫. গ্লাস ইফেক্ট সাব-প্যানেল (ডান পাশের টাইম বক্স)
    draw.rounded_rectangle([450, 100, w - 60, 390], radius=10, fill="#0F172A", outline="#1E293B", width=2)

    # বাম প্যানেলের টেক্সট রেন্ডারিং
    # মার্কেট নাম
    draw.text((90, 120), "MARKET / ASSET", fill="#64748B", font=font_label)
    draw.text((90, 145), market.upper(), fill="#FFFFFF", font=font_value)

    # টাইমফ্রেম
    draw.text((90, 210), "TIMEFRAME / DURATION", fill="#64748B", font=font_label)
    draw.text((90, 235), timeframe.upper(), fill="#38BDF8", font=font_value)

    # ডিরেকশন
    draw.text((90, 300), "ACTION / DIRECTION", fill="#64748B", font=font_label)
    draw.text((90, 325), action_text, fill=theme_color, font=font_value)

    # ডান প্যানেলের টেক্সট রেন্ডারিং (ট্রেড নেওয়ার সময়)
    draw.text((480, 180), "ENTRY TIME (CLOCK)", fill="#64748B", font=font_label)
    draw.text((480, 210), trade_time.upper(), fill="#FBBF24", font=font_time)

    # ডান কোণায় ইন্ডিকেটর গ্লো লাইট
    draw.ellipse([w - 95, 52, w - 75, 72], fill=theme_color)

    # ৯. ওয়াটারমার্ক সিগনেচার
    draw.text((70, h - 22), "Bot by: KING VIP TRADER | @kingviptrader", fill="#475569", font=font_footer)

    img.save(output_path)
    return True

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    # ওয়ান-ক্লিক লিংক ওপেন করার জন্য ইনলাইন কিবোর্ড বাটন পে-লোড তৈরি
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🌐 Open IX Broker 🌐", "url": SITE_URL}
            ]
        ]
    }
    
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'caption': caption,
            'parse_mode': 'Markdown',
            'reply_markup': json.dumps(reply_markup)  # JSON টেক্সট হিসেবে পাঠাতে হবে
        }
        try:
            response = requests.post(url, files=files, data=data)
            return response.json()
        except Exception as e:
            print(f"Telegram error: {e}")
            return {}

def main():
    # অ্যাডমিন ইনপুট
    market = input("Enter Market Name (e.g., USD/BDT (OTC)): ").strip()
    timeframe = input("Enter Timeframe (e.g., 1m, 5m): ").strip()
    direction = input("Enter Direction (BUY / SELL / CALL / PUT): ").strip().upper()
    trade_time = input("Enter Entry Time (e.g., 10:45 PM): ").strip()

    # প্রফেশনাল ইমেজ জেনারেট করা হচ্ছে
    print("প্রিমিয়াম সিগন্যাল কার্ড ইমেজ তৈরি করা হচ্ছে...")
    generate_premium_signal_card(market, timeframe, direction, trade_time)

    if direction in ["BUY", "CALL", "UP"]:
        direction_formatted = "🟢 *BUY / CALL (UP)* 📈"
    elif direction in ["SELL", "PUT", "DOWN"]:
        direction_formatted = "🔴 *SELL / PUT (DOWN)* 📉"
    else:
        direction_formatted = f"⚡ *{direction}*"

    # টেলিগ্রামের জন্য আকর্ষণীয় মেসেজ ক্যাপশন সাজানো
    caption = (
        f"📊 *IX BROKER PREMIUM SIGNAL* 📊\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Asset:* {market.upper()}\n"
        f"⏱ *Duration:* {timeframe.upper()}\n"
        f"🚀 *Action:* {direction_formatted}\n"
        f"⏰ *Entry Time:* {trade_time.upper()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Bot by:* KING VIP TRADER | @kingviptrader\n"
        f"⚠️ _Proper money management ব্যবহার করুন।_"
    )

    print("টেলিগ্রামে সিগন্যাল ও কার্ড পাঠানো হচ্ছে...")
    res = send_telegram_photo("signal_card.png", caption)
    if res.get("ok"):
        print("সফলভাবে টেলিগ্রামে সিগন্যাল ও কার্ড পাঠানো হয়েছে!")
    else:
        print(f"ব্যর্থ হয়েছে: {res}")

if __name__ == "__main__":
    main()