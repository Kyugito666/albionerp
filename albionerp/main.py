from flask import Flask, request, jsonify, send_file, render_template
import os
import json # Tetap di-import kalau ada fallback, tapi kita prioritas orjson
import orjson
import threading
import copy
import time
import queue
from datetime import datetime, timedelta

from core.calculator import execute_calculation
from core.ingestor import process_ingest_data
from core.logistics import build_manifest
from core.adc_client import fetch_and_merge_adc

app = Flask(__name__)
CONFIG_FILE    = "config.json"
PRICES_FILE    = "prices.json"
DB_FILE        = "database/db_gear.json"
VOLUME_FILE    = "volume_history.json"
CHECKLIST_FILE = "checklist.json"
LOGS_FILE      = "logs.json"

ENCHANTS      = [".0", ".1", ".2", ".3", ".4"]
TIERS         = [3, 4, 5, 6, 7, 8]
ALL_CITIES    = ["Lymhurst", "Fort Sterling", "Thetford", "Martlock", "Bridgewatch", "Caerleon", "Brecilien", "Black Market"]
JOURNAL_TYPES = ["fletcher", "imbuer", "blacksmith", "toolmaker"]
JOURNAL_NPC_PRICES = {3: 1154, 4: 2308, 5: 4616, 6: 9232, 7: 18464, 8: 36928}

# Antrean data ingestor
ingest_queue = queue.Queue()

class MemoryState:
    def __init__(self):
        self.lock = threading.RLock()
        self.db_gear = {}
        self.config = {}
        self.prices = {}
        self.checklist = {}
        self.logs = []
        self.volume = []
        self.price_version = 0
        
        self.dirty_config = False
        self.dirty_prices = False
        self.dirty_checklist = False
        self.dirty_logs = False
        self.dirty_volume = False

state = MemoryState()

# MENGGUNAKAN ORJSON UNTUK I/O YANG JAUH LEBIH CEPAT
def load_json(filepath, default):
    if not os.path.exists(filepath): return default
    try:
        with open(filepath, "rb") as f: return orjson.loads(f.read())
    except Exception: return default

def save_json(filepath, data):
    tmp = filepath + ".tmp"
    with open(tmp, "wb") as f: 
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    os.replace(tmp, filepath)

def _generate_tier_template(db, t):
    return {
        "raw":       {k: {e: "" for e in ENCHANTS} for k in ["fiber", "hide", "ore", "wood"]},
        "under":     {k: {e: "" for e in ENCHANTS} for k in ["cloth", "leather", "steel", "plank"]},
        "ref":       {k: {e: "" for e in ENCHANTS} for k in ["cloth", "leather", "steel", "plank"]},
        "artifacts": {}, 
        "crafted":   {cat: {k: {e: "" for e in ENCHANTS} for k in db.get(cat, {})} for cat in db},
        "journal":   {k: {"empty": JOURNAL_NPC_PRICES.get(t, ""), "full": ""} for k in JOURNAL_TYPES},
        "fragments": {"rune": "", "soul": "", "relic": ""},
        "farming_mats": {},
        "timestamps": {}, "timestamp": None,
    }

def _deep_merge(base, override):
    for key, val in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict): _deep_merge(base[key], val)
        else: base[key] = val
    return base

with state.lock:
    state.db_gear = load_json(DB_FILE, {})
    db_consumables = load_json("database/db_consumables.json", {})
    _deep_merge(state.db_gear, db_consumables)
    db_luxury = load_json("database/db_luxury.json", {})
    
    base_selected_items = {item: {e: True for e in ENCHANTS} for cat in state.db_gear.values() for item in cat}
    for lux in db_luxury.values():
        base_selected_items[lux["name"]] = {e: True for e in ENCHANTS}
        
    base_cfg = {
        "tier": 4, "q0": 0, "q1": 0, "q2": 0, "q3": 0, "q4": 0, 
        "selected_items": base_selected_items,
        "active_profile": "Default", "buy_city": "Lymhurst", "sell_city": "Black Market", "route_from": "Lymhurst", "route_to": "Fort Sterling",
        "gear": { "bag": {"t": 8, "e": 0, "q": "normal"}, "boots": {"t": 8, "e": 0, "q": "normal", "s": 106}, "mount": {"type": "ox", "t": 8, "q": "normal"}, "food": "pie_7_0" },
        "raw_cities": {"fiber": "Thetford", "hide": "Bridgewatch", "ore": "Fort Sterling", "wood": "Lymhurst", "stone": "Martlock"},
        "refine_cities": {"cloth": "Lymhurst", "leather": "Martlock", "steel": "Thetford", "plank": "Fort Sterling", "block": "Bridgewatch"},
        "frag_cities": {"rune": "Lymhurst", "soul": "Lymhurst", "relic": "Lymhurst"},
        "farming_buy_cities": {"crops": "Thetford", "herbs": "Thetford", "meat": "Lymhurst", "dairy": "Martlock", "intermediate": "Caerleon"},
        "cooking_city": "Lymhurst", "alchemy_city": "Thetford",
        "use_multi_consumables": True,
        "bonus_city_refine": True, "focus_refine": True, "bonus_city_craft": True, "focus_craft": False, "bonus_city_consumables": True, "premium_tax": True, "fee_refine": 0, "fee_craft": 0, "use_own_journals": True,
        "do_refine": True, "do_craft": True,
        "cancelled_crafts": {}, 
        "adjusted_qty_crafts": {},
        "profiles": { "Default": { "fiber": {"s": 100}, "hide": {"s": 100}, "ore": {"s": 100}, "wood": {"s": 100}, "main_specs": {} } }, 
        "specs": { "fiber": {"s": 100}, "hide": {"s": 100}, "ore": {"s": 100}, "wood": {"s": 100} }
    }
    saved_cfg = load_json(CONFIG_FILE, {})
    if "prices" in saved_cfg: del saved_cfg["prices"]
    state.config = _deep_merge(base_cfg, saved_cfg)
    for cat in state.db_gear.values():
        for item in cat:
            if item not in state.config["selected_items"]: 
                state.config["selected_items"][item] = {e: True for e in ENCHANTS}
            elif isinstance(state.config["selected_items"][item], bool):
                b = state.config["selected_items"][item]
                state.config["selected_items"][item] = {e: b for e in ENCHANTS}
                
    base_prices = {city: {f"t{t}": _generate_tier_template(state.db_gear, t) for t in TIERS} for city in ALL_CITIES}
    state.prices = _deep_merge(base_prices, load_json(PRICES_FILE, {}))
    state.checklist = load_json(CHECKLIST_FILE, {})
    state.logs = load_json(LOGS_FILE, [])
    state.volume = load_json(VOLUME_FILE, [])

