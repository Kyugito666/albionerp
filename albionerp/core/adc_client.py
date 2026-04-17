import requests
from datetime import datetime
from core.constants import ALBION_MAPPING, FARMING_MATS_MAPPING

# URL Server ASIA
ADC_URL = "https://east.albion-online-data.com/api/v2/stats/prices/"

REVERSE_MAP = {v[1]: k for k, v in ALBION_MAPPING.items()}
RAW_MAP = {"fiber": "FIBER", "hide": "HIDE", "ore": "ORE", "wood": "WOOD", "stone": "ROCK"}
REF_MAP = {"cloth": "CLOTH", "leather": "LEATHER", "steel": "METALBAR", "plank": "PLANKS", "block": "STONEBLOCK"}
MAT_PAIRS = [("cloth", "fiber"), ("leather", "hide"), ("steel", "ore"), ("plank", "wood"), ("block", "stone")]
ALL_CITIES = ["Lymhurst", "Fort Sterling", "Thetford", "Martlock", "Bridgewatch", "Caerleon", "Black Market"]

import re

def build_albion_id(base_str, tier, enchant, is_gear=False):
    actual_tier = tier
    match = re.match(r'^T(\d+)_', base_str)
    if match:
        actual_tier = match.group(1)
        base_str = base_str[len(match.group(0)):]
        
    if enchant == ".0": return f"T{actual_tier}_{base_str}"
    lvl = enchant.replace(".", "")
    return f"T{actual_tier}_{base_str}@{lvl}" if is_gear else f"T{actual_tier}_{base_str}_LEVEL{lvl}"

def get_timestamp(date_str):
    if not date_str or date_str == "0001-01-01T00:00:00": return None
    # FIX: Hapus "Z" dari response API sebelum di-parse
    clean_date = date_str.replace("Z", "")
    return datetime.strptime(clean_date.split(".")[0], "%Y-%m-%dT%H:%M:%S")

