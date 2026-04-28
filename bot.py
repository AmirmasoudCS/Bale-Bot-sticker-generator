from flask import Flask, request, jsonify
import requests
from PIL import Image
from io import BytesIO
from secrets import BALE_BOT_TOKEN as Token
app = Flask(__name__)

TOKEN = Token

@app.route('/', methods=['POST'])
def webhook():
    update = request.json
    if 'message' in update:
        msg = update['message']
        if 'file_id' in msg:
            file_id = msg['file_id']
            return jsonify({"status": "received"})
    return jsonify({})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
