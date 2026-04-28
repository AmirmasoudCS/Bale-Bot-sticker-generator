import requests
import time
from io import BytesIO
from PIL import Image
from secrets import BALE_BOT_TOKEN

TOKEN = BALE_BOT_TOKEN
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

offset = 0

# ---------- API HELPERS ----------

def get_updates():
    global offset
    url = f"{BASE_URL}/getUpdates"
    params = {"offset": offset, "timeout": 30}
    return requests.get(url, params=params).json()

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })

def get_file(file_id):
    r = requests.get(f"{BASE_URL}/getFile", params={"file_id": file_id}).json()
    return r["result"]["file_path"]

def download_file(file_path):
    url = f"https://tapi.bale.ai/file/bot{TOKEN}/{file_path}"
    return requests.get(url).content

def send_sticker(chat_id, sticker_bytes):
    url = f"{BASE_URL}/sendSticker"
    files = {
        "sticker": ("sticker.webp", sticker_bytes)
    }
    data = {"chat_id": chat_id}
    requests.post(url, data=data, files=files)

# ---------- IMAGE → STICKER ----------

def convert_to_sticker(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGBA")

    img.thumbnail((512, 512))

    output = BytesIO()
    img.save(output, format="WEBP")
    output.seek(0)

    return output

# ---------- MAIN LOOP ----------

print("✅ Bot is running...")

while True:
    updates = get_updates()

    if updates.get("ok"):
        for update in updates["result"]:
            offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]

            # اگر عکس فرستاده شد
            if "photo" in message:
                photo = message["photo"][-1]
                file_id = photo["file_id"]

                send_message(chat_id, "📸 عکس دریافت شد، در حال ساخت استیکر...")

                try:
                    file_path = get_file(file_id)
                    image_bytes = download_file(file_path)
                    sticker = convert_to_sticker(image_bytes)
                    send_sticker(chat_id, sticker)

                except Exception as e:
                    send_message(chat_id, "❌ خطا در تبدیل عکس")

            else:
                send_message(chat_id, "👋 لطفاً یک عکس بفرست تا برات استیکر بسازم")

    time.sleep(1)
