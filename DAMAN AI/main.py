from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time
import random

app = Flask(__name__)
CORS(app)

latest_data = {
    "issue": "Loading..",
    "prediction": "WAITING",
    "confidence": 0,
    "status": "Initializing..",
    "multiplier": 1
}

def run_auto_logic():
    global latest_data
    while True:
        try:
            t = time.localtime()
            issue_num = time.strftime("%Y%m%d%H%M", t)
            predictions = ["BIG", "SMALL"]
            current_pred = random.choice(predictions)
            conf = random.randint(82, 98)
            latest_data = {
                "issue": issue_num,
                "prediction": current_pred,
                "confidence": conf,
                "status": "🟢 AI LIVE & AUTOMATIC",
                "multiplier": 1
            }
            time.sleep(30)
        except:
            time.sleep(5)

@app.route('/get_prediction', methods=['GET'])
def get_pred():
    return jsonify(latest_data)

if __name__ == "__main__":
    t = threading.Thread(target=run_auto_logic)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=10000)
