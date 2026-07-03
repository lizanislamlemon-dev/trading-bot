import os
import time
import json
import re
import requests
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "6941432294:AAHNxdm6YPCtsZ4tZTYCVx8bylxhXRsT0Bw"
TELEGRAM_CHAT_ID = "7504616242"
SITE_URL = "https://ictex.iceiy.com"

# মাল্টি-চ্যানেল ব্রডকাস্ট লিস্ট
TELEGRAM_CHAT_IDS = [
    "@king_vip_trader",
]

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

# মার্কেট আইডিকে ডাটাবেজ পাথে রূপান্তর করার ফাংশন
def get_market_path(market_id):
    cleaned = re.sub(r'[\.\/ ]', '-', market_id)
    return cleaned.lower()

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

# প্রিমিয়াম ড্যাশবোর্ড থিমযুক্ত সিগন্যাল কার্ড (Image) তৈরি করার ফাংশন
def generate_premium_signal_card(market, timeframe, direction, trade_time, output_path="signal_card.png"):
    w, h = 800, 480
    # Obsidian dark high-tech background
    img = Image.new("RGB", (w, h), "#080B10")
    draw = ImageDraw.Draw(img, "RGBA")

    # নিয়ন কালার থিম নির্ধারণ
    is_up = direction.upper() in ["BUY", "CALL", "UP", "GREEN", "🟢"]
    theme_color = "#00E676"  # Electric Neon Green
    if not is_up:
        theme_color = "#FF1744"  # Electric Neon Red

    action_text = "CALL / BUY (UP)" if is_up else "PUT / SELL (DOWN)"

    # Loading system fonts
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_status = ImageFont.truetype(font_path, 11)
        font_title = ImageFont.truetype(font_path, 25)
        font_label = ImageFont.truetype(font_path, 12)
        font_value = ImageFont.truetype(font_path, 28)
        font_time = ImageFont.truetype(font_path, 46)
        font_footer = ImageFont.truetype(font_path, 11)
    except:
        font_status = font_title = font_label = font_value = font_time = font_footer = ImageFont.load_default()

    # ১. প্রধান ফ্রেম বর্ডার আঁকা
    draw.rounded_rectangle([30, 30, w - 30, h - 30], radius=18, outline="#1E293B", width=2)

    # ২. ওপরের ছোট স্ট্যাটাস বার
    draw.rounded_rectangle([60, 45, 260, 70], radius=8, fill=(30, 41, 59, 150), outline="#334155", width=1)
    draw.ellipse([75, 55, 83, 63], fill=theme_color)
    draw.text((95, 51), "SIGNAL TERMINAL", fill="#94A3B8", font=font_status)

    # ৩. প্রধান শিরোনাম
    draw.text((290, 43), "IX BROKER VIP SIGNAL", fill="#FFFFFF", font=font_title)

    # ৪. সুবিন্যস্ত ট্রেডিং ড্যাশবোর্ড বক্সসমূহ (SaaS Panel Layout)
    # ক) অ্যাসেট বক্স
    draw.rounded_rectangle([60, 95, 430, 195], radius=12, fill=(22, 27, 34, 240), outline="#1F2937", width=1)
    draw.text((85, 112), "ASSET NAME", fill="#57606A", font=font_label)
    draw.text((85, 137), market.upper(), fill="#F0F6FC", font=font_value)

    # খ) ডিউরেশন বক্স
    draw.rounded_rectangle([60, 210, 430, 310], radius=12, fill=(22, 27, 34, 240), outline="#1F2937", width=1)
    draw.text((85, 227), "TRADE DURATION", fill="#57606A", font=font_label)
    draw.text((85, 252), f"⏳ {timeframe.upper()}", fill="#B6C4FF", font=font_value)

    # গ) অ্যাকশন বক্স (থিম কালার নিয়ন আউটলাইন সহ)
    draw.rounded_rectangle([60, 325, 430, 425], radius=12, fill=(22, 27, 34, 240), outline=theme_color, width=2)
    draw.text((85, 342), "EXPECTED ACTION", fill="#57606A", font=font_label)
    draw.text((85, 367), action_text, fill=theme_color, font=font_value)

    # ঘ) ক্লক প্যানেল বক্স (ডান পাশের বক্স)
    draw.rounded_rectangle([455, 95, w - 60, 425], radius=12, fill=(13, 17, 23, 240), outline="#1F2937", width=1)
    draw.text((490, 160), "ENTRY CLOCK TIME", fill="#57606A", font=font_label)
    draw.text((490, 210), trade_time.upper(), fill="#FBBF24", font=font_time)

    # ৫. নিচে ওয়াটারমার্ক সিগনেচার
    draw.text((60, h - 22), "BOT BY: KING VIP TRADER | @king_vip_trader", fill="#475569", font=font_footer)

    img.save(output_path)
    return True

# সব চ্যানেলে একসঙ্গে সিগন্যাল পাঠানোর ফাংশন
def broadcast_telegram_photo(photo_path, caption):
    sent_messages = []
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "💎 ──── OPEN IX BROKER ──── 💎", "url": SITE_URL}
            ]
        ]
    }
    
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'Markdown',
                'reply_markup': json.dumps(reply_markup)
            }
            try:
                response = requests.post(url, files=files, data=data)
                res_json = response.json()
                if res_json.get("ok"):
                    sent_messages.append({
                        "chat_id": chat_id,
                        "message_id": res_json["result"]["message_id"]
                    })
                    print(f"Signal sent to channel: {chat_id}")
                else:
                    print(f"Failed to send to {chat_id}: {res_json}")
            except Exception as e:
                print(f"Telegram error on {chat_id}: {e}")
                
    return sent_messages

