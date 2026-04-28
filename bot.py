import time
import requests
from io import BytesIO
from PIL import Image
from rembg import remove
from secrets import BALE_BOT_TOKEN

class BaleAPI:
    """Handles all raw API calls to Bale."""
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://tapi.bale.ai/bot{token}"
        self.file_url = f"https://tapi.bale.ai/file/bot{token}"
        self.session = requests.Session() # Reuse connection for speed

    def get_updates(self, offset, timeout=30):
        url = f"{self.base_url}/getUpdates"
        params = {"offset": offset, "timeout": timeout}
        try:
            resp = self.session.get(url, params=params, timeout=timeout + 10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"⚠️ get_updates error: {e}")
            return None

    def send_message(self, chat_id, text, reply_markup=None):
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            self.session.post(url, json=payload, timeout=15)
        except Exception as e:
            print(f"⚠️ send_message error: {e}")

    def get_file_path(self, file_id):
        url = f"{self.base_url}/getFile"
        try:
            resp = self.session.get(url, params={"file_id": file_id}, timeout=20)
            return resp.json().get("result", {}).get("file_path")
        except Exception as e:
            print(f"⚠️ get_file_path error: {e}")
            return None

    def download_file(self, file_path):
        url = f"{self.file_url}/{file_path}"
        try:
            resp = self.session.get(url, timeout=40)
            return resp.content
        except Exception as e:
            print(f"⚠️ download_file error: {e}")
            return None

    def send_sticker(self, chat_id, sticker_bytes):
        url = f"{self.base_url}/sendSticker"
        files = {"sticker": ("sticker.webp", sticker_bytes, "image/webp")}
        data = {"chat_id": chat_id}
        try:
            self.session.post(url, data=data, files=files, timeout=40)
        except Exception as e:
            print(f"⚠️ send_sticker error: {e}")


class StickerProcessor:
    """Handles image processing logic."""
    
    @staticmethod
    def _create_canvas(img):
        """Helper to center image on 512x512 transparent canvas."""
        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        img.thumbnail((512, 512))
        x = (512 - img.width) // 2
        y = (512 - img.height) // 2
        canvas.paste(img, (x, y), img if img.mode == 'RGBA' else None)
        
        output = BytesIO()
        canvas.save(output, format="WEBP")
        output.seek(0)
        return output.getvalue()

    def convert_normal(self, image_bytes):
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        return self._create_canvas(img)

    def convert_remove_bg(self, image_bytes):
        img = Image.open(BytesIO(image_bytes))
        no_bg = remove(img)
        img = Image.open(BytesIO(no_bg_bytes)).convert("RGBA")
        return self._create_canvas(img)


class BaleStickerBot:
    """The main Bot class that ties everything together."""
    def __init__(self, token):
        self.api = BaleAPI(token)
        self.processor = StickerProcessor()
        self.offset = 0
        self.user_modes = {} # chat_id -> mode_name

    def handle_message(self, message):
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        # 1. Handle Commands
        if text.startswith("/start"):
            self.api.send_message(chat_id, "👋 Welcome! Send me a photo to make a sticker.")
            return

        if text.startswith("/mode"):
            # We will implement button selection here later
            self.api.send_message(chat_id, "Current modes: normal, remove_bg")
            return

        # 2. Handle Photos
        if "photo" in message:
            self.process_photo_message(chat_id, message["photo"][-1])
        else:
            self.api.send_message(chat_id, "Please send a photo! 📸")

    def process_photo_message(self, chat_id, photo_data):
        self.api.send_message(chat_id, "⏳ Processing your sticker...")
        
        file_id = photo_data["file_id"]
        file_path = self.api.get_file_path(file_id)
        
        if not file_path:
            self.api.send_message(chat_id, "❌ Could not get file path.")
            return

        image_bytes = self.api.download_file(file_path)
        if not image_bytes:
            self.api.send_message(chat_id, "❌ Could not download image.")
            return

        # Determine mode (default to normal)
        mode = self.user_modes.get(chat_id, "remove_bg") # Defaulting to remove_bg for now

        try:
            if mode == "remove_bg":
                sticker_bytes = self.processor.convert_remove_bg(image_bytes)
            else:
                sticker_bytes = self.processor.convert_normal(image_bytes)

            self.api.send_sticker(chat_id, sticker_bytes)
        except Exception as e:
            print(f"Error in processing: {e}")
            self.api.send_message(chat_id, "❌ Processing failed.")

    def run(self):
        print("🚀 Bot is running (OOP Mode)...")
        while True:
            updates = self.api.get_updates(self.offset)
            
            if updates and updates.get("ok"):
                for update in updates["result"]:
                    self.offset = update["update_id"] + 1
                    if "message" in update:
                        self.handle_message(update["message"])
            
            time.sleep(1)

# ------------------ START THE BOT ------------------
if __name__ == "__main__":
    bot = BaleStickerBot(BALE_BOT_TOKEN)
    bot.run()
