"""
Keep Alive Server for Replit / PythonAnywhere
Ye bot ko 24/7 chalane ke liye hai
"""

from flask import Flask
from threading import Thread
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Minecraft Bot is Alive! Version 1.21.11"

@app.route('/status')
def status():
    return "running"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("[✓] Keep-alive server started on port 8080")