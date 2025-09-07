import os
import time
import csv
import requests
from lxml import etree
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
import pygetwindow._pygetwindow_win as win_module
import pygetwindow as gw
import platform
import socket
import json
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# ---------------------- CONFIG ------------------------
INPUT_FILE = "input.txt"
HISTORY_FILE = "setup/history.txt"
OUTPUT_CSV = "output.csv"
IMAGES_DIR = "Images"
WAIT_TIME = 10
# ------------------------------------------------------
with open('setup/config.json', 'r') as f:
    config = json.load(f)

main_URL = config.get('URL')
api_key = config.get('API_KEY')
GROUP_NAME = config.get('Group_name')
ORIGIN = config.get('Origin')
print(F"Group name : { GROUP_NAME}, ORIGIN : {ORIGIN}")
# Detect platform
IS_WINDOWS = platform.system() == "Windows"

# Base path of the setup folder (relative to main.py location)
base_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "setup")

# User data dir inside setup folder
# user_data_dir = os.path.join(base_path, "browser8888")
user_data_dir= r"C:\Users\Arifsoft\Desktop\Folders\newproject\browsers\browser8888" 
# Chromedriver path inside setup folder
chrome_driver_filename = "chromedriver.exe" if IS_WINDOWS else "chromedriver"
chrome_driver_path = os.path.join(base_path, chrome_driver_filename)

# Chrome executable finder
def find_chrome_path():
    if IS_WINDOWS:
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
    else:
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/usr/bin/google-chrome"
        ]

    for path in possible_paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("❌ Google Chrome not found on your system.")

