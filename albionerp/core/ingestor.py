import json
import os
from core.constants import ALBION_MAPPING, LOCATION_MAPPING, FARMING_MATS_MAPPING
from datetime import datetime

FRAGMENT_TYPES = {"RUNE": "rune", "SOUL": "soul", "RELIC": "relic"}

# DIUBAH JADI ITERATIVE STACK BIAR GA KENA RECURSION ERROR / CRASH
def extract_orders(d):
    orders = []
    stack = [d]
    
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            keys_lower = [k.lower() for k in current.keys()]
            if "itemtypeid" in keys_lower and ("price" in keys_lower or "unitpricesilver" in keys_lower):
                orders.append(current)
            for v in current.values():
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(current, list):
            for v in current:
                if isinstance(v, (dict, list)):
                    stack.append(v)
    return orders

def process_ingest_data(data, target_tier, current_prices):
    updated_prices = False
    volume_entries = []
    orders         = extract_orders(data)
    seen_items     = {}

    def _safe_dict(root, *keys):
        d = root
        for k in keys:
            d = d.setdefault(k, {})
        return d

    def _update_best_price(target_dict, key, val, unique_id, is_req):
        nonlocal updated_prices
        try:
            should_update = False
            if unique_id not in seen_items:
                should_update = True
            else:
                old_val = seen_items[unique_id]
                if is_req and val > old_val:
                    should_update = True
                elif not is_req and val < old_val:
                    should_update = True

            if should_update:
                seen_items[unique_id] = val
                target_dict[key] = val
                
                city, tier_key, category, enchant = unique_id
                if city in current_prices and tier_key in current_prices[city]:
                    ts_dict = current_prices[city][tier_key].setdefault("timestamps", {})
                    ts_dict[f"{category}_{enchant}"] = datetime.utcnow().isoformat() + "Z"
                
                updated_prices = True
        except KeyError:
            pass

    for o in orders:
        o_lower = {k.lower(): v for k, v in o.items()}
        
        loc_val = o_lower.get("locationid", o_lower.get("location", ""))
        loc_str = str(loc_val).strip().lower()
        city = LOCATION_MAPPING.get(loc_str, "Unknown")
        if city == "Unknown" and str(loc_val).isdigit():
            city = LOCATION_MAPPING.get(int(loc_val), "Unknown")
            
        if city == "Unknown": continue
        
        item_id = str(o_lower.get("itemtypeid", "")).upper()
        
        parts = item_id.split("@")
        base_id = parts[0]
        
        clean_id_temp = ""
        if len(base_id) > 3 and base_id[2] == "_":
            if "_LEVEL" in base_id: 
                clean_id_temp = base_id.split("_LEVEL")[0][3:]
            else:
                clean_id_temp = base_id[3:]

        is_fragment = clean_id_temp in ["RUNE", "SOUL", "RELIC"]

        auc_type = str(o_lower.get("auctiontype", "")).strip().lower()
        is_bm = (city == "Black Market")
        is_journal_full = ("JOURNAL_" in base_id and "FULL" in base_id)
        is_req = False
        
        if is_bm:
            if auc_type and auc_type != "request": continue
            is_req = True
        else:
            if is_journal_full:
                if auc_type and auc_type != "request": continue
                is_req = True
            else:
                if auc_type and auc_type != "offer": continue
                is_req = False
        
        price_val = 0
        if "unitpricesilver" in o_lower and float(o_lower["unitpricesilver"]) > 0:
            price_val = float(o_lower["unitpricesilver"]) / 10000.0
        elif "price" in o_lower and float(o_lower["price"]) > 0:
            price_val = float(o_lower["price"])
            
        if price_val <= 0: continue
        price = int(price_val)
        volume = int(o_lower.get("amount", 0))
        
        if "_LEVEL" in base_id: 
            level_str = base_id.split("_LEVEL")[1]
            base_id = base_id.split("_LEVEL")[0]
            enchant = f".{level_str}"
        else:
            enchant = f".{parts[1]}" if len(parts) > 1 else ".0"

        if not base_id.startswith("T") or len(base_id) < 3 or base_id[2] != "_": continue
        try: item_tier = int(base_id[1]) 
        except ValueError: continue
            
        if item_tier < 1 or item_tier > 8: continue
            
        tier_key_t = f"t{item_tier}"
        tier_key_over = f"t{item_tier + 1}" if item_tier < 8 else None 
        clean_id = base_id[3:] 

        try:
            if not is_bm:
                if clean_id == "FIBER": _update_best_price(_safe_dict(current_prices, city, tier_key_t, "raw", "fiber"), enchant, price, (city, tier_key_t, "raw_fiber", enchant), is_req)
                elif clean_id == "HIDE": _update_best_price(_safe_dict(current_prices, city, tier_key_t, "raw", "hide"), enchant, price, (city, tier_key_t, "raw_hide", enchant), is_req)
                elif clean_id == "ORE": _update_best_price(_safe_dict(current_prices, city, tier_key_t, "raw", "ore"), enchant, price, (city, tier_key_t, "raw_ore", enchant), is_req)
                elif clean_id == "WOOD": _update_best_price(_safe_dict(current_prices, city, tier_key_t, "raw", "wood"), enchant, price, (city, tier_key_t, "raw_wood", enchant), is_req)

                elif clean_id == "CLOTH": 
                    _update_best_price(_safe_dict(current_prices, city, tier_key_t, "ref", "cloth"), enchant, price, (city, tier_key_t, "ref_cloth", enchant), is_req)
                    if tier_key_over: _update_best_price(_safe_dict(current_prices, city, tier_key_over, "under", "cloth"), enchant, price, (city, tier_key_over, "under_cloth", enchant), is_req)
                elif clean_id == "LEATHER": 
                    _update_best_price(_safe_dict(current_prices, city, tier_key_t, "ref", "leather"), enchant, price, (city, tier_key_t, "ref_leather", enchant), is_req)
                    if tier_key_over: _update_best_price(_safe_dict(current_prices, city, tier_key_over, "under", "leather"), enchant, price, (city, tier_key_over, "under_leather", enchant), is_req)
                elif clean_id == "METALBAR": 
                    _update_best_price(_safe_dict(current_prices, city, tier_key_t, "ref", "steel"), enchant, price, (city, tier_key_t, "ref_steel", enchant), is_req)
                    if tier_key_over: _update_best_price(_safe_dict(current_prices, city, tier_key_over, "under", "steel"), enchant, price, (city, tier_key_over, "under_steel", enchant), is_req)
                elif clean_id == "PLANKS": 
                    _update_best_price(_safe_dict(current_prices, city, tier_key_t, "ref", "plank"), enchant, price, (city, tier_key_t, "ref_plank", enchant), is_req)
                    if tier_key_over: _update_best_price(_safe_dict(current_prices, city, tier_key_over, "under", "plank"), enchant, price, (city, tier_key_over, "under_plank", enchant), is_req)

                elif clean_id.startswith("JOURNAL_"):
                    j_type = ""
                    if "HUNTER" in clean_id: j_type = "fletcher"
                    elif "MAGE" in clean_id: j_type = "imbuer"
                    elif "WARRIOR" in clean_id: j_type = "blacksmith"
                    elif "TOOLMAKER" in clean_id: j_type = "toolmaker"
                    
                    j_state = "full" if "FULL" in clean_id else "empty" if "EMPTY" in clean_id else ""
                    
                    if j_type and j_state:
                        _update_best_price(_safe_dict(current_prices, city, tier_key_t, "journal", j_type), j_state, price, (city, tier_key_t, f"journal_{j_type}", j_state), is_req)

                elif clean_id in ["RUNE", "SOUL", "RELIC"]:
                    frag_key = FRAGMENT_TYPES[clean_id]
                    _update_best_price(_safe_dict(current_prices, city, tier_key_t, "fragments"), frag_key, price, (city, tier_key_t, f"frag_{frag_key}", "0"), is_req)
                    
                # FIX TRANSLASI ARTEFACT -> ARTIFACT KE DATABASE LOKAL LU
                elif clean_id.startswith("ARTEFACT_") or clean_id.startswith("ARTIFACT_"):
                    art_name = clean_id.lower().replace("artefact", "artifact")
                    _update_best_price(_safe_dict(current_prices, city, tier_key_t, "artifacts"), art_name, price, (city, tier_key_t, "artifacts", art_name), is_req)

            if base_id in FARMING_MATS_MAPPING:
                f_name = FARMING_MATS_MAPPING[base_id]
                _update_best_price(_safe_dict(current_prices, city, tier_key_t, "farming_mats"), f_name, price, (city, tier_key_t, f"farming_{f_name}", "price"), is_req)
            elif "LUXURY" in base_id:
                _update_best_price(_safe_dict(current_prices, city, tier_key_t, "luxury"), base_id, price, (city, tier_key_t, "luxury", base_id), is_req)

            if base_id in ALBION_MAPPING:
                cat, name = ALBION_MAPPING[base_id]
                _update_best_price(_safe_dict(current_prices, city, tier_key_t, "crafted", cat, name), enchant, price, (city, tier_key_t, f"crafted_{name}", enchant), is_req)
                if is_bm and volume > 0:
                    volume_entries.append({
                        "tier": item_tier, "cat": cat, "item": name,
                        "enchant": enchant, "price": price, "volume": volume
                    })
            elif clean_id in ALBION_MAPPING:
                cat, name = ALBION_MAPPING[clean_id]
                
                _update_best_price(_safe_dict(current_prices, city, tier_key_t, "crafted", cat, name), enchant, price, (city, tier_key_t, f"crafted_{name}", enchant), is_req)
                
                if is_bm and volume > 0:
                    volume_entries.append({
                        "tier": item_tier, "cat": cat, "item": name,
                        "enchant": enchant, "price": price, "volume": volume
                    })

        except KeyError:
            pass

    return updated_prices, current_prices, volume_entries