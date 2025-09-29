import os
import subprocess
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Taxi Bot is running!"

@app.route('/health')
def health():
    return "OK"

def run_bot():
    """Sizning taxi.py bot faylingizni ishga tushiradi"""
    try:
        subprocess.run(["python", "taxi.py"])
    except Exception as e:
        print(f"Bot ishga tushirishda xato: {e}")

if __name__ == '__main__':
    # Botni backgroundda ishga tushirish
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Flask ni ishga tushirish
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
    