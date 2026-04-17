import math
import re
from core.constants import RESOURCE_WEIGHT, FRAGMENT_MAPPING

from core.constants import RESOURCE_WEIGHT, FRAGMENT_MAPPING, ITEM_BONUS_CITY, FARMING_MATS_MAPPING, FARMING_GROUPS, FARMING_BONUS_CITY

def get_stack_info(qty):
    c_qty = math.ceil(float(qty))
    stacks = c_qty // 999
    rem = c_qty % 999
    return f"{c_qty:,} ({stacks} Stk + {rem})" if stacks > 0 else f"{c_qty:,}"

def build_manifest(cfg: dict, calc_data: dict) -> dict:
    royal_cities = ["Lymhurst", "Fort Sterling", "Thetford", "Martlock", "Bridgewatch", "Caerleon", "Brecilien"]
    board = {c: {"refine": [], "craft": [], "peak_weight_in": 0.0, "peak_weight_out": 0.0} for c in royal_cities}

    use_multi = cfg.get("use_multi_refine", True)
    use_multi_cons = cfg.get("use_multi_consumables", False)
    base_craft_city = "" if use_multi else cfg.get("craft_city", "Lymhurst")

    global_raw = {}
    global_under = {}
    global_farm = {} # {city: {mat_name: qty}}
    global_frags_total = {}
    global_frags_detail = {}
    global_arts_total = {} # {art_name: qty}

    for r in calc_data.get("raw_refine_data", []):
        if use_multi:
            target_city = cfg.get("refine_cities", {}).get(r["mat"], "Lymhurst")
        else:
            target_city = base_craft_city if base_craft_city else cfg.get("buy_city", "Lymhurst")
        
        t_ref = r.get("tier", int(cfg.get("tier", 4)))
        under_t = t_ref - 1 if t_ref > 3 else t_ref

        raw_name = r.get("raw_name", "")
        raw_qty = r.get("raw_qty", 0)
        enc = r.get("enchant", ".0")
        
        if raw_qty > 0 and raw_name:
            r_key = f"{raw_name} (T{t_ref})"
            if r_key not in global_raw: global_raw[r_key] = {".0":0, ".1":0, ".2":0, ".3":0, ".4":0}
            global_raw[r_key][enc] += raw_qty
            
        u_qty = r.get("under_qty", 0)
        u_enc = ".0" if under_t <= 3 else r.get("under_enchant", ".0")
        
        if u_qty > 0:
            mat_key = f"{r.get('mat', '')} (T{under_t})"
            if mat_key not in global_under: global_under[mat_key] = {".0":0, ".1":0, ".2":0, ".3":0, ".4":0}
            global_under[mat_key][u_enc] += u_qty

        if target_city in board:
            board[target_city]["peak_weight_in"] += r.get("weight_in", 0)
            board[target_city]["peak_weight_out"] += r.get("weight_out", 0)
            
            if u_qty > 0:
                if under_t <= 3:
                    under_text = f" <span class='text-gray-500'>|</span> Beli Lokal: <span class='text-rose-400'>{get_stack_info(u_qty)} Pcs {r['mat'].upper()} T{under_t} (Flat)</span>"
                else:
                    under_text = f" <span class='text-gray-500'>|</span> Beli Lokal: <span class='text-rose-400'>{get_stack_info(u_qty)} Pcs {r['mat'].upper()} T{under_t} {u_enc}</span>"
            else:
                under_text = ""

            base_r = r.get("base_raw", 0)
            base_u = r.get("base_under", 0)
            base_txt = f"<br><span class='text-[10px] text-gray-500'>*Syarat Buka Tas (Base Req): {get_stack_info(base_r)} {raw_name.upper()} T{t_ref} & {get_stack_info(base_u)} UNDER-REFINE T{under_t}</span>"

            task_id = f"ref_{target_city}_{r['mat']}_{t_ref}_{r['enchant']}"
            board[target_city]["refine"].append({
                "id": task_id,
                "text": f"Refine <strong class='text-amber-300'>{get_stack_info(r['qty'])} Pcs</strong> {r['mat'].upper()} T{t_ref} {r['enchant']}<br><span class='text-cyan-400 text-xs font-mono'>Net Consumed: {get_stack_info(raw_qty)} Pcs {raw_name.upper()} T{t_ref}{under_text}</span>{base_txt}",
                "weight_in": r.get("weight_in", 0),
                "weight_out": r.get("weight_out", 0),
                "mat": r["mat"],
                "tier": t_ref,
                "u_qty": u_qty,
                "u_enc": u_enc,
                "raw_qty": raw_qty,
                "out_qty": r.get("qty", 0),
                "fame": r.get("fame", 0) 
            })

    for c in calc_data.get("raw_crafting_data", []):
        item_name = c["item"]
        qty = c["qty"]
        is_cancelled = c.get("is_cancelled", False)
        t_craft = c.get("tier", int(cfg.get("tier", 4)))
        j_type = str(c.get("journal", "")).lower()
        
        # Determine target city
        bonus_hub = ITEM_BONUS_CITY.get(item_name, "")
        is_cons = bonus_hub in ["Caerleon", "Brecilien"]
        
        if use_multi_cons and cfg.get("use_multi_cooking", True):
            if is_cons:
                if bonus_hub == "Caerleon": target_city = cfg.get("cooking_city", "Caerleon")
                else: target_city = cfg.get("alchemy_city", "Brecilien")
            else:
                target_city = bonus_hub or cfg.get("buy_city", "Lymhurst")
        else:
            target_city = base_craft_city if base_craft_city else (bonus_hub or cfg.get("buy_city", "Lymhurst"))
            if is_cons: target_city = cfg.get("craft_city", "Lymhurst")

        # FILTER: Only show consumables in the consumables tab, and gear in the gear tab.
        active_tab = cfg.get("activeTab", "dashboard")
        if active_tab == 'logistics_consumables' and not is_cons: continue
        if active_tab == 'logistics_craft' and is_cons: continue

        # Handle farming mats for manifest
        if not is_cancelled:
            for m_name, enchants in c.get("mats_dict", {}).items():
                m_lower = m_name.lower()
                m_qty = sum(enchants.values())
                if m_lower in FARMING_MATS_MAPPING.values():
                    f_buy_city = cfg.get("buy_city", "Lymhurst")
                    if use_multi_cons and cfg.get("use_multi_farming", True):
                        # PRIORITAS 1: Bonus City Mapping (FARMING YIELD)
                        bonus_farm_city = FARMING_BONUS_CITY.get(m_lower)
                        if bonus_farm_city:
                            f_buy_city = bonus_farm_city
                        else:
                            f_cat = "crops"
                            for fc, flist in FARMING_GROUPS.items():
                                if m_lower in flist: f_cat = fc; break
                            f_buy_city = cfg.get("farming_buy_cities", {}).get(f_cat, f_buy_city)
                    
                    if f_buy_city not in global_farm: global_farm[f_buy_city] = {}
                    global_farm[f_buy_city][m_name] = global_farm[f_buy_city].get(m_name, 0) + m_qty

        frag_base = FRAGMENT_MAPPING.get(item_name, "").lower()
        if frag_base in ["rune", "soul", "relic"]:
            f_key = f"{frag_base} (T{t_craft})"
            if f_key not in global_frags_total: global_frags_total[f_key] = 0
            f_qty = qty * 50
            global_frags_total[f_key] += f_qty
            
            meld_cat = {"blacksmith": "Warrior's", "fletcher": "Hunter's", "imbuer": "Mage's"}.get(j_type, "")
            if meld_cat:
                if meld_cat not in global_frags_detail:
                    global_frags_detail[meld_cat] = {}
                if f_key not in global_frags_detail[meld_cat]:
                    global_frags_detail[meld_cat][f_key] = 0
                global_frags_detail[meld_cat][f_key] += f_qty

        if target_city in board:
            board[target_city]["peak_weight_in"] += c.get("weight_in", 0)
            board[target_city]["peak_weight_out"] += c.get("weight_out", 0)
            
            j_amt_float = float(c.get("j_amount", 0))
            j_text = f" <span class='text-gray-500'>|</span> Journals: <span class='text-purple-400'>{round(j_amt_float, 2)}x {j_type.title()} T{t_craft}</span>" if cfg.get("use_own_journals", False) and j_type and j_amt_float > 0 else ""
            
            mats_dict_formatted = c.get("mats_dict", {})
            task_id = f"craft_{target_city}_{item_name.replace(' ','')}_{t_craft}_{c['enchant']}"
            
            j_key_with_tier = f"{j_type} T{t_craft}" if j_type else ""

            board[target_city]["craft"].append({
                "id": task_id,
                "text": f"Craft <strong class='text-white'>{qty}x</strong> {item_name} T{t_craft} {c['enchant']}<br><span class='text-emerald-400 text-xs font-mono'>Net Consumed: {c['mats_str']}{j_text}</span>",
                "weight_in": c.get("weight_in", 0),
                "weight_out": c.get("weight_out", 0),
                "mats_dict": mats_dict_formatted,
                "j_type": j_key_with_tier if cfg.get("use_own_journals", False) else "",
                "j_amt": j_amt_float if cfg.get("use_own_journals", False) else 0.0,
                "out_qty": qty,
                "is_cancelled": is_cancelled,
                "fame": c.get("fame", 0),             
                "main_node": c.get("main_node", ""),  
                "raw_data": {"item": item_name, "enchant": c['enchant']}
            })

            # AGGREGATE UPGRADE FRAGMENTS AND ARTIFACTS INTO GLOBAL TOTALS
            if not is_cancelled:
                for m_name, enchants in mats_dict_formatted.items():
                    m_lower = m_name.lower()
                    m_qty = sum(enchants.values())
                    if "rune" in m_lower or "soul" in m_lower or "relic" in m_lower:
                        if m_name not in global_frags_total: global_frags_total[m_name] = 0
                        global_frags_total[m_name] += m_qty
                    
                    # Logic to identify Artifacts/Hearts (they aren't in refined/farming/fragments)
                    REFINED_LIST = ["cloth", "leather", "steel", "plank", "block"]
                    is_refined = any(r in m_lower for r in REFINED_LIST)
                    is_farming = m_lower in FARMING_MATS_MAPPING.values()
                    is_fragment = "rune" in m_lower or "soul" in m_lower or "relic" in m_lower
                    
                    if not (is_refined or is_farming or is_fragment):
                        if m_name not in global_arts_total: global_arts_total[m_name] = 0
                        global_arts_total[m_name] += m_qty

    is_cons_tab = cfg.get("activeTab") == "logistics_consumables"
    
    shop_html = "<div class='grid grid-cols-1 md:grid-cols-5 gap-6'>"
    
    # 1. TOTAL RAW (Sorted by Tier)
    if not is_cons_tab:
        active_raw = {m: {e:q for e,q in encs.items() if q>0} for m, encs in global_raw.items()}
        active_raw = {m: encs for m, encs in active_raw.items() if encs}
        if active_raw:
            shop_html += "<div><h4 class='text-xs font-black text-cyan-400 uppercase tracking-widest mb-3 border-b border-[#1E2D45] pb-2'>Total Raw (Gather)</h4>"
            # Sort by tier found in parentheses, e.g., "(T4)"
            sorted_mats = sorted(active_raw.keys(), key=lambda x: re.search(r'\(T(\d+)\)', x).group(1) if re.search(r'\(T(\d+)\)', x) else x)
            for m in sorted_mats:
                encs = active_raw[m]
                shop_html += f"<div class='mb-3'><span class='text-[11px] font-bold text-gray-400 uppercase block mb-1.5'>{m}</span><div class='flex flex-wrap gap-1.5'>"
                for e, q in sorted(encs.items()):
                    ec = {"0":"enc-0", "1":"enc-1", "2":"enc-2", "3":"enc-3", "4":"enc-4"}.get(e[1:], "text-white")
                    shop_html += f"<span class='bg-[#0A101C] px-2 py-1 rounded border border-[#1E2D45] text-[11px] font-mono'><span class='{ec} font-black'>{e}</span>: {get_stack_info(q)}</span>"
                shop_html += "</div></div>"
            shop_html += "</div>"

    # 2. TOTAL UNDER-REFINE (Sorted by Tier)
    if not is_cons_tab:
        active_under = {m: {e:q for e,q in encs.items() if q>0} for m, encs in global_under.items()}
        active_under = {m: encs for m, encs in active_under.items() if encs}
        if active_under:
            shop_html += "<div><h4 class='text-xs font-black text-rose-400 uppercase tracking-widest mb-3 border-b border-[#1E2D45] pb-2'>Total Under-Refine</h4>"
            sorted_mats = sorted(active_under.keys(), key=lambda x: re.search(r'\(T(\d+)\)', x).group(1) if re.search(r'\(T(\d+)\)', x) else x)
            for m in sorted_mats:
                encs = active_under[m]
                shop_html += f"<div class='mb-3'><span class='text-[11px] font-bold text-gray-400 uppercase block mb-1.5'>{m}</span><div class='flex flex-wrap gap-1.5'>"
                if "(T3)" in m:
                    tot = sum(encs.values())
                    shop_html += f"<span class='bg-[#0A101C] px-2 py-1 rounded border border-[#1E2D45] text-[11px] font-mono text-white'>FLAT: {get_stack_info(tot)}</span>"
                else:
                    for e, q in sorted(encs.items()):
                        ec = {"0":"enc-0", "1":"enc-1", "2":"enc-2", "3":"enc-3", "4":"enc-4"}.get(e[1:], "text-white")
                        shop_html += f"<span class='bg-[#0A101C] px-2 py-1 rounded border border-[#1E2D45] text-[11px] font-mono'><span class='{ec} font-black'>{e}</span>: {get_stack_info(q)}</span>"
                shop_html += "</div></div>"
            shop_html += "</div>"
    
    # 3. TOTAL FRAGMENTS (Sorted by Tier)
    if not is_cons_tab:
        has_frags = sum(global_frags_total.values()) > 0
        if has_frags:
            shop_html += "<div><h4 class='text-xs font-black text-purple-400 uppercase tracking-widest mb-3 border-b border-[#1E2D45] pb-2'>Total Fragments (Gacha)</h4>"
            shop_html += f"<div class='flex flex-col gap-3'>"
            for cat_name, frags in global_frags_detail.items():
                active_frags = {f:q for f,q in frags.items() if q>0}
                if active_frags:
                    shop_html += f"<div><span class='text-[10px] text-gray-400 font-bold uppercase mb-1 block'>Meld Categories: {cat_name}</span><div class='flex flex-col gap-1'>"
                    # Sort frags by Tier
                    sorted_f = sorted(active_frags.items(), key=lambda x: re.search(r'\(T(\d+)\)', x[0]).group(1) if re.search(r'\(T(\d+)\)', x[0]) else x[0])
                    for f_type, f_qty in sorted_f:
                        color_class = "text-amber-400" if "rune" in f_type.lower() else "text-purple-400" if "soul" in f_type.lower() else "text-rose-400"
                        shop_html += f"<span class='bg-[#0A101C] px-3 py-1.5 rounded border border-[#1E2D45] text-[10px] font-mono'><span class='{color_class} font-black uppercase'>{f_type}</span>: {get_stack_info(f_qty)} Pcs</span>"
                    shop_html += "</div></div>"

            total_active = {f:q for f,q in global_frags_total.items() if q>0}
            if total_active:
                shop_html += f"<div class='mt-1 pt-2 border-t border-[#1E2D45]'><span class='text-[10px] text-emerald-400 font-bold uppercase mb-1.5 block'>TOTAL BUY ORDER (MAX 9999/ORDER)</span><div class='flex flex-col gap-1'>"
                # Sort by Tier
                sorted_total = sorted(total_active.items(), key=lambda x: re.search(r'T(\d+)', x[0]).group(1) if re.search(r'T(\d+)', x[0]) else x[0])
                for f_type, f_qty in sorted_total:
                    color_class = "text-amber-400" if "rune" in f_type.lower() else "text-purple-400" if "soul" in f_type.lower() else "text-rose-400"
                    bo_qty = math.ceil(float(f_qty))
                    if bo_qty <= 9999: bo_str = f"{bo_qty:,} Pcs"
                    else:
                        orders = bo_qty // 9999; rem = bo_qty % 9999
                        parts = ["9999"] * orders
                        if rem > 0: parts.append(str(rem))
                        bo_str = f"{bo_qty:,} Pcs <span class='text-gray-500'>({ ' + '.join(parts) })</span>"
                    shop_html += f"<span class='bg-[#0A101C] px-3 py-1.5 rounded border border-emerald-900/40 text-[10px] font-mono'><span class='{color_class} font-black uppercase'>{f_type}</span>: {bo_str}</span>"
                shop_html += "</div></div>"
            shop_html += "</div></div>"

    # 4. TOTAL FARMING MATS
    has_farm = any(mats for mats in global_farm.values())
    if has_farm:
        col_title = "Ingredients (Farming/Enchant)" if is_cons_tab else "Total Farming Mats"
        shop_html += f"<div><h4 class='text-xs font-black text-emerald-400 uppercase tracking-widest mb-3 border-b border-[#1E2D45] pb-2'>{col_title}</h4>"
        for city in sorted(global_farm.keys()):
            mats = global_farm[city]
            if mats:
                shop_html += f"<div class='mb-3'><span class='text-[11px] font-black text-emerald-500 uppercase block mb-1.5 underline decoration-emerald-500/30'>Buy at: {city}</span><div class='flex flex-col gap-1'>"
                for m_name in sorted(mats.keys()):
                    m_qty = mats[m_name]
                    shop_html += f"<span class='bg-[#0A101C] px-3 py-1.5 rounded border border-[#1E2D45] text-[11px] font-mono text-white'><span class='text-emerald-400 font-black'>{m_name.upper()}</span>: {get_stack_info(m_qty)}</span>"
                shop_html += "</div></div>"
        shop_html += "</div>"
    
    # 5. TOTAL ARTIFACTS & HEARTS (Sorted by Name/Tier)
    if global_arts_total:
        shop_html += "<div><h4 class='text-xs font-black text-orange-400 uppercase tracking-widest mb-3 border-b border-[#1E2D45] pb-2'>Artifacts & Hearts</h4>"
        shop_html += f"<div class='flex flex-col gap-1'>"
        for art_name in sorted(global_arts_total.keys()):
            art_qty = global_arts_total[art_name]
            shop_html += f"<span class='bg-[#0A101C] px-3 py-1.5 rounded border border-[#1E2D45] text-[11px] font-mono text-white'><span class='text-orange-400 font-black'>{art_name.upper()}</span>: {get_stack_info(art_qty)}</span>"
        shop_html += "</div></div>"

    shop_html += "</div>"
    
    board["global_shopping_html"] = shop_html

    # TASK 4: Build "Total Raw Resource Needed" summary for REFINE ONLY mode
    if cfg.get("use_refine_only", False):
        ro_html = "<div class='grid grid-cols-1 md:grid-cols-2 gap-6'>"

        # Raw Resources column
        active_raw_ro = {m: {e:q for e,q in encs.items() if q>0} for m, encs in global_raw.items()}
        active_raw_ro = {m: encs for m, encs in active_raw_ro.items() if encs}
        if active_raw_ro:
            ro_html += "<div><h4 class='text-xs font-black text-cyan-400 uppercase tracking-widest mb-3 border-b border-[#1E2D45] pb-2'>Raw Resources Needed</h4>"
            sorted_mats = sorted(active_raw_ro.keys(), key=lambda x: re.search(r'\(T(\d+)\)', x).group(1) if re.search(r'\(T(\d+)\)', x) else x)
            for m in sorted_mats:
                encs = active_raw_ro[m]
                ro_html += f"<div class='mb-3'><span class='text-[11px] font-bold text-gray-400 uppercase block mb-1.5'>{m}</span><div class='flex flex-wrap gap-1.5'>"
                for e, q in sorted(encs.items()):
                    ec = {"0":"enc-0", "1":"enc-1", "2":"enc-2", "3":"enc-3", "4":"enc-4"}.get(e[1:], "text-white")
                    ro_html += f"<span class='bg-[#0A101C] px-2 py-1 rounded border border-[#1E2D45] text-[11px] font-mono'><span class='{ec} font-black'>{e}</span>: {get_stack_info(q)}</span>"
                ro_html += "</div></div>"
            ro_html += "</div>"

        # Under-Refine column
        active_under_ro = {m: {e:q for e,q in encs.items() if q>0} for m, encs in global_under.items()}
        active_under_ro = {m: encs for m, encs in active_under_ro.items() if encs}
        if active_under_ro:
            ro_html += "<div><h4 class='text-xs font-black text-rose-400 uppercase tracking-widest mb-3 border-b border-[#1E2D45] pb-2'>Under-Refine Needed</h4>"
            sorted_mats = sorted(active_under_ro.keys(), key=lambda x: re.search(r'\(T(\d+)\)', x).group(1) if re.search(r'\(T(\d+)\)', x) else x)
            for m in sorted_mats:
                encs = active_under_ro[m]
                ro_html += f"<div class='mb-3'><span class='text-[11px] font-bold text-gray-400 uppercase block mb-1.5'>{m}</span><div class='flex flex-wrap gap-1.5'>"
                if "(T3)" in m:
                    tot = sum(encs.values())
                    ro_html += f"<span class='bg-[#0A101C] px-2 py-1 rounded border border-[#1E2D45] text-[11px] font-mono text-white'>FLAT: {get_stack_info(tot)}</span>"
                else:
                    for e, q in sorted(encs.items()):
                        ec = {"0":"enc-0", "1":"enc-1", "2":"enc-2", "3":"enc-3", "4":"enc-4"}.get(e[1:], "text-white")
                        ro_html += f"<span class='bg-[#0A101C] px-2 py-1 rounded border border-[#1E2D45] text-[11px] font-mono'><span class='{ec} font-black'>{e}</span>: {get_stack_info(q)}</span>"
                ro_html += "</div></div>"
            ro_html += "</div>"

        ro_html += "</div>"
        board["refine_only_summary_html"] = ro_html

    peak_w = 0.0
    for city in royal_cities:
        # Sort Refine and Craft tasks by tier
        board[city]["refine"].sort(key=lambda x: x.get("tier", 4))
        # For craft tasks, we don't always have a 'tier' key at the root, but it's in the text or we can add it
        board[city]["craft"].sort(key=lambda x: (re.search(r'T(\d+)', x['text']).group(1) if re.search(r'T(\d+)', x['text']) else '0', x['text']))

        w_in = board[city]["peak_weight_in"]
        w_out = board[city]["peak_weight_out"]
        if w_in > peak_w: peak_w = w_in
        if w_out > peak_w: peak_w = w_out

    board["peak_weight"] = peak_w
    return board