# BACKGROUND SAVER THREAD (OPTIMIZED: NO LOCK DURING WRITE)
def background_saver():
    while True:
        time.sleep(3)
        to_save = {}
        with state.lock:
            if state.dirty_config: to_save[CONFIG_FILE] = copy.deepcopy(state.config); state.dirty_config = False
            if state.dirty_prices: to_save[PRICES_FILE] = copy.deepcopy(state.prices); state.dirty_prices = False
            if state.dirty_checklist: to_save[CHECKLIST_FILE] = copy.deepcopy(state.checklist); state.dirty_checklist = False
            if state.dirty_logs: to_save[LOGS_FILE] = copy.deepcopy(state.logs); state.dirty_logs = False
            if state.dirty_volume: to_save[VOLUME_FILE] = copy.deepcopy(state.volume); state.dirty_volume = False
        
        # 🚀 Tulis ke disk di LUAR LOCK biar network ga keganggu
        for filepath, content in to_save.items():
            try: save_json(filepath, content)
            except Exception as e: app.logger.error(f"[saver] Error saving {filepath}: {e}")

threading.Thread(target=background_saver, daemon=True).start()

# BACKGROUND INGESTOR WORKER (ASYNC QUEUE PROCESSOR)
def ingest_worker():
    while True:
        data = ingest_queue.get()
        try:
            with state.lock:
                target_tier = int(state.config.get("tier", 4))
                buy_city_snapshot = state.config.get("buy_city", "Lymhurst")
                
                # 🚀 OPTIMASI: Update langsung ke memory (in-place)
                # Gak perlu copy.deepcopy lagi, irit CPU 90%
                updated, _, vol_entries = process_ingest_data(data, target_tier, state.prices)
                
                if updated:
                    now_str = datetime.utcnow().isoformat() + "Z"
                    tk = f"t{target_tier}"
                    if buy_city_snapshot in state.prices and tk in state.prices[buy_city_snapshot]: 
                        state.prices[buy_city_snapshot][tk]["timestamp"] = now_str
                    
                    state.price_version += 1
                    state.dirty_prices = True
            
                if vol_entries:
                    now_ts  = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    cutoff  = (datetime.utcnow() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
                    for entry in vol_entries:
                        is_duplicate = False
                        for r in reversed(state.volume):
                            if r["ts"] < cutoff: break
                            if (r["tier"] == entry["tier"] and r["cat"] == entry["cat"] and r["item"] == entry["item"] and r["enchant"] == entry["enchant"]):
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            new_id = (state.volume[-1]["id"] + 1) if state.volume else 1
                            state.volume.append({ "id": new_id, "ts": now_ts, "tier": entry["tier"], "cat": entry["cat"], "item": entry["item"], "enchant": entry["enchant"], "price": entry["price"], "volume": entry["volume"] })
                    if len(state.volume) > 10000: state.volume = state.volume[-10000:]
                    state.dirty_volume = True
        except Exception as e:
            app.logger.error(f"[ingest_worker] Error: {e}")
        finally:
            ingest_queue.task_done()

threading.Thread(target=ingest_worker, daemon=True).start()

# --- ROUTES ---

@app.route('/')
def index(): return render_template('base.html')

@app.route('/favicon.ico')
def favicon(): return '', 204

@app.route("/static/<path:filename>")
def serve_static(filename): return send_file(os.path.join("static", filename))

from routes.api import api_bp
app.register_blueprint(api_bp)

@app.route('/api/prices_version', methods=['GET'])
def get_prices_version():
    return jsonify({"version": state.price_version})

@app.route('/api/ingest', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/<path:catchall>', methods=['GET', 'POST', 'OPTIONS'])
def handle_ingest(catchall=None):
    if request.method == 'OPTIONS':
        return '', 200
    if request.method == 'GET':
        return jsonify({"status": "ready"}), 200
        
    data = request.get_json(force=True, silent=True)
    if not data and request.data:
        try: data = orjson.loads(request.data)
        except: pass
        
    if data:
        # LANGSUNG LEMPAR KE ANTREAN & BALAS "OK" (0.001 DETIK)
        ingest_queue.put(data)
    return jsonify({"status": "queued"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True, threaded=True)