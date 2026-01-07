from flask import Flask, jsonify
from flask_cors import CORS
import threading
import requests
import time
import numpy as np
import csv
import os
from datetime import datetime
from collections import deque
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from xgboost import XGBClassifier

# --- WEBSITE SETTINGS ---
app = Flask(__name__)
CORS(app)  # Ye website ko data lene ki permission dega

# Global variable (Yahan prediction save hogi)
latest_data = {
    "issue": "Connecting...",
    "prediction": "WAITING",
    "confidence": 0,
    "status": "Starting AI...",
    "multiplier": 1
}

# --- OLD AI SETTINGS ---
HISTORY_LEN = 20000 
LEARNING_LIMIT = 2000 
TRAIN_SIZE = 2       
DATA_FILE = "daman_big_data.csv"
base_bet = 30

# --- AI BRAIN (Tumhara Logic) ---
class MultiBrain:
    def __init__(self):
        self.gb_model = GradientBoostingClassifier(n_estimators=100)
        self.rf_model = RandomForestClassifier(n_estimators=100)
        self.xgb_model = XGBClassifier(n_estimators=100, use_label_encoder=False, eval_metric='logloss')
        self.history = deque(maxlen=HISTORY_LEN)
        self.last_prediction = None
        self.multiplier = 1

    def load_memory(self, old_data):
        self.history.extend(old_data)

    def update_recovery(self, actual_size):
        if self.last_prediction:
            if self.last_prediction == actual_size:
                self.multiplier = 1  
            else:
                self.multiplier *= 3  
                if self.multiplier > 81: self.multiplier = 1 

    def predict(self):
        if len(self.history) < 2: return "WAITING", 0, "Learning Data..."

        working_data = list(self.history)[-LEARNING_LIMIT:]
        X, y = [], []
        for i in range(len(working_data) - TRAIN_SIZE):
            X.append(working_data[i : i + TRAIN_SIZE])
            y.append(working_data[i + TRAIN_SIZE])

        X, y = np.array(X), np.array(y)
        last_pattern = np.array(working_data[-TRAIN_SIZE:]).reshape(1, -1)

        try:
            self.gb_model.fit(X, y)
            self.rf_model.fit(X, y)
            self.xgb_model.fit(X, y)

            p1 = self.gb_model.predict(last_pattern)[0]
            p2 = self.rf_model.predict(last_pattern)[0]
            p3 = self.xgb_model.predict(last_pattern)[0]

            votes = p1 + p2 + p3
            final_val = 1 if votes >= 2 else 0
            confidence = (votes / 3) * 100 if final_val == 1 else ((3 - votes) / 3) * 100
            
            status = "⚡ DIRECT TREND"
            if votes == 3 or votes == 0: status = "🔥 SUPER SIGNAL"
            elif confidence < 60: status = "⚠️ UNSTABLE MARKET"

            return ("BIG" if final_val == 1 else "SMALL"), confidence, status
        except:
            return "WAITING", 0, "Calculation Error"

def save_to_csv(issue, number, size):
    # CSV file logic hata diya hai taaki server fast chale
    pass

def load_from_csv():
    # Start fresh for simplicity
    return []

# --- BACKGROUND WORKER ---
def run_bot_logic():
    global latest_data
    bot = MultiBrain()
    # Initial data fetch to fill memory
    print("Bot Started...")
    
    last_issue = ""
    while True:
        try:
            res = requests.get("https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json", timeout=10).json()
            item = res['data']['list'][0]
            issue, num = item['issueNumber'], int(item['number'])

            if issue != last_issue:
                size = "BIG" if num >= 5 else "SMALL"
                bot.history.append(1 if size == "BIG" else 0) # Memory Update
                bot.update_recovery(size)
                
                pred, conf, status = bot.predict()
                bot.last_prediction = pred
                
                # Update Website Data
                latest_data = {
                    "issue": issue,
                    "prediction": pred,
                    "confidence": round(conf, 1),
                    "status": status,
                    "multiplier": bot.multiplier
                }
                print(f"Updated: {issue} -> {pred}")
                last_issue = issue
            
            time.sleep(1)
        except Exception as e:
            print("Error:", e)
            time.sleep(2)

# --- SERVER START ---
@app.route('/get_prediction', methods=['GET'])
def get_pred():
    return jsonify(latest_data)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot_logic)
    t.daemon = True
    t.start()

    app.run(host='0.0.0.0', port=10000)

