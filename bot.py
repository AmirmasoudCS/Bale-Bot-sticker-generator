import requests
import time
from io import BytesIO
from PIL import Image
from secrets import BALE_BOT_TOKEN

TOKEN = BALE_BOT_TOKEN
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ------------------ API HELPERS ------------------

def get_updates():
    global offset
    url = f"{BASE_URL}/getUpdates"
    params = {"offset": offset, "timeout": 30}

    try:
        resp = requests.get(url, params=params, timeout=40)
        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.Timeout:
        print("⚠️ Timeout در getUpdates")
        return None

    except requests.exceptions.RequestException as e:
        print(f"⚠️ خطا در getUpdates: {e}")
        return None


def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
    except Exception as e:
        print(f"⚠️ خطا در sendMessage: {e}")


def get_file(file_id):
    try:
        r = requests.get(f"{BASE_URL}/getFile",
                         params={"file_id": file_id},
                         timeout=20).json()
        return r["result"]["file_path"]
    except Exception as e:
        print(f"⚠️ خطا در getFile: {e}")
        return None


def download_file(file_path):
    url = f"https://tapi.bale.ai/file/bot{TOKEN}/{file_path}"

    try:
        return requests.get(url, timeout=40).content
    except Exception as e:
        print(f"⚠️ خطا در download_file: {e}")
        return None


def send_sticker(chat_id, sticker_bytes):
    url = f"{BASE_URL}/sendSticker"

    files = {"sticker": ("sticker.webp", sticker_bytes)}
    data = {"chat_id": chat_id}

    try:
        requests.post(url, data=data, files=files, timeout=40)
    except Exception as e:
        print(f"⚠️ خطا در sendSticker: {e}")


# ------------------ IMAGE → STICKER ------------------

def convert_to_sticker(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGBA")
    img.thumbnail((512, 512))
    output = BytesIO()
    img.save(output, format="WEBP")
    output.seek(0)
    return output


# ------------------ MAIN LOOP ------------------

print("✅ Bot is running...")

while True:
    updates = get_updates()

    if updates is None:
        print("⏳ صبر کردن 5 ثانیه...")
        time.sleep(5)
        continue

    if updates.get("ok"):
        for update in updates["result"]:
            offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]

            if "photo" in message:
                photo = message["photo"][-1]
                file_id = photo["file_id"]

                send_message(chat_id, "📸 عکس دریافت شد، در حال ساخت استیکر...")

                try:
                    file_path = get_file(file_id)
                    if not file_path:
                        send_message(chat_id, "❌ خطا در دریافت فایل")
                        continue

                    image_bytes = download_file(file_path)
                    if not image_bytes:
                        send_message(chat_id, "❌ خطا در دانلود فایل")
                        continue

                    sticker = convert_to_sticker(image_bytes)
                    send_sticker(chat_id, sticker)

                except Exception as e:
                    print(f"❌ خطا: {e}")
                    send_message(chat_id, "❌ مشکلی در ساخت استیکر پیش آمد!")

            else:
                send_message(chat_id, "👋 لطفاً یک عکس بفرست تا برات استیکر بسازم 😊")

    time.sleep(1)