# সব চ্যানেলের নির্দিষ্ট মেসেজে রিপ্লাই আকারে রেজাল্ট পাঠানোর ফাংশন
def broadcast_telegram_result(text, sent_messages):
    for msg in sent_messages:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': msg["chat_id"],
            'text': text,
            'parse_mode': 'Markdown',
            'reply_to_message_id': msg["message_id"]
        }
        try:
            response = requests.post(url, json=payload)
            res_json = response.json()
            if res_json.get("ok"):
                print(f"Result posted to channel: {msg['chat_id']}")
            else:
                print(f"Failed to post result to {msg['chat_id']}: {res_json}")
        except Exception as e:
            print(f"Error sending result to {msg['chat_id']}: {e}")

def get_signal_inputs():
    import re
    while True:
        print("\n========================================")
        print("          IX BROKER SIGNAL SETUP        ")
        print("========================================")
        print("[1] REAL Market")
        print("[2] OTC Market")
        market_choice = input("Select Market Type (1/2): ").strip()
        
        market = input("Enter Market Name (e.g., EUR/USD): ").strip()
        
        # Auto-append (OTC) if type is selected as OTC
        if market_choice == "2":
            if not market.upper().endswith("(OTC)"):
                market = f"{market} (OTC)"
                
        timeframe = input("Enter Timeframe (e.g., 1m, 5m): ").strip()
        direction = input("Enter Direction (BUY/SELL/CALL/PUT): ").strip().upper()
        trade_time = input("Enter Entry Time (e.g., 10:45 PM): ").strip()

        # Input confirmation screen
        print("\n----------------------------------------")
        print("         CONFIRM SIGNAL DETAILS         ")
        print("----------------------------------------")
        print(f"Market:     {market.upper()}")
        print(f"Timeframe:  {timeframe.upper()}")
        print(f"Direction:  {direction}")
        print(f"Entry Time: {trade_time.upper()}")
        print("----------------------------------------")
        print("[1] Confirm & Send Signal")
        print("[2] Reset / Create New Signal")
        
        confirm = input("Select Option (1/2): ").strip()
        if confirm == "1":
            return market, timeframe, direction, trade_time
        else:
            print("\nResetting inputs, please enter details again...")

def handle_result_reporting(sent_messages, market):
    print("\n========================================")
    print("             REPORT RESULT              ")
    print("========================================")
    print("[1] DIRECT WIN (1000% SURESHOT NON MTG)")
    print("[2] MTG 1 WIN (SURESHOT MTG 1)")
    print("[3] LOSS (OTM)")
    print("[4] REFUND (PUSH)")
    print("[5] Skip Result")
    choice = input("Select Result (1/2/3/4/5): ").strip()
    
    if choice == "5":
        print("Result reporting skipped.")
        return

    if choice == "1":
        result_text = (
            f"🏆 *1000% SURESHOT NON MTG* 🏆\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Asset:* {market.upper()}\n"
            f"📊 *Result:* ✅ *DIRECT WIN!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 *Channel:* KING VIP TRADER\n"
            f"👑 *Owner:* @king_vip_trader"
        )
    elif choice == "2":
        result_text = (
            f"🏆 *SURESHOT MTG 1* 🏆\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Asset:* {market.upper()}\n"
            f"📊 *Result:* ✅ *MTG 1 WIN!*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 *Channel:* KING VIP TRADER\n"
            f"👑 *Owner:* @king_vip_trader"
        )
    elif choice == "3":
        result_text = (
            f"🛑 *OTM (LOSS)* 🛑\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Asset:* {market.upper()}\n"
            f"📊 *Result:* ❌ *LOSS*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 *Channel:* KING VIP TRADER\n"
            f"👑 *Owner:* @king_vip_trader"
        )
    elif choice == "4":
        result_text = (
            f"🔄 *TRADE REFUND (PUSH)* 🔄\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Asset:* {market.upper()}\n"
            f"📊 *Result:* 🤝 *REFUND*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 *Channel:* KING VIP TRADER\n"
            f"👑 *Owner:* @king_vip_trader"
        )
    else:
        print("Invalid choice, result skipped.")
        return

    print("Sending result response to all channels...")
    broadcast_telegram_result(result_text, sent_messages)

def main():
    market, timeframe, direction, trade_time = get_signal_inputs()

    # Generating the premium Neon Signal Card
    print("\nGenerating premium Signal Card...")
    generate_premium_signal_card(market, timeframe, direction, trade_time)

    # Format Direction for Telegram Caption
    if direction in ["BUY", "CALL", "UP"]:
        direction_formatted = "🟢 *BUY / CALL (UP)* 📈"
    elif direction in ["SELL", "PUT", "DOWN"]:
        direction_formatted = "🔴 *SELL / PUT (DOWN)* 📉"
    else:
        direction_formatted = f"⚡ *{direction}*"

    # Styled Telegram Caption (রিপ্লেসমেন্ট সম্পন্ন)
    caption = (
        f"📊 *IX BROKER PREMIUM SIGNAL* 📊\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Asset:* {market.upper()}\n"
        f"⏱ *Duration:* {timeframe.upper()}\n"
        f"🚀 *Action:* {direction_formatted}\n"
        f"⏰ *Entry Time:* {trade_time.upper()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 *Channel:* KING VIP TRADER\n"
        f"👑 *Owner ID:* @king_vip_trader\n"
        f"⚠️ _Proper money management is advised._"
    )

    print("Sending signal card to Telegram channels...")
    sent_messages = broadcast_telegram_photo("signal_card.png", caption)
    
    if sent_messages:
        print("Signals sent successfully to all active channels!")
        # Open Result Flow
        handle_result_reporting(sent_messages, market)
    else:
        print("Failed to send signals. Please ensure the bot is an Admin in the specified channels.")

if __name__ == "__main__":
    main()