# Port check utility
def is_chrome_debugging_running(port):
    """Check if Chrome with remote debugging is already running."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", int(port))) == 0

# Main function to open or connect to Chrome
def open_browser():
    chrome_path = find_chrome_path()
    port = "8888"

    if not is_chrome_debugging_running(port):
        print(f"[INFO] Chrome not running on port {port} — launching it.")
        cmd = [
            chrome_path,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)  # Wait for Chrome to be ready
    else:
        print(f"[INFO] Chrome already running on port {port} — connecting.")

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")

    # Setup WebDriver
    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver
def bring_browser_to_front(driver1):
    title = driver1.title
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        print(f"Window with title '{title}' not found.")
        return

    win = windows[0]

    try:
        if win.isMinimized:
            print("Window is minimized, restoring...")
            win.restore()
            time.sleep(0.5)  # Wait a bit after restoring

        # Activate the window
        win.activate()
        time.sleep(0.2)  # Give a little time to process

        # Optionally maximize or set window size/position if you want full screen
        win.maximize()

    except win_module.PyGetWindowException as e:
        if 'Error code from Windows: 0' in str(e):
            # Ignore this misleading 'success' error
            pass
        else:
            raise
def load_input_url():
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        raise FileNotFoundError("input.txt not found.")

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def save_history(history_set):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.writelines(link + "\n" for link in sorted(history_set))

def store_csv(data):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    file_exists = os.path.exists(OUTPUT_CSV)

    with open(OUTPUT_CSV, mode="a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Link", "Title", "Price", "ModelYear", "Mileage", "Fuel",
                "Transmission", "Body", "Options", "SellerName","location", "Distance", "ImageFilename","Description"
            ])
        for row in data:
            writer.writerow(row)
def scroll_and_focus_cards(driver):
    try:
        # Wait for cards to appear
        cards = driver.find_elements(By.XPATH, '//li[@class="hz-Listing hz-Listing--list-item-cars"]')
        print(f"🔍 Found {len(cards)} cards")

        actions = ActionChains(driver)

        for idx, card in enumerate(cards, 1):
            try:
                # Find the <a> tag inside the card
                a_tag = card.find_element(By.XPATH, './a')
                
                # Scroll into view (smoothly) and move to element
                actions.move_to_element(a_tag).perform()
                time.sleep(1)  # Small wait to let lazy-loaded attributes appear

                # Optional: grab href after focus
                href = a_tag.get_attribute("href")
                print(f"{idx}. ✅ Href loaded: {href}")

            except Exception as e:
                print(f"{idx}. ⚠️ Error focusing card: {e}")
                continue

    except Exception as e:
        print(f"❌ Failed to find or process cards: {e}")
def download_image(url, filename):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(os.path.join(IMAGES_DIR, filename), "wb") as f:
                f.write(response.content)
        time.sleep(2)        
    except Exception as e:
        print(f"Failed to download image: {e}")

def safe_xpath_text(card, xpath_expr):
    try:
        return "".join(card.xpath(xpath_expr)).strip()
    except:
        return ""

def safe_xpath_attr(card, xpath_expr):
    try:
        result = card.xpath(xpath_expr)
        return result[0].strip() if result else ""
    except:
        return ""
def get_distance_duration(origin, destination, api_key):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "key": api_key,
        "language": "nl",  # Dutch
        "units": "metric"
    }

    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print("❌ Failed to get response from API")
        return None

    data = response.json()

    try:
        element = data['rows'][0]['elements'][0]
        if element['status'] != 'OK':
            print("❌ No route found.")
            return None

        distance_text = element['distance']['text']
        duration_text = element['duration']['text']

        return distance_text, duration_text
    except Exception as e:
        print(f"⚠️ Error parsing API response: {e}")
        return None

driver_telegram = open_browser()
bring_browser_to_front(driver_telegram)
driver_telegram.get('https://web.telegram.org/k/')
def send_telegram_post(driver_telegram, data):
    try:
        # Find the message input box (Telegram Web)
        message_box = driver_telegram.find_element(By.CSS_SELECTOR, "div.input-message-input[contenteditable='true']")
        actions = ActionChains(driver_telegram)
        for idx, row in enumerate(data, 1):
            try:
                (
                    link, title, price, model_year, mileage, fuel, transmission,
                    body, options_text, seller_name, location, distance,
                    image_filename, description
                ) = row

                # 📝 Construct the message in your new format
                post = f"""  **{title}**

                        💶 Prijs: **{price}**
                        📍 Locatie: {location}
                        👤 Naam verkoper: {seller_name}
                        📅 Jaar: {model_year}
                        📈 Tellerstand: {mileage}
                        ⛽ Brandstof: {fuel}
                        🕹️ Transmissie: {transmission}
                        🛞 Carrosserie: {body}
                        🚗 Opties: {options_text}
                        🛣️ Afstand: {distance}

                        [🔗 Bekijk de auto]({link})
                        """
                # Clear message box (CTRL+A, Backspace)
                message_box.click()
                actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE).perform()
                time.sleep(0.2)

                # Type and format each line
                for line in post.strip().splitlines():
                    actions.send_keys(line.strip()).perform()
                    actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
                    time.sleep(0.05)

                # Send the message
                time.sleep(5)
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(2)

                print(f"{idx}. ✅ Posted: {title}")

            except Exception as e:
                print(f"{idx}. ⚠️ Failed to send post: {e}")
                continue

    except Exception as e:
        print(f"❌ Failed to send Telegram post: {e}")
def telegram(data):
    if not GROUP_NAME:
        return
    global driver_telegram
    bring_browser_to_front(driver_telegram)
    try:
        search_box = driver_telegram.find_element(By.XPATH, '//div[@class="input-search"]/input')
        search_box.clear()
        search_box.send_keys(GROUP_NAME)
        time.sleep(5)
        driver_telegram.find_element(By.XPATH,'//div[@class="search-group search-group-contacts"]//a[1]').click()
    except:
        return    
    time.sleep(4)  # Wait for Telegram web to fully load

    send_telegram_post(driver_telegram, data)
history = load_history()


def main():
   driver = uc.Chrome()
   bring_browser_to_front(driver)
   driver.get(main_URL)
   while True:
    try:
        bring_browser_to_front(driver)
        driver.refresh()
        time.sleep(10)
        try:
            WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_all_elements_located((By.XPATH, '//li[@class="hz-Listing hz-Listing--list-item-cars"]'))
            )
        except Exception as e:
            print("❌ Error waiting for listings:", e)
            driver.quit()
            return
        scroll_and_focus_cards(driver)
        tree = etree.HTML(driver.page_source)
        cards = tree.xpath('//li[@class="hz-Listing hz-Listing--list-item-cars"]')

        print(f"Found {len(cards)} cards.")
        new_rows = []

        for card in cards:
            try:
                link = safe_xpath_attr(card, './a/@href')
                link=f'https://www.2dehands.be{link}'
                print(f'link is this : {link}')
                if not link or link in history:
                    # print("Link not found or repeating ")
                    # print("=============================================================")
                    continue

                title = safe_xpath_text(card, './/h3//text()')
                price = safe_xpath_text(card, './/div[@class="hz-Listing-price-extended-details"]//text()')
                model_year = safe_xpath_text(card, './/span[i[contains(@class, "hz-SvgIconCarConstructionYear")]]//text()')
                mileage = safe_xpath_text(card, './/span[i[contains(@class, "hz-SvgIconCarMileage")]]//text()')
                fuel = safe_xpath_text(card, './/span[i[contains(@class, "hz-SvgIconCarFuel")]]//text()')
                transmission = safe_xpath_text(card, './/span[i[contains(@class, "hz-SvgIconCarTransmission")]]//text()')
                body = safe_xpath_text(card, './/span[i[contains(@class, "hz-SvgIconCarBody")]]//text()')
                options_text = safe_xpath_text(card, './/div[@class="hz-Listing-attribute-options hz-Text hz-Text--regular u-colorTextSecondary"]//text()')
                seller_name = safe_xpath_text(card, './/span[@class="hz-Listing-sellerName"]//text()')
                location = safe_xpath_text(card, './/div[@class="hz-Listing-sellerLocation u-colorTextSecondary"]/text()')
                distance = safe_xpath_text(card, './/div[@class="hz-Listing-sellerLocation u-colorTextSecondary"]//span//text()')
                image_url = safe_xpath_attr(card, './/figure[@class="hz-Listing-image-container"]//img[1]/@src')
                description=safe_xpath_text(card,'.//p[@class="hz-Listing-description hz-text-paragraph"]//text()')
                ad=safe_xpath_text(card,'.//div[@class="hz-Listing-priority hz-Listing-priority--all-devices"]//text()')
            
                if ad and 'topadvertentie' in ad.lower() or 'topzoekertje' in ad.lower():
                    print("Skiping Add")
                    continue
                # Clean filename
                safe_title = title.replace('/', '-').replace('\\', '-').replace(':', '').strip()
                image_filename = f"{safe_title}.jpg" if safe_title else "unknown.jpg"

                if image_url:
                    try:
                        download_image(image_url, image_filename)
                    except:pass
                if location:    
                    result = get_distance_duration(ORIGIN, location, api_key)
                    if result:
                        distance, duration = result
                        print(f"🛣️ Distance: {distance} 🕒 {duration}")
                        distance=f'{distance} {duration}'    
                row = [
                    link, title, price, model_year, mileage, fuel,
                    transmission, body, options_text, seller_name, location,distance, image_filename,description
                ]
                new_rows.append(row)
                history.add(link)

            except Exception as e:
                print(f"⚠️ Error processing card: {e}")
                continue

        if new_rows:
            store_csv(new_rows)
            save_history(history)
            print(f"✅ Stored {len(new_rows)} new rows.")
            print('Working in telegram now :')
            telegram(new_rows)
        else:
            print("ℹ️ No new cards found.")
            time.sleep(50)
    except:pass  
    try:
        driver.quit()
    except:pass       
if __name__ == "__main__":
    main()
    