def fetch_and_merge_adc(cfg, current_prices, db):
    t = int(cfg.get("tier", 4))
    tk = f"t{t}"
    
    cities = ALL_CITIES

    item_queries = []
    item_metadata = {}

    for ref_name, raw_name in MAT_PAIRS:
        raw_base = RAW_MAP[raw_name]
        ref_base = REF_MAP[ref_name]
        for e in [".0", ".1", ".2", ".3", ".4"]:
            r_id = build_albion_id(raw_base, t, e, False)
            item_queries.append(r_id)
            item_metadata[r_id] = ("raw", raw_name, e)
            ref_id = build_albion_id(ref_base, t, e, False)
            item_queries.append(ref_id)
            item_metadata[ref_id] = ("ref", ref_name, e)
            if t > 3:
                eu = e if t > 4 else ".0"
                ur_id = build_albion_id(ref_base, t-1, eu, False)
                item_queries.append(ur_id)
                item_metadata[ur_id] = ("under", ref_name, eu)

    for frag, b_id in zip(["rune", "soul", "relic"], ["RUNE", "SOUL", "RELIC"]):
        f_id = f"T{t}_{b_id}"
        item_queries.append(f_id)
        item_metadata[f_id] = ("fragments", frag, "0")

    # 🚀 TAMBAHAN JURNAL TOOLMAKER
    for j, b_id in zip(["fletcher", "imbuer", "blacksmith", "toolmaker"], ["HUNTER", "MAGE", "WARRIOR", "TOOLMAKER"]):
        j_e = f"T{t}_JOURNAL_{b_id}_EMPTY"
        j_f = f"T{t}_JOURNAL_{b_id}_FULL"
        item_queries.extend([j_e, j_f])
        item_metadata[j_e] = ("journal", j, "empty")
        item_metadata[j_f] = ("journal", j, "full")

    # 🚀 TAMBAHAN SEMUA FARMING MATS (T1-T8)
    for farm_id, mat_name in FARMING_MATS_MAPPING.items():
        item_queries.append(farm_id)
        item_metadata[farm_id] = ("farming_mats", mat_name)

    for cat, items in db.items():
        for item_name, item_data in items.items():
            base_id = REVERSE_MAP.get(item_name)
            art_id = item_data.get("artifact")
            heart_id = item_data.get("heart") # 🚀 TANGKEP JEROAN HEART

            if base_id:
                if art_id:
                    # 🚀 BYPASS KHUSUS TOME OF INSIGHT (Selalu T4 di ADC)
                    if art_id.lower() == "tome_experience":
                        a_id = f"T4_{art_id.upper()}"
                    elif "capeitem_" in art_id.lower() and "_crest" in art_id.lower():
                        # 🚀 FACTION CRESTS: DB stores "capeitem_fw_lymhurst_crest" → ADC expects "T4_CAPEITEM_FW_LYMHURST_CREST"
                        # Crests are always T4 in ADC regardless of crafting tier
                        a_id = f"T4_{art_id.upper()}"
                    else:
                        # Standard Artifact scaling per tier (e.g., artifact_head_cloth_keeper → ARTEFACT_HEAD_CLOTH_KEEPER)
                        a_id = f"T{t}_{art_id.upper()}".replace("ARTIFACT_", "ARTEFACT_")

                    item_queries.append(a_id)
                    item_metadata[a_id] = ("artifacts", art_id, "0")

                if heart_id:
                    # 🚀 BYPASS KHUSUS HEART & AVALONIAN ENERGY
                    if heart_id.lower() == "token_avalon":
                        h_id = "QUESTITEM_TOKEN_AVALON"
                    else:
                        # 🚀 CITY HEARTS: DB stores "faction_forest_token_1" → ADC expects "T4_FACTION_FOREST_TOKEN_1"
                        # City Hearts are always T4 in ADC
                        h_id = f"T4_{heart_id.upper()}"

                    item_queries.append(h_id)
                    item_metadata[h_id] = ("artifacts", heart_id, "0")

                for e in [".0", ".1", ".2", ".3", ".4"]:
                    g_id = build_albion_id(base_id, t, e, True)
                    item_queries.append(g_id)
                    item_metadata[g_id] = ("crafted", cat, item_name, e)

    item_queries = list(set(item_queries))
    updated_any = False

    chunk_size = 100
    for i in range(0, len(item_queries), chunk_size):
        chunk = item_queries[i:i+chunk_size]
        url = f"{ADC_URL}{','.join(chunk)}?locations={','.join(cities)}"
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200: continue
            data = resp.json()

            for row in data:
                c = row.get("city")
                if not c or c not in cities: continue
                item_id = row.get("item_id")
                meta = item_metadata.get(item_id)
                if not meta: continue

                is_bm = (c == "Black Market")
                
                s_price_s = row.get("sell_price_min", 0)
                s_date_s  = row.get("sell_price_min_date", "")
                b_price_s = row.get("buy_price_max", 0)
                b_date_s  = row.get("buy_price_max_date", "")

                s_ts = get_timestamp(s_date_s)
                b_ts = get_timestamp(b_date_s)

                price_to_use = 0
                ts_to_use = None

                if meta[0] in ["raw", "under", "ref", "fragments", "artifacts", "farming_mats"]:
                    if not is_bm:
                        if s_price_s > 0:
                            price_to_use = s_price_s
                            ts_to_use = s_ts
                elif meta[0] == "journal":
                    if not is_bm:
                        if meta[2] == "empty" and s_price_s > 0:
                            price_to_use = s_price_s
                            ts_to_use = s_ts
                        elif meta[2] == "full" and b_price_s > 0:
                            price_to_use = b_price_s
                            ts_to_use = b_ts
                elif meta[0] == "crafted":
                    if is_bm and b_price_s > 0:
                        price_to_use = b_price_s
                        ts_to_use = b_ts

                if price_to_use > 0 and ts_to_use:
                    if c not in current_prices: current_prices[c] = {}
                    if tk not in current_prices[c]:
                        current_prices[c][tk] = { "raw": {}, "under": {}, "ref": {}, "journal": { "fletcher": {}, "imbuer": {}, "blacksmith": {}, "toolmaker": {} }, "fragments": {}, "artifacts": {}, "crafted": {}, "timestamps": {} }
                    
                    p_node = current_prices[c][tk]
                    cat_name = meta[0]
                    
                    ts_key = ""

                    if cat_name in ["raw", "under", "ref"]:
                        if meta[1] not in p_node[cat_name]: p_node[cat_name][meta[1]] = {}
                        p_node[cat_name][meta[1]][meta[2]] = price_to_use
                        ts_key = f"{cat_name}_{meta[1]}_{meta[2]}"
                    elif cat_name == "fragments":
                        p_node[cat_name][meta[1]] = price_to_use
                        ts_key = f"frag_{meta[1]}_0"
                    elif cat_name == "artifacts":
                        p_node[cat_name][meta[1]] = price_to_use
                        ts_key = f"artifacts_{meta[1]}"
                    elif cat_name == "farming_mats":
                        # Extract tier from item_id (e.g., T5_CABBAGE -> t5)
                        try:
                            f_tier = int(item_id[1])
                            f_tk = f"t{f_tier}"
                        except:
                            f_tk = tk

                        if f_tk not in current_prices[c]:
                             current_prices[c][f_tk] = { "raw": {}, "under": {}, "ref": {}, "journal": { "fletcher": {}, "imbuer": {}, "blacksmith": {}, "toolmaker": {} }, "fragments": {}, "artifacts": {}, "crafted": {}, "timestamps": {}, "farming_mats": {} }
                        
                        f_node = current_prices[c][f_tk]
                        if "farming_mats" not in f_node: f_node["farming_mats"] = {}
                        f_node["farming_mats"][meta[1]] = price_to_use
                        ts_key = f"farming_{meta[1]}_price"
                        
                        if ts_key:
                            existing_ts_str = f_node.get("timestamps", {}).get(ts_key)
                            existing_ts = get_timestamp(existing_ts_str) if existing_ts_str else None
                            if not existing_ts or ts_to_use > existing_ts:
                                f_node.setdefault("timestamps", {})[ts_key] = ts_to_use.isoformat() + "Z"
                                updated_any = True
                        continue # Skip the generic timestamp update below
                    elif cat_name == "journal":
                        if "toolmaker" not in p_node["journal"]: p_node["journal"]["toolmaker"] = {} 
                        if meta[1] not in p_node["journal"]: p_node["journal"][meta[1]] = {}
                        p_node["journal"][meta[1]][meta[2]] = price_to_use
                        ts_key = f"journal_{meta[1]}_{meta[2]}"
                    elif cat_name == "crafted":
                        c_cat = meta[1]
                        i_name = meta[2]
                        e_lvl = meta[3]
                        if c_cat not in p_node["crafted"]: p_node["crafted"][c_cat] = {}
                        if i_name not in p_node["crafted"][c_cat]: p_node["crafted"][c_cat][i_name] = {}
                        p_node["crafted"][c_cat][i_name][e_lvl] = price_to_use
                        ts_key = f"crafted_{i_name}_{e_lvl}"

                    if ts_key:
                        existing_ts_str = p_node.get("timestamps", {}).get(ts_key)
                        existing_ts = get_timestamp(existing_ts_str) if existing_ts_str else None
                        
                        if not existing_ts or ts_to_use > existing_ts:
                            p_node.setdefault("timestamps", {})[ts_key] = ts_to_use.isoformat() + "Z"
                            updated_any = True

        except Exception as e:
            print(f"Error fetching ADC chunk: {e}")

    return updated_any, current_prices