import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- আপনার দেওয়া ক্রেডেনশিয়াল ও কনফিগারেশন ---
TELEGRAM_BOT_TOKEN = "6941432294:AAHNxdm6YPCtsZ4tZTYCVx8bylxhXRsT0Bw"
TELEGRAM_CHAT_ID = "7504616242"
SITE_URL = "https://ictex.iceiy.com"
EMAIL = "mdg145712@gmail.com"
PASSWORD = "nayem544"

# টাইমফ্রেম ম্যাপিং
TF_MAP = {
    "1m": "60",
    "2m": "120",
    "3m": "180",
    "4m": "240",
    "5m": "300",
    "10m": "600",
    "15m": "900"
}

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
            print(f"Telegram sending error: {e}")
            return {}

def main():
    # অ্যাডমিন প্যানেল থেকে ইনপুট নেওয়া হচ্ছে
    market = input("Enter Market Name (e.g., EUR/USD): ").strip()
    timeframe = input("Enter Timeframe (1m, 2m, 3m, 4m, 5m, 10m, 15m): ").strip().lower()
    direction = input("Enter Direction (BUY / SELL / CALL / PUT / UP / DOWN): ").strip().upper()

    if timeframe not in TF_MAP:
        print("ভুল টাইমফ্রেম সিলেক্ট করা হয়েছে!")
        return

    # ডিরেকশন অনুযায়ী সুন্দর ইমোজি ও ফরম্যাটিং সেট করা
    if direction in ["BUY", "CALL", "UP"]:
        direction_formatted = "🟢 *BUY / CALL (UP)* 📈"
    elif direction in ["SELL", "PUT", "DOWN"]:
        direction_formatted = "🔴 *SELL / PUT (DOWN)* 📉"
    else:
        direction_formatted = f"⚡ *{direction}*"

    # ক্রোম ব্রাউজারের হেডলেস ও সিকিউরিটি অপশন কনফিগারেশন
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--window-size=375,812") 
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1")

    # লোকাল মোবাইল প্রসেসর আর্কিটেকচার ড্রাইভার লোড করা হচ্ছে
    service = Service(executable_path='/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        print("সাইটে প্রবেশ করা হচ্ছে...")
        driver.get(SITE_URL)

        print("লগইন করা হচ্ছে...")
        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        password_input = driver.find_element(By.ID, "login-password")
        
        email_input.send_keys(EMAIL)
        password_input.send_keys(PASSWORD)
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button.btn-submit-auth")
        login_button.click()

        print("ড্যাশবোর্ডের জন্য অপেক্ষা করা হচ্ছে...")
        wait.until(EC.presence_of_element_located((By.ID, "market-selector-btn-new")))
        time.sleep(3) 

        print(f"মার্কেট নির্বাচন করা হচ্ছে: {market}")
        market_btn = driver.find_element(By.ID, "market-selector-btn-new")
        market_btn.click()

        search_input = wait.until(EC.visibility_of_element_located((By.ID, "market-search-input")))
        search_input.clear()
        search_input.send_keys(market)
        time.sleep(2) 

        market_items = driver.find_elements(By.CSS_SELECTOR, ".market-option-item")
        clicked = False
        for item in market_items:
            try:
                name_el = item.find_element(By.CSS_SELECTOR, ".market-info-name")
                if market.lower().replace("/", "") in name_el.text.lower().replace("/", ""):
                    item.click()
                    clicked = True
                    break
            except:
                continue
        
        if not clicked:
            print("সরাসরি নাম মেলেনি, প্রথম মার্কেটটি সিলেক্ট করা হচ্ছে...")
            if market_items:
                market_items[0].click()
            else:
                print("কোনো মার্কেট পাওয়া যায়নি।")
                return

        time.sleep(2)

        # টাইমফ্রেম পরিবর্তন
        print(f"টাইমফ্রেম পরিবর্তন করা হচ্ছে: {timeframe}")
        tf_btn = wait.until(EC.element_to_be_clickable((By.ID, "chart-timeframe-btn")))
        tf_btn.click()

        tf_val = TF_MAP[timeframe]
        tf_option = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[data-timeframe='{tf_val}']")))
        tf_option.click()
        time.sleep(2)

        try:
            driver.execute_script("document.getElementById('chart-display-options-modal').classList.remove('visible')")
        except:
            pass

        print("ক্যান্ডেল লোড হওয়া পর্যন্ত অপেক্ষা করা হচ্ছে...")
        try:
            wait.until(EC.invisibility_of_element_located((By.ID, "chart-loader-overlay")))
        except:
            driver.execute_script("document.getElementById('chart-loader-overlay').style.display = 'none';")

        time.sleep(6) 

        # স্ক্রিনশট নেওয়া
        screenshot_path = "chart_signal.png"
        driver.save_screenshot(screenshot_path)
        print("স্ক্রিনশট নেওয়া সম্পন্ন হয়েছে।")

        # টেলিগ্রামের জন্য সিগন্যাল মেসেজ ফরম্যাটিং
        caption = (
            f"📊 *ICTEX PREMIUM SIGNAL* 📊\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Asset:* {market.upper()}\n"
            f"⏱ *Duration:* {timeframe.upper()}\n"
            f"🚀 *Action:* {direction_formatted}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ _Proper money management ব্যবহার করুন।_"
        )

        print("টেলিগ্রামে সিগন্যাল পাঠানো হচ্ছে...")
        res = send_telegram_photo(screenshot_path, caption)
        if res.get("ok"):
            print("সফলভাবে টেলিগ্রামে সিগন্যাল পাঠানো হয়েছে!")
        else:
            print(f"টেলিগ্রামে পাঠাতে ব্যর্থ হয়েছে: {res}")

    except Exception as e:
        print(f"ত্রুটি ঘটেছে: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()