from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')

# We need to access state and functions from main, but to avoid circular imports,
# we can inject them or just import them inside functions. For a simple app,
# it's cleaner to put the state in a separate module, but since we are just 
# refactoring main.py quickly, we'll import from main locally inside functions.

def get_main():
    import sys
    if 'main' in sys.modules and hasattr(sys.modules['main'], 'state'):
        return sys.modules['main']
    elif '__main__' in sys.modules and hasattr(sys.modules['__main__'], 'state'):
        return sys.modules['__main__']
    import main as main_module
    return main_module

@api_bp.route("/config", methods=["GET", "POST"])
def config_api():
    m = get_main()
    with m.state.lock:
        if request.method == "POST":
            data = request.json
            if "prices" in data: del data["prices"]
            m.state.config = data
            m.state.dirty_config = True
            return jsonify({"status": "success"})
        return jsonify(m.state.config)

@api_bp.route("/prices", methods=["GET", "POST"])
def prices_api():
    m = get_main()
    with m.state.lock:
        if request.method == "POST":
            m.state.prices = m._deep_merge(m.state.prices, request.json)
            m.state.price_version += 1
            m.state.dirty_prices = True
            return jsonify({"status": "success"})
        return jsonify(m.state.prices)

@api_bp.route("/adc_fetch", methods=["POST"])
def fetch_adc_api():
    m = get_main()
    def background_fetch():
        import copy
        try:
            with m.state.lock:
                cfg_copy = copy.deepcopy(m.state.config)
                prices_copy = copy.deepcopy(m.state.prices)
            updated, new_prices = m.fetch_and_merge_adc(cfg_copy, prices_copy, m.state.db_gear)
            if updated:
                with m.state.lock:
                    m.state.prices = new_prices
                    m.state.price_version += 1
                    m.state.dirty_prices = True
        except Exception as e:
            m.app.logger.error(f"[fetch_adc_bg] Error: {e}")

    m.threading.Thread(target=background_fetch, daemon=True).start()
    return jsonify({"status": "success", "message": "ADC fetch process running in background"})

@api_bp.route("/checklist", methods=["GET", "POST", "DELETE"])
def checklist_api():
    m = get_main()
    with m.state.lock:
        if request.method == "POST":
            m.state.checklist = request.json
            m.state.dirty_checklist = True
            return jsonify({"status": "success"})
        elif request.method == "DELETE":
            m.state.checklist = {}
            m.state.dirty_checklist = True
            return jsonify({"status": "cleared"})
        return jsonify(m.state.checklist)

@api_bp.route("/logs", methods=["GET", "POST", "DELETE"])
def logs_api():
    m = get_main()
    with m.state.lock:
        if request.method == "POST":
            m.state.logs = request.json
            m.state.dirty_logs = True
            return jsonify({"status": "success"})
        elif request.method == "DELETE":
            m.state.logs = []
            m.state.dirty_logs = True
            return jsonify({"status": "cleared"})
        return jsonify(m.state.logs)

@api_bp.route("/volume", methods=["GET", "DELETE"])
def volume_api():
    m = get_main()
    with m.state.lock:
        if request.method == "DELETE":
            m.state.volume = []
            m.state.dirty_volume = True
            return jsonify({"status": "cleared"})

        tier_f, cat_f, enchant_f, days_f = request.args.get("tier", ""), request.args.get("cat", ""), request.args.get("enchant", ""), int(request.args.get("days", "30"))
        records = m.state.volume

        if days_f > 0:
            cutoff = (datetime.utcnow() - timedelta(days=days_f)).strftime("%Y-%m-%d %H:%M:%S")
            records = [r for r in records if r["ts"] >= cutoff]
        if tier_f: records = [r for r in records if str(r["tier"]) == tier_f]
        if cat_f: records = [r for r in records if r["cat"] == cat_f]
        if enchant_f: records = [r for r in records if r["enchant"] == enchant_f]

        records_sorted = sorted(records, key=lambda x: x["ts"], reverse=True)
        prices_all = [r["price"] for r in records if r["price"] > 0]
        unique_items = len(set(f"{r['item']} {r['enchant']}" for r in records))
        last_ts = records_sorted[0]["ts"] if records_sorted else None
        return jsonify({ "history": records_sorted[:5000], "summary": { "total": len(records), "unique_items": unique_items, "avg_price": int(sum(prices_all) / len(prices_all)) if prices_all else 0, "last_capture": last_ts } })

