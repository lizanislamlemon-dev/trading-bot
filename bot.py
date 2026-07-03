import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont

# --- কনফিগারেশন ---
TELEGRAM_BOT_TOKEN = "6941432294:AAHNxdm6YPCtsZ4tZTYCVx8bylxhXRsT0Bw"
TELEGRAM_CHAT_ID = "7504616242"

# দৃষ্টিনন্দন প্রফেশনাল সিগন্যাল কার্ড (Image) তৈরি করার ফাংশন
def generate_premium_signal_card(market, timeframe, direction, trade_time, output_path="signal_card.png"):
    w, h = 800, 450
    # ডার্ক থিম ব্যাকগ্রাউন্ড
    img = Image.new("RGB", (w, h), "#080B11")
    draw = ImageDraw.Draw(img)

    # ডিরেকশন অনুযায়ী থিম কালার সিলেক্ট (সবুজ অথবা লাল)
    is_up = direction.upper() in ["BUY", "CALL", "UP", "GREEN", "🟢"]
    theme_color = "#0CCF56" if is_up else "#FF4D5E"
    action_text = "CALL / BUY (UP)" if is_up else "PUT / SELL (DOWN)"

    # সিস্টেমে থাকা ডেজাভু ফন্ট লোড করা (ফন্ট সাইজ সুন্দর করার জন্য)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_title = ImageFont.truetype(font_path, 22)
        font_label = ImageFont.truetype(font_path, 15)
        font_value = ImageFont.truetype(font_path, 34)
        font_time = ImageFont.truetype(font_path, 40)
    except:
        font_title = font_label = font_value = font_time = ImageFont.load_default()

    # ১. বাম পাশে প্রফেশনাল কালার বর্ডার আঁকা
    draw.rectangle([0, 0, 18, h], fill=theme_color)

    # ২. চারপাশের সূক্ষ্ম ফ্রেম
    draw.rectangle([40, 25, w - 25, h - 25], outline="#1F2937", width=2)

    # ৩. হেডার টেক্সট
    draw.text((60, 45), "⚡ ICTEX OFFICIAL VIP SIGNAL ⚡", fill="#707A8A", font=font_title)

    # ৪. মার্কেট ইনফো
    draw.text((60, 105), "MARKET / ASSET", fill="#707A8A", font=font_label)
    draw.text((60, 130), market.upper(), fill="#FFFFFF", font=font_value)

    # ৫. টাইমফ্রেম
    draw.text((60, 210), "TIMEFRAME", fill="#707A8A", font=font_label)
    draw.text((60, 235), timeframe.upper(), fill="#3B82F6", font=font_value)

    # ৬. ডিরেকশন / অ্যাকশন
    draw.text((60, 315), "ACTION / DIRECTION", fill="#707A8A", font=font_label)
    draw.text((60, 340), action_text, fill=theme_color, font=font_value)

    # ৭. ট্রেড নেওয়ার সময় (ডানপাশে গোল্ডেন কালার হাইলাইট)
    draw.text((460, 210), "ENTRY TIME (CLOCK)", fill="#707A8A", font=font_label)
    draw.text((460, 235), trade_time.upper(), fill="#FFC107", font=font_time)

    # ৮. কোণায় ইন্ডিকেটর লাইট (গ্লো ইফেক্ট)
    draw.ellipse([w - 65, 45, w - 45, 65], fill=theme_color)

    # ইমেজটি সেভ করা
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
    # অ্যাডমিন প্যানেল থেকে ইনপুট
    market = input("Enter Market Name (e.g., USD/BDT (OTC)): ").strip()
    timeframe = input("Enter Timeframe (e.g., 1m, 5m): ").strip()
    direction = input("Enter Direction (BUY / SELL / CALL / PUT): ").strip().upper()
    trade_time = input("Enter Entry Time (e.g., 10:45 PM): ").strip()

    # ইমেজ কার্ড জেনারেট করা হচ্ছে
    print("সিগন্যাল কার্ড ইমেজ তৈরি করা হচ্ছে...")
    generate_premium_signal_card(market, timeframe, direction, trade_time)

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
        f"⏰ *Entry Time:* {trade_time.upper()}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
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