@api_bp.route("/calculate")
def calculate():
    m = get_main()
    try:
        with m.state.lock:
            calc_result = m.execute_calculation(m.state.config, m.state.db_gear, m.state.prices)
            logistics_result = m.build_manifest(m.state.config, calc_result)
            calc_result["logistics"] = logistics_result
            peak_w = logistics_result.get("peak_weight", 0.0)
            max_load = calc_result.get("weight_data", {}).get("max_load", 50.0)
            calc_result["weight_data"]["total_kg"] = round(peak_w, 1)
            calc_result["weight_data"]["percentage"] = min(round((peak_w / max_load) * 100, 1), 100) if max_load > 0 else 0  
            calc_result["weight_data"]["is_overweight"] = peak_w > max_load
        return jsonify(calc_result)
    except Exception as e:
        import traceback
        import core.ai_analyzer
        error_trace = traceback.format_exc()
        m.app.logger.error(f"[calculate] Error: {e}\n{error_trace}")
        
        # Auto-Recovery via LLM if API Key is set
        api_key = m.state.config.get("gemini_api_key", "")
        if api_key:
            try:
                m.app.logger.info("[calculate] Attempting Auto-Recovery via Gemini LLM...")
                safe_fallback = core.ai_analyzer.auto_recover_error(api_key, error_trace, {"mode": "calculate"})
                # We return an empty safe state to prevent UI crash, alongside the reasoning
                return jsonify({
                    "weight_data": {"total_kg": 0, "percentage": 0, "is_overweight": False, "max_load": 50},
                    "focus_data": {"used": 0, "remaining": 30000, "is_overcap": False},
                    "financial": {"total_capital": 0, "grand_profit": 0, "profit_refine": 0, "profit_bm": 0, "profit_journals": 0, "cost_raw_mats": 0, "fee_refine": 0, "fee_craft": 0, "cost_journals": 0, "cost_artifacts": 0},
                    "raw_crafting_data": [], "raw_refine_data": [], "journals": {}, "logistics": {"manifest": []},
                    "ai_recovery_reasoning": safe_fallback.get("reasoning", "Unknown AI reason")
                }), 200
            except Exception as llm_e:
                m.app.logger.error(f"[calculate] Auto-Recovery failed: {llm_e}")

        return jsonify({"error": str(e)}), 500

@api_bp.route("/smart_llm", methods=["POST"])
def smart_llm():
    m = get_main()
    data = request.json
    api_key = m.state.config.get("gemini_api_key", "")

    # Local fallback works even without API key — no early 400 return
    try:
        import copy
        import core.ai_analyzer

        # Snapshot state under lock for thread-safe read
        with m.state.lock:
            cfg_snap = copy.deepcopy(m.state.config)
            db_snap = copy.deepcopy(m.state.db_gear)
            prices_snap = copy.deepcopy(m.state.prices)
            vol_snap = list(m.state.volume)

        res = core.ai_analyzer.analyze_portfolio(
            api_key=api_key,
            budget=data.get("budget"),
            candidates=data.get("candidates"),
            mode=data.get("mode"),
            cfg=cfg_snap,
            db=db_snap,
            prices=prices_snap,
            volume_records=vol_snap,
        )
        return jsonify(res)
    except Exception as e:
        import traceback
        import core.ai_analyzer
        error_trace = traceback.format_exc()
        m.app.logger.error(f"[smart_llm] Error: {e}\n{error_trace}")

        # Auto-Recovery via LLM
        if api_key:
            try:
                m.app.logger.info("[smart_llm] Attempting Auto-Recovery via Gemini LLM...")
                safe_fallback = core.ai_analyzer.auto_recover_error(api_key, error_trace, {"mode": data.get("mode"), "budget": data.get("budget")})
                return jsonify(safe_fallback), 200
            except Exception as llm_e:
                m.app.logger.error(f"[smart_llm] Auto-Recovery failed: {llm_e}")

        return jsonify({"error": str(e)}), 500

