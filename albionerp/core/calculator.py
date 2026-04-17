import math
import re
import json
import os
from core.constants import *

TIERS = [3, 4, 5, 6, 7, 8]

def clean_art_name(val):
    if not val: return ""
    v = re.sub(r'^T\d+_', '', val, flags=re.IGNORECASE)
    v = re.sub(r'ARTIFACT_', '', v, flags=re.IGNORECASE)
    return v.replace('_', ' ').title()

def sfloat(val):
    try: return float(val) if str(val).strip() != "" else 0.0
    except: return 0.0

def sint(val):
    try: return int(val) if str(val).strip() != "" else 0
    except: return 0

def format_qty(amount):
    amt = math.ceil(amount)
    if amt <= 0: return "0 Pcs"
    stacks = amt // 999
    rem    = amt % 999
    return f"{amt:,} Pcs | {stacks} Stack + {rem}" if stacks > 0 else f"{amt:,} Pcs"

def get_focus_discount(spec):
    efficiency = (spec * 250)
    return 0.5 ** (efficiency / 10000.0)

def get_total_ip(tier, enchant, quality, spec=0, artifact_level=0):
    base_ip = IP_TIER_BASE.get(tier, 700)
    ench_ip = enchant * 100
    qual_ip = IP_QUALITY.get(quality.lower(), 0)
    spec_ip = spec * 2.2 
    art_ip = artifact_level * 25
    return base_ip + ench_ip + qual_ip + spec_ip + art_ip


def calc_luxury_arbitrage(cfg, prices, unit_margins):
    # 🚀 CALCULATE LUXURY ARBITRAGE
    if os.path.exists("database/db_luxury.json"):
        with open("database/db_luxury.json", "rb") as f:
            db_luxury = json.loads(f.read())
        unit_margins["luxury"] = {}
        for lux_id, lux_data in db_luxury.items():
            lux_name = lux_data["name"]; target_city = lux_data["city"]; npc_price = lux_data["price"]; lux_tier = lux_data["tier"]; w = lux_data["weight"]
            buy_p = sfloat(prices.get(cfg.get("buy_city", "Lymhurst"), {}).get(f"t{lux_tier}", {}).get("luxury", {}).get(lux_id, 0))
            if buy_p > 0 and buy_p < npc_price:
                profit = npc_price - buy_p
                if lux_name not in unit_margins["luxury"]: unit_margins["luxury"][lux_name] = {}
                unit_margins["luxury"][lux_name]['.0'] = { "p": int(profit), "pct": round((profit / buy_p) * 100, 1), "foc": 0, "cost": buy_p, "w": w, "t": lux_tier, "city": target_city }

STONE_ENCHANT_MULT = {".0": 1, ".1": 2, ".2": 4, ".3": 8, ".4": 1}

def calc_mat_unit_cost(cfg, prices, do_refine, craft_city, use_multi, fee_r):
    RAW_MAP = {"cloth": "fiber", "leather": "hide", "steel": "ore", "plank": "wood", "block": "stone"}
    mat_unit_cost = {mat: {t: {e: 0 for e in ENCHANTS} for t in TIERS} for mat in RAW_MAP.keys()}
    for mat in RAW_MAP.keys():
        raw_name = RAW_MAP[mat]
        is_stone = (mat == "block")
        c_raw = cfg.get("raw_cities", {}).get(raw_name, "Lymhurst")
        c_ref_unit = cfg.get("refine_cities", {}).get(mat, "Lymhurst") if use_multi else (craft_city or cfg.get("buy_city", "Lymhurst"))
        has_ref_bonus_unit = (c_ref_unit == REFINE_BONUS_CITY.get(mat, ""))
        ref_rrr_unit = (0.539 if has_ref_bonus_unit else 0.435) if cfg.get("focus_refine", False) else (0.367 if has_ref_bonus_unit else 0.152)
        for t_unit in TIERS:
            current_iv_unit = IV_BASE.get(t_unit, 16)
            for e in ENCHANTS:
                if is_stone and e == ".4":
                    mat_unit_cost[mat][t_unit][e] = 0
                    continue
                if do_refine:
                    stone_mult = STONE_ENCHANT_MULT.get(e, 1) if is_stone else 1
                    raw_req = (1.0 - ref_rrr_unit) * RAW_AMOUNT_NEEDED.get(t_unit, 2) * stone_mult
                    under_req = ((1.0 - ref_rrr_unit) * stone_mult) if t_unit > 3 else 0
                    p_raw = sfloat(prices.get(c_raw, {}).get(f"t{t_unit}", {}).get("raw", {}).get(raw_name, {}).get(e, 0))
                    # Stone: under-tier block is ALWAYS .0 (no enchanted blocks exist)
                    under_e = ".0" if is_stone else (e if t_unit > 4 else ".0")
                    p_und = sfloat(prices.get(c_ref_unit, {}).get(f"t{t_unit-1}", {}).get("under", {}).get(mat, {}).get(under_e, 0)) if t_unit > 3 else 0
                    if p_raw == 0 or (t_unit > 3 and p_und == 0): mat_unit_cost[mat][t_unit][e] = 0
                    else:
                        # Stone: output is always .0 block, so fee uses .0 IV mult but scaled by stone_mult
                        fee_iv_mult = IV_MULT[".0"] if is_stone else IV_MULT[e]
                        mat_unit_cost[mat][t_unit][e] = (raw_req * p_raw) + (under_req * p_und) + (current_iv_unit * fee_iv_mult * stone_mult * (fee_r / 100.0) * 0.1125)
                else:
                    # When buying refined: stone blocks are always .0
                    ref_e = ".0" if is_stone else e
                    mat_unit_cost[mat][t_unit][e] = sfloat(prices.get(c_ref_unit, {}).get(f"t{t_unit}", {}).get("ref", {}).get(mat, {}).get(ref_e, 0))
    return mat_unit_cost

def calc_journal_unit_profit(cfg, prices, tax_rate):
    journal_unit_profit = {t: {"fletcher": 0, "imbuer": 0, "blacksmith": 0, "toolmaker": 0} for t in TIERS}
    base_j_city = cfg.get("buy_city", "Lymhurst")
    for t_unit in TIERS:
        for jtype in ["fletcher", "imbuer", "blacksmith", "toolmaker"]:
            p_full = sfloat(prices.get(base_j_city, {}).get(f"t{t_unit}", {}).get("journal", {}).get(jtype, {}).get("full", 0))
            if cfg.get("use_own_journals", False):
                p_empty = float(JOURNAL_NPC_PRICES.get(t_unit, 0))
            else:
                p_empty = sfloat(prices.get(base_j_city, {}).get(f"t{t_unit}", {}).get("journal", {}).get(jtype, {}).get("empty", 0))
            if p_full > 0 and p_empty > 0: journal_unit_profit[t_unit][jtype] = (p_full * (1.0 - tax_rate - 0.025)) - p_empty
    return journal_unit_profit

def calc_max_load(cfg):
    try:
        bag = cfg.get("gear", {}).get("bag", {}); boots = cfg.get("gear", {}).get("boots", {}); mount = cfg.get("gear", {}).get("mount", {}); food = cfg.get("gear", {}).get("food", "none")
        
        bag_type = bag.get("type", "")
        bag_art_lvl = 1 if bag_type == "insight" or "satchel" in bag_type.lower() else 0
        bag_ip = get_total_ip(sint(bag.get("t", 8)), sint(bag.get("e", 0)), bag.get("q", "normal"), 0, bag_art_lvl)
        w_bag = {4: 151, 5: 195, 6: 249, 7: 300, 8: 361}.get(sint(bag.get("t", 8)), 361) * (1.05 ** ((bag_ip - IP_TIER_BASE.get(sint(bag.get("t", 8)), 1100)) / 100.0))
        
        boots_type = boots.get("type", "")
        boots_art_lvl = 0 # Expandable if boots artifact offset is needed
        boots_ip = get_total_ip(sint(boots.get("t", 8)), sint(boots.get("e", 0)), boots.get("q", "normal"), sint(boots.get("s", 106)), boots_art_lvl)
        w_boots = {4: 30, 5: 38, 6: 48, 7: 60, 8: 73}.get(sint(boots.get("t", 8)), 73) * (1.05 ** ((boots_ip - IP_TIER_BASE.get(sint(boots.get("t", 8)), 1100)) / 100.0))
        mount_base_weight = { "ox": {3: 1503, 4: 1655, 5: 1901, 6: 2237, 7: 2667, 8: 3200}, "boar": {3: 500, 4: 640, 5: 782, 6: 985, 7: 1261, 8: 1500}, "bear": {3: 800, 4: 1000, 5: 1231, 6: 1600, 7: 2100, 8: 2704} }.get(mount.get("type", "ox"), {8:3200}).get(sint(mount.get("t", 8)), 3200)
        w_mount = mount_base_weight * (1.25 ** (IP_QUALITY.get(mount.get("q", "normal").lower(), 0) / 100.0))
        max_load = (50.0 + w_bag + w_boots + w_mount) * (1.0 + PIE_MULT.get(food, 0.3))
    except Exception: max_load = 50.0
    return max_load

def execute_calculation(cfg, db, prices):
    global_target_t = int(cfg.get("tier", 4))
    sell_city  = cfg.get("sell_city", "Black Market")
    
    use_multi  = cfg.get("use_multi_refine", True)
    use_multi_tier = cfg.get("use_multi_tier", False) 
    craft_city = "" if use_multi else cfg.get("craft_city", "Lymhurst")
    
    fee_r = sfloat(cfg.get("fee_refine", 0))
    fee_c = sfloat(cfg.get("fee_craft", 0))

    do_refine = cfg.get("do_refine", True)
    do_craft  = cfg.get("do_craft", True)
    use_refine_only = cfg.get("use_refine_only", False)
    if use_refine_only:
        do_craft = False
        do_refine = True

    raw_transport = {mat: {t: {e: 0 for e in ENCHANTS} for t in TIERS} for mat in ["fiber", "hide", "ore", "wood", "stone"]}
    under_refine  = {mat: {t: {e: 0 for e in ENCHANTS} for t in TIERS} for mat in ["cloth", "leather", "steel", "plank", "block"]}
    refine_res    = {mat: {t: {e: 0 for e in ENCHANTS} for t in TIERS} for mat in ["cloth", "leather", "steel", "plank", "block"]}

    j_needed = {"fletcher": {t: 0.0 for t in TIERS}, "imbuer": {t: 0.0 for t in TIERS}, "blacksmith": {t: 0.0 for t in TIERS}, "toolmaker": {t: 0.0 for t in TIERS}}
    
    total_foc = tot_w = 0
    cost_raw_mats = fee_refine_total = fee_craft_total = cost_empty_journals = 0.0
    rev_refined_mats = rev_bm_gears = rev_full_journals = 0.0

    total_craft_foc = 0.0
    total_refine_foc = 0.0
    cost_buy_refined = 0.0
    weight_of_refined_mats = 0.0

    used_artifacts = {}
    cost_artifacts = 0.0
    raw_crafting_data = []
        
    tax_rate = 0.04 if cfg.get("premium_tax", True) else 0.08
    setup_fee_gear = 0.0 if sell_city == "Black Market" else 0.025 

    active_prof = cfg.get("active_profile", "Default")
    profiles_data = cfg.get("profiles", {}).get(active_prof, {})
    main_specs = profiles_data.get("main_specs") or {}

    RAW_MAP = {"cloth": "fiber", "leather": "hide", "steel": "ore", "plank": "wood", "block": "stone"}
    unit_margins = {cat: {} for cat in db.keys()}
    analyzer_margins = {cat: {} for cat in db.keys()}
    

    calc_luxury_arbitrage(cfg, prices, unit_margins)
    calc_luxury_arbitrage(cfg, prices, analyzer_margins)
    
    mat_unit_cost = calc_mat_unit_cost(cfg, prices, do_refine, craft_city, use_multi, fee_r)
    journal_unit_profit = calc_journal_unit_profit(cfg, prices, tax_rate)
    for cat, items in db.items():
        for item_name, item_data in items.items():
            if cat not in unit_margins: unit_margins[cat] = {}
            unit_margins[cat][item_name] = {}
            if cat not in analyzer_margins: analyzer_margins[cat] = {}
            analyzer_margins[cat][item_name] = {}
            
            main_spec_node = ITEM_TO_MAIN_SPEC.get(item_name, "")
            display_t = item_data.get("tier", global_target_t)

            # --- Calculate Focus Discount here for calc_margins_for_tier scope ---
            if cat == "foods":
                spec_val = sint(main_specs.get("Chef", 0))
            elif cat == "potions":
                spec_val = sint(main_specs.get("Alchemist", 0))
            else:
                spec_val = sint(main_specs.get(main_spec_node, 0))
            
            focus_disc_craft = get_focus_discount(spec_val)

            if "tier" in item_data:
                actual_t = item_data["tier"]
            elif use_multi_tier:
                if main_spec_node and main_spec_node in main_specs:
                    node_lvl = sint(main_specs[main_spec_node])
                    if node_lvl >= 100: actual_t = 8
                    elif node_lvl >= 60: actual_t = 7
                    elif node_lvl >= 30: actual_t = 6
                    elif node_lvl >= 10: actual_t = 5
                    else: actual_t = 4
                else: actual_t = global_target_t
            else: actual_t = global_target_t
                
            def calc_margins_for_tier(t_val):
                res = {}
                tier_key = f"t{t_val}"
                current_iv = IV_BASE.get(t_val, 16)
                mat_weight = RESOURCE_WEIGHT.get(t_val, 0.5)

                # Determine production city and focus state
                prod_city = craft_city
                use_focus_unit = cfg.get("focus_craft", False)
                fee_unit = fee_c
                if cfg.get("use_multi_consumables", False) and cfg.get("use_multi_cooking", True):
                    if cat == "foods": 
                        prod_city = cfg.get("cooking_city", craft_city)
                        use_focus_unit = cfg.get("focus_cooking", False)
                        fee_unit = cfg.get("fee_cooking", fee_c)
                    elif cat == "potions": 
                        prod_city = cfg.get("alchemy_city", craft_city)
                        use_focus_unit = cfg.get("focus_alchemy", False)
                        fee_unit = cfg.get("fee_alchemy", fee_c)

                actual_bonus_city = ITEM_BONUS_CITY.get(item_name, "")
                has_craft_bonus_unit = bool(prod_city) and (prod_city == actual_bonus_city)
                res["bonus"] = actual_bonus_city if not prod_city else ("Yes" if has_craft_bonus_unit else "No")
                
                frag_type = FRAGMENT_MAPPING.get(item_name, "")
                if frag_type: res["frag_type"] = frag_type
                
                mats = item_data.get("mats", {})
                j_type = item_data.get("journal", "")
                art_n = item_data.get("artifact", "")
                heart_n = item_data.get("heart", "") 
                y_yield = item_data.get("yield", 1)
                if y_yield <= 0: y_yield = 1
                
                # Determine production city for consumables
                prod_city = craft_city
                if cfg.get("use_multi_consumables", False) and cfg.get("use_multi_cooking", True):
                    if cat == "foods": prod_city = cfg.get("cooking_city", craft_city)
                    elif cat == "potions": prod_city = cfg.get("alchemy_city", craft_city)

                actual_bonus_city = ITEM_BONUS_CITY.get(item_name, "")
                has_craft_bonus_unit = bool(prod_city) and (prod_city == actual_bonus_city)
                res["bonus"] = actual_bonus_city if not prod_city else ("Yes" if has_craft_bonus_unit else "No")

                tot_mats_qty_for_fee = sum(mats.values())
                unit_w = tot_mats_qty_for_fee * mat_weight 
                
                craft_rrr_unit = (0.479 if has_craft_bonus_unit else 0.435) if use_focus_unit else (0.248 if has_craft_bonus_unit else 0.152)

                for e in ENCHANTS:
                    try:
                        sell_p = sfloat(prices.get(sell_city, {}).get(tier_key, {}).get("crafted", {}).get(cat, {}).get(item_name, {}).get(e, 0))
                        
                        cost_mats = 0; has_missing_mat = False; has_missing_flat_mat = False; route_flat_mat_cost = 0; route_ench_mat_cost = 0; uses_fragments = False
                        
                        for mat_name, mat_qty in mats.items():
                            if mat_name in FARMING_MATS_MAPPING.values():
                                # Multi-city farming lookup
                                farm_buy_city = cfg.get("buy_city", "Lymhurst")
                                if cfg.get("use_multi_consumables", False) and cfg.get("use_multi_farming", True):
                                    # PRIORITAS 1: Bonus City Mapping (FARMING YIELD)
                                    bonus_farm_city = FARMING_BONUS_CITY.get(mat_name)
                                    if bonus_farm_city:
                                        farm_buy_city = bonus_farm_city
                                    else:
                                        # Fallback to category based config
                                        f_cat = "crops"
                                        for fc, flist in FARMING_GROUPS.items():
                                            if mat_name in flist: f_cat = fc; break
                                        farm_buy_city = cfg.get("farming_buy_cities", {}).get(f_cat, farm_buy_city)

                                p_farm = 0
                                for t_f in range(1, 9):
                                    city_prices = prices.get(farm_buy_city, {}).get(f"t{t_f}", {})
                                    farm_prices = city_prices.get("farming_mats", {})
                                    p_f = sfloat(farm_prices.get(mat_name, 0))
                                    if p_f > 0: p_farm = p_f; break
                                if p_farm == 0: has_missing_mat = True; has_missing_flat_mat = True
                                cost_mats += (mat_qty * (1.0 - craft_rrr_unit)) * p_farm
                                route_ench_mat_cost += (mat_qty * (1.0 - craft_rrr_unit)) * p_farm
                                route_flat_mat_cost += (mat_qty * (1.0 - craft_rrr_unit)) * p_farm
                            else:
                                mat_costs = mat_unit_cost.get(mat_name)
                                if mat_costs is None:
                                    has_missing_mat = True
                                    print(f"WARNING: Material '{mat_name}' for '{item_name}' not found in any mapping.")
                                    continue
                                
                                if mat_costs[t_val][e] == 0: has_missing_mat = True
                                if mat_costs[t_val]['.0'] == 0: has_missing_flat_mat = True
                                route_ench_mat_cost += (mat_qty * (1.0 - craft_rrr_unit)) * mat_costs[t_val][e]
                                route_flat_mat_cost += (mat_qty * (1.0 - craft_rrr_unit)) * mat_costs[t_val]['.0']

                        frag_cost_total = 0
                        if y_yield == 1 and e in ['.1', '.2', '.3'] and not has_missing_flat_mat:
                            base_frag_qty = tot_mats_qty_for_fee * FRAG_PER_MAT.get(t_val, 3.0)
                            p_rune = sfloat(prices.get(cfg.get("frag_cities", {}).get("rune", cfg.get("buy_city", "Lymhurst")), {}).get(tier_key, {}).get("fragments", {}).get("rune", 0))
                            p_soul = sfloat(prices.get(cfg.get("frag_cities", {}).get("soul", cfg.get("buy_city", "Lymhurst")), {}).get(tier_key, {}).get("fragments", {}).get("soul", 0))
                            p_relic = sfloat(prices.get(cfg.get("frag_cities", {}).get("relic", cfg.get("buy_city", "Lymhurst")), {}).get(tier_key, {}).get("fragments", {}).get("relic", 0))
                            if e == '.1': frag_cost_total = base_frag_qty * p_rune
                            elif e == '.2': frag_cost_total = base_frag_qty * (p_rune + p_soul)
                            elif e == '.3': frag_cost_total = base_frag_qty * (p_rune + p_soul + p_relic)
                            if frag_cost_total > 0 and (has_missing_mat or (route_flat_mat_cost + frag_cost_total) < route_ench_mat_cost): 
                                cost_mats = route_flat_mat_cost + frag_cost_total
                                uses_fragments = True
                                has_missing_mat = False
                            else: cost_mats = route_ench_mat_cost
                        elif y_yield == 1:
                            cost_mats = route_ench_mat_cost

                        ench_mat_base = item_data.get("enchant_mat")
                        p_e_mat = 0
                        if ench_mat_base and e in ['.1', '.2', '.3']:
                            e_mat = f"{ench_mat_base}_{e}"
                            for t_f in range(1, 9):
                                p_f = sfloat(prices.get(cfg.get("buy_city", "Lymhurst"), {}).get(f"t{t_f}", {}).get("farming_mats", {}).get(e_mat, 0))
                                if p_f > 0: p_e_mat = p_f; break
                            if p_e_mat == 0: has_missing_mat = True
                            cost_mats += 15 * p_e_mat

                        cost_mats = cost_mats / y_yield
                        unit_w_final = unit_w / y_yield if y_yield > 1 else unit_w

                        art_cost = 0; heart_cost = 0
                        if art_n:
                            art_tk = tier_key; art_qty = 1
                            if "crest" in art_n.lower(): art_qty = {4: 1, 5: 1, 6: 3, 7: 5, 8: 10}.get(t_val, 1)
                            if art_n == "tome_experience": art_tk = "t4"
                            art_p = sfloat(prices.get(cfg.get("buy_city", "Lymhurst"), {}).get(art_tk, {}).get("artifacts", {}).get(art_n, 0))
                            if art_p == 0 and frag_type:
                                c_frag = cfg.get("frag_cities", {}).get(frag_type.lower(), cfg.get("buy_city", "Lymhurst"))
                                frag_p = sfloat(prices.get(c_frag, {}).get(tier_key, {}).get("fragments", {}).get(frag_type.lower(), 0))
                                if frag_p > 0: art_p = frag_p * 50
                            if art_p == 0: has_missing_mat = True
                            art_cost = (art_p * art_qty)
                            cost_mats += art_cost / y_yield

                        if heart_n:
                            h_qty = 15 if heart_n == "token_avalon" else 1
                            heart_p = sfloat(prices.get(cfg.get("buy_city", "Lymhurst"), {}).get("t4", {}).get("artifacts", {}).get(heart_n, 0))
                            if heart_p == 0: has_missing_mat = True
                            heart_cost = (heart_p * h_qty)
                            cost_mats += heart_cost / y_yield

                        gear_iv = tot_mats_qty_for_fee * current_iv * IV_MULT[e]
                        craft_fee_1 = gear_iv * (sfloat(fee_unit) / 100.0) * 0.1125 / y_yield
                        
                        j_profit = 0
                        if j_type in journal_unit_profit.get(t_val, {}):
                            j_profit = ((tot_mats_qty_for_fee * FAME_PER_RESOURCE.get(t_val, 22.5) * ENCHANT_FAME_MULT.get(e, 1)) / JOURNAL_FAME_REQ.get(t_val, 3600)) * journal_unit_profit[t_val][j_type] / y_yield
                        
                        total_cost = cost_mats + craft_fee_1
                        
                        if sell_p == 0:
                            res[e] = {"p": 0, "pct": 0, "foc": 0, "cost": 0, "w": round(unit_w_final, 2), "t": t_val, "uses_fragments": False, "frag_cost": 0, "art_cost": 0, "heart_cost": 0, "potion_ench_cost": 0, "y": y_yield}
                            continue
                            
                        net_sell = sell_p * (1.0 - tax_rate - setup_fee_gear)
                        margin = net_sell - total_cost + j_profit
                        pct = (margin / total_cost * 100) if total_cost > 0 else 0

                        denom = ((gear_iv * focus_disc_craft * 0.1) / y_yield)
                        foc_val = round((margin / denom * 10000), 2) if denom > 0 else 0

                        res[e] = {"p": round(margin, 2), "pct": round(pct, 2), "foc": foc_val, "cost": round(total_cost - j_profit, 2), "w": round(unit_w_final, 2), "t": t_val, "uses_fragments": uses_fragments, "frag_cost": round(frag_cost_total, 2), "art_cost": round(art_cost, 2), "heart_cost": round(heart_cost, 2), "potion_ench_cost": round(15 * p_e_mat, 2), "y": y_yield}
                    except Exception as e_inner:
                        res[e] = {"p": 0, "pct": 0, "foc": 0, "cost": 0, "w": 0, "t": t_val, "uses_fragments": False, "frag_cost": 0, "art_cost": 0, "heart_cost": 0, "potion_ench_cost": 0, "y": y_yield}
                        print(f"Error calculating margin for {item_name} {e}: {e_inner}")
                return res

            res_display = calc_margins_for_tier(display_t)
            unit_margins[cat][item_name] = res_display
            
            if display_t == actual_t:
                analyzer_margins[cat][item_name] = res_display
            else:
                analyzer_margins[cat][item_name] = calc_margins_for_tier(actual_t)

    if use_refine_only:
        r_mat = cfg.get("refine_only_mat", "cloth")
        r_tier = sint(cfg.get("tier", 4))
        qty_conf = { ".0": sint(cfg.get("q0", 0)), ".1": sint(cfg.get("q1", 0)), ".2": sint(cfg.get("q2", 0)), ".3": sint(cfg.get("q3", 0)), ".4": sint(cfg.get("q4", 0)) }
        for e, q in qty_conf.items():
            if q > 0:
                refine_res[r_mat][r_tier][e] += q
        # HARD ISOLATE: Skip entire crafting loop in refine-only mode
        raw_crafting_data = []
    elif True:
        for cat, items in db.items():
            if cat not in ["foods", "potions", "helmets", "armors", "shoes", "offhands", "weapons", "bags", "capes", "artifact_helmets", "artifact_armors", "artifact_shoes", "artifact_offhands", "artifact_weapons", "artifact_bags", "artifact_capes"]:
                continue

            for item_name, item_data in items.items():
                # Consumables have fixed tier in DB
                is_cons_cat = cat in ["foods", "potions"]
                use_multi_cons = cfg.get("use_multi_consumables", False)

                if is_cons_cat:
                    actual_t = item_data.get("tier", 4)
                else:
                    main_spec_node = ITEM_TO_MAIN_SPEC.get(item_name, "")
                    if "tier" in item_data:
                        actual_t = item_data["tier"]
                    elif use_multi_tier:
                        if main_spec_node and main_spec_node in main_specs:
                            node_lvl = sint(main_specs[main_spec_node])
                            if node_lvl >= 100: actual_t = 8
                            elif node_lvl >= 60: actual_t = 7
                            elif node_lvl >= 30: actual_t = 6
                            elif node_lvl >= 10: actual_t = 5
                            else: actual_t = 4
                        else: actual_t = global_target_t
                    else: actual_t = global_target_t
                    
                tier_key = f"t{actual_t}"
                current_iv = IV_BASE.get(actual_t, 16)
                mat_weight = RESOURCE_WEIGHT.get(actual_t, 0.5)

                item_selection = cfg.get("selected_items", {}).get(item_name)
                if not item_selection: continue
                if not isinstance(item_selection, dict):
                    val = item_selection if isinstance(item_selection, bool) else True
                    item_selection = {e: val for e in ENCHANTS}
                
                qty_conf = { ".0": sint(cfg.get("q0", 0)), ".1": sint(cfg.get("q1", 0)), ".2": sint(cfg.get("q2", 0)), ".3": sint(cfg.get("q3", 0)), ".4": sint(cfg.get("q4", 0)) }
                mats = item_data.get("mats", {})
                j_type = item_data.get("journal", "")
                art_name = item_data.get("artifact", "")
                heart_name = item_data.get("heart", "") 
                y_yield = item_data.get("yield", 1)

                actual_bonus_city = ITEM_BONUS_CITY.get(item_name, "")
                
                # Determine hub, focus state and fee for this specific loop
                prod_city = craft_city
                use_focus = cfg.get("focus_craft", False)
                fee_unit = fee_c
                
                if use_multi_cons and cfg.get("use_multi_cooking", True):
                    if cat == "foods":
                        prod_city = cfg.get("cooking_city", craft_city)
                        use_focus = cfg.get("focus_cooking", False)
                        fee_unit = cfg.get("fee_cooking", fee_c)
                        spec_val = sint(main_specs.get("Chef", 0))
                    elif cat == "potions":
                        prod_city = cfg.get("alchemy_city", craft_city)
                        use_focus = cfg.get("focus_alchemy", False)
                        fee_unit = cfg.get("fee_alchemy", fee_c)
                        spec_val = sint(main_specs.get("Alchemist", 0))
                    else:
                        spec_val = sint(main_specs.get(main_spec_node, 0))
                else:
                    spec_val = sint(main_specs.get(main_spec_node, 0))

                has_craft_bonus = bool(prod_city) and (prod_city == actual_bonus_city)
                if use_focus: c_rrr = 0.479 if has_craft_bonus else 0.435
                else: c_rrr = 0.248 if has_craft_bonus else 0.152

                focus_disc_craft = get_focus_discount(spec_val)

                c_crafts = cfg.get("cancelled_crafts") or {}
                i_crafts = c_crafts.get(item_name) or {}
                a_crafts = cfg.get("adjusted_qty_crafts") or {}
                i_adj_crafts = a_crafts.get(item_name) or {}

                for e in ENCHANTS:
                    if not item_selection.get(e, False): continue
                    
                    override_q = i_adj_crafts.get(e)
                    q = sint(override_q) if override_q is not None else qty_conf[e]
                    if q <= 0: continue

                    is_cancelled = i_crafts.get(e, False)
                    out_qty = q * y_yield
                    
                    frag_type = FRAGMENT_MAPPING.get(item_name, "")
                    meld_cat = {"blacksmith": "Warrior's", "fletcher": "Hunter's", "imbuer": "Mage's", "toolmaker": "Tinker's"}.get(j_type, "")
                    art_display = f"{meld_cat} {frag_type.title()} Artifact" if frag_type and meld_cat else clean_art_name(art_name)

                    sell_p = sfloat(prices.get(sell_city, {}).get(tier_key, {}).get("crafted", {}).get(cat, {}).get(item_name, {}).get(e, 0))
                    net_sell = sell_p * (1.0 - tax_rate - setup_fee_gear)
                    
                    tot_mats_qty_for_fee = sum(mats.values())
                    gear_iv = tot_mats_qty_for_fee * current_iv * IV_MULT[e]
                    
                    fame_earned = tot_mats_qty_for_fee * FAME_PER_RESOURCE.get(actual_t, 22.5) * ENCHANT_FAME_MULT.get(e, 1) * q
                    j_amount_float = fame_earned / JOURNAL_FAME_REQ.get(actual_t, 3600)

                    unit_data = analyzer_margins.get(cat, {}).get(item_name, {}).get(e, {})
                    uses_fragments = unit_data.get("uses_fragments", False)
                    
                    if not is_cancelled:
                        cost_artifacts += (unit_data.get("frag_cost", 0) * q)
                        cost_artifacts += (unit_data.get("potion_ench_cost", 0) * q)

                    for mat_name, mat_qty in mats.items():
                        if mat_name in FARMING_MATS_MAPPING.values():
                            req_mats = q * mat_qty * (1.0 - c_rrr)
                            if not is_cancelled:
                                # Use logic-based f_buy_city for the price lookup
                                f_buy_city = cfg.get("buy_city", "Lymhurst")
                                if use_multi_cons and cfg.get("use_multi_farming", True):
                                    bonus_farm_city = FARMING_BONUS_CITY.get(mat_name)
                                    if bonus_farm_city: f_buy_city = bonus_farm_city
                                    else:
                                        f_cat = "crops"
                                        for fc, flist in FARMING_GROUPS.items():
                                            if mat_name in flist: f_cat = fc; break
                                        f_buy_city = cfg.get("farming_buy_cities", {}).get(f_cat, f_buy_city)

                                p_farm = 0
                                for t_f in range(1, 9):
                                    p_f = sfloat(prices.get(f_buy_city, {}).get(f"t{t_f}", {}).get("farming_mats", {}).get(mat_name, 0))
                                    if p_f > 0: p_farm = p_f; break
                                cost_raw_mats += (req_mats * p_farm)
                        else:
                            req_mats = q * mat_qty * (1.0 - c_rrr)
                            if mat_name in refine_res: 
                                target_e = '.0' if uses_fragments else e
                                refine_res[mat_name][actual_t][target_e] += req_mats
                        
                    w_in = sum(q * m_qty * (1.0 - c_rrr) * mat_weight for m_name, m_qty in mats.items())
                    weight_of_refined_mats += w_in
                    w_out = out_qty * (tot_mats_qty_for_fee * mat_weight / y_yield) if y_yield > 1 else q * tot_mats_qty_for_fee * mat_weight

                    REFINED_LIST = ["cloth", "leather", "steel", "plank", "block"]
                    mats_display = {mn: mn.title() + (f" T{actual_t}" if mn.lower() in REFINED_LIST else "") for mn in mats.keys()}

                    base_mat_str = ", ".join([f"{q * m_qty} {mats_display[m_name]}" for m_name, m_qty in mats.items()])
                    req_mat_str = ", ".join([f"{math.ceil(q * m_qty * (1.0 - c_rrr)):,} {mats_display[m_name]}" for m_name, m_qty in mats.items()])
                    
                    if not is_cancelled:
                        rev_bm_gears += (net_sell * out_qty)
                        tot_w += w_out

                        if art_name:
                            if art_name not in used_artifacts: used_artifacts[art_name] = art_display
                            art_tk = tier_key; art_qty = 1
                            if "crest" in art_name.lower(): art_qty = {4: 1, 5: 1, 6: 3, 7: 5, 8: 10}.get(actual_t, 1)
                            if art_name == "tome_experience": art_tk = "t4"
                            art_p = sfloat(prices.get(cfg.get("buy_city", "Lymhurst"), {}).get(art_tk, {}).get("artifacts", {}).get(art_name, 0))
                            
                            if art_p == 0:
                                frag_low = frag_type.lower()
                                if frag_low:
                                    c_frag = cfg.get("frag_cities", {}).get(frag_low, cfg.get("buy_city", "Lymhurst"))
                                    frag_p = sfloat(prices.get(c_frag, {}).get(tier_key, {}).get("fragments", {}).get(frag_low, 0))
                                    if frag_p > 0: art_p = frag_p * 50
                            cost_artifacts += (art_p * art_qty * q)
                            frag_str = f" <span class='text-purple-400 font-bold'>(Atau Gacha: {q * art_qty * 50} {frag_type.title()})</span>" if frag_type else ""
                            req_mat_str += f", {q * art_qty} {art_display}{frag_str}"
                            base_mat_str += f", {q * art_qty} {art_display}"

                        if heart_name:
                            if heart_name not in used_artifacts: used_artifacts[heart_name] = clean_art_name(heart_name)
                            h_qty = 15 if heart_name == "token_avalon" else 1
                            heart_p = sfloat(prices.get(cfg.get("buy_city", "Lymhurst"), {}).get("t4", {}).get("artifacts", {}).get(heart_name, 0))
                            cost_artifacts += (heart_p * h_qty * q)
                            req_mat_str += f", {q * h_qty} {clean_art_name(heart_name)}"
                            base_mat_str += f", {q * h_qty} {clean_art_name(heart_name)}"

                        if use_focus:
                            base_craft_focus = tot_mats_qty_for_fee * current_iv * IV_MULT[e]
                            craft_foc = (q * base_craft_focus * focus_disc_craft * 0.1)
                            total_craft_foc += craft_foc
                            total_foc += craft_foc

                        craft_fee = (gear_iv * (fee_unit / 100.0) * 0.1125) * q
                        fee_craft_total += craft_fee

                        if j_type in j_needed:
                            j_needed[j_type][actual_t] += j_amount_float

                    # Determine enchantment for materials (use .0 if upgrade path is cheapest)
                    m_enc = ".0" if uses_fragments else e
                    mats_dict_val = {mats_display[mn]: {m_enc: math.ceil(q * mq * (1.0 - c_rrr))} for mn, mq in mats.items()}
                    
                    # Add Artifacts/Hearts to the manifest checklist
                    if not is_cancelled:
                        if art_name:
                            mats_dict_val[art_display] = { ".0": q * art_qty }
                        if heart_name:
                            mats_dict_val[clean_art_name(heart_name)] = { ".0": q * h_qty }
                        
                        # Add Upgrade Fragments if this is the cheapest path
                        if uses_fragments:
                            base_frag_count = math.ceil(q * tot_mats_qty_for_fee * FRAG_PER_MAT.get(actual_t, 3.0))
                            if e >= ".1": mats_dict_val[f"Rune T{actual_t}"] = { ".0": base_frag_count }
                            if e >= ".2": mats_dict_val[f"Soul T{actual_t}"] = { ".0": base_frag_count }
                            if e >= ".3": mats_dict_val[f"Relic T{actual_t}"] = { ".0": base_frag_count }

                    upgrade_details = ""
                    if uses_fragments:
                        steps = ".0 -> " + e
                        frags = []
                        if e >= ".1": frags.append("Rune")
                        if e >= ".2": frags.append("Soul")
                        if e >= ".3": frags.append("Relic")
                        upgrade_details = f"[UPGRADE: {steps} ({'+'.join(frags)})]"
                    
                    upgrade_prefix = f"<span class='text-amber-400 font-bold'>{upgrade_details}</span> " if upgrade_details else ""

                    raw_crafting_data.append({
                        "item": item_name, "enchant": e, "qty": q, "tier": actual_t,
                        "is_cancelled": is_cancelled, "fame": fame_earned, "main_node": main_spec_node,       
                        "mats_str": f"{upgrade_prefix}{req_mat_str}<br><span class='text-[10px] text-gray-500 mt-1 block'>*Syarat Tas (Batch): {base_mat_str}</span>", 
                        "journal": j_type.title() if j_type else "", "j_amount": j_amount_float if not is_cancelled else 0,
                        "mats_dict": mats_dict_val, "weight_in": w_in, "weight_out": w_out if not is_cancelled else 0,
                        "out_qty": out_qty
                    })

    RAW_MAP = {"cloth": "fiber", "leather": "hide", "steel": "ore", "plank": "wood", "block": "stone"}
    raw_refine_data = []

    for mat, tiers in refine_res.items():
        raw_name = RAW_MAP[mat]
        current_tier_spec = sint(profiles_data.get(raw_name, {}).get("s", 0))
        focus_disc_refine = get_focus_discount(current_tier_spec)
        c_ref = cfg.get("refine_cities", {}).get(mat, "Lymhurst") if use_multi else (craft_city or cfg.get("buy_city", "Lymhurst"))
        has_ref_bonus = (c_ref == REFINE_BONUS_CITY.get(mat, ""))
        
        if cfg.get("focus_refine", False): r_rrr = 0.539 if has_ref_bonus else 0.435
        else: r_rrr = 0.367 if has_ref_bonus else 0.152

        for t_ref, enchants in tiers.items():
            current_iv_ref = IV_BASE.get(t_ref, 16)
            mat_weight_ref = RESOURCE_WEIGHT.get(t_ref, 0.5)
            tier_key_ref = f"t{t_ref}"
            
            for e, needed in enchants.items():
                if needed <= 0: continue
                is_stone = (mat == "block")
                stone_mult = STONE_ENCHANT_MULT.get(e, 1) if is_stone else 1

                # Stone: enchantment multiplies quantities, output is ALWAYS .0 block
                actual_needed = needed * stone_mult
                raw_qty = actual_needed * (1.0 - r_rrr) * RAW_AMOUNT_NEEDED.get(t_ref, 2)
                under_qty = actual_needed * (1.0 - r_rrr) if t_ref > 3 else 0
                # Stone: under-tier block is always .0 (no enchanted blocks)
                eu = ".0" if is_stone else (e if t_ref > 4 else ".0")
                base_raw = actual_needed * RAW_AMOUNT_NEEDED.get(t_ref, 2)
                base_under = actual_needed if t_ref > 3 else 0
                # Stone: output enchant key forced to .0
                out_enchant = ".0" if is_stone else e

                raw_transport[raw_name][t_ref][e] += raw_qty
                if t_ref > 3: under_refine[mat][t_ref][eu] += under_qty

                c_raw = cfg.get("raw_cities", {}).get(raw_name, "Lymhurst")
                p_raw = sfloat(prices.get(c_raw, {}).get(tier_key_ref, {}).get("raw", {}).get(raw_name, {}).get(e, 0))
                p_und = 0
                if t_ref > 3:
                    p_und = sfloat(prices.get(c_ref, {}).get(f"t{t_ref-1}", {}).get("under", {}).get(mat, {}).get(eu, 0))

                cost_raw_mats += (raw_qty * p_raw) + (under_qty * p_und)
                # Stone: fee IV mult is always .0 since output is .0 blocks
                fee_iv_mult = IV_MULT[".0"] if is_stone else IV_MULT[e]
                fee_refine_total += (actual_needed * current_iv_ref * fee_iv_mult * (fee_r / 100.0) * 0.1125)

                # Stone: revenue uses .0 ref price (no enchanted blocks in market)
                p_ref = sfloat(prices.get(c_ref, {}).get(tier_key_ref, {}).get("ref", {}).get(mat, {}).get(out_enchant, 0))
                rev_refined_mats += (actual_needed * p_ref) * (1.0 - tax_rate - 0.025)
                cost_buy_refined += actual_needed * p_ref

                if cfg.get("focus_refine", False):
                    ref_foc = (actual_needed * (current_iv_ref * fee_iv_mult) * focus_disc_refine * 0.5)
                    total_refine_foc += ref_foc
                    total_foc += ref_foc

                raw_refine_data.append({
                    "mat": mat, "tier": t_ref, "enchant": e, "qty": actual_needed,
                    "weight_in": raw_qty * mat_weight_ref, "weight_out": actual_needed * mat_weight_ref,
                    "raw_name": raw_name, "raw_qty": raw_qty, "under_qty": under_qty, "under_enchant": eu,
                    "out_qty": actual_needed, "out_enchant": out_enchant,
                    "fame": actual_needed * FAME_PER_RESOURCE.get(t_ref, 22.5) * ENCHANT_FAME_MULT.get(e, 1),
                    "base_raw": base_raw, "base_under": base_under,
                    "stone_mult": stone_mult if is_stone else 1
                })


    max_load = calc_max_load(cfg)
    if not do_refine:
        cost_raw_mats = cost_buy_refined; fee_refine_total = 0; raw_refine_data = []; total_foc -= total_refine_foc; rev_refined_mats = cost_buy_refined
    if not do_craft:
        rev_bm_gears = rev_refined_mats; fee_craft_total = 0; cost_artifacts = 0; raw_crafting_data = []; j_needed = {k: {t: 0 for t in TIERS} for k in j_needed}; total_foc -= total_craft_foc; tot_w = weight_of_refined_mats
    else:
        for t_j in TIERS:
            for jt in ["fletcher", "imbuer", "blacksmith", "toolmaker"]:
                qty = j_needed.get(jt, {}).get(t_j, 0)
                if qty > 0:
                    p_full = sfloat(prices.get(cfg.get("buy_city", "Lymhurst"), {}).get(f"t{t_j}", {}).get("journal", {}).get(jt, {}).get("full", 0))
                    if cfg.get("use_own_journals", False):
                        p_empty = float(JOURNAL_NPC_PRICES.get(t_j, 0))
                    else:
                        p_empty = sfloat(prices.get(cfg.get("buy_city", "Lymhurst"), {}).get(f"t{t_j}", {}).get("journal", {}).get(jt, {}).get("empty", 0))
                    cost_empty_journals += (qty * p_empty)
                    rev_full_journals += (qty * p_full * (1.0 - tax_rate - 0.025))

    profit_refine = rev_refined_mats - cost_raw_mats - fee_refine_total if do_refine else 0
    profit_bm = rev_bm_gears - rev_refined_mats - fee_craft_total - cost_artifacts if do_craft else 0
    profit_journals = rev_full_journals - cost_empty_journals if do_craft else 0
    
    formatted_journals = {f"{jt.title()} T{t_j}": math.ceil(qty) for jt, tiers_dict in j_needed.items() for t_j, qty in tiers_dict.items() if qty > 0}

    return {
        "weight_data": {"total_kg": round(tot_w, 1), "percentage": min(round((tot_w / max_load) * 100, 1), 100), "is_overweight": tot_w > max_load, "max_load": round(max_load, 1)},
        "focus_data": {"used": math.ceil(max(total_foc, 0)), "remaining": 30000 - math.ceil(max(total_foc, 0)), "is_overcap": max(total_foc, 0) > 30000},
        "financial": {"cost_raw_mats": int(cost_raw_mats), "cost_artifacts": int(cost_artifacts), "fee_refine": int(fee_refine_total), "fee_craft": int(fee_craft_total), "cost_journals": int(cost_empty_journals), "total_capital": int(cost_raw_mats + fee_refine_total + fee_craft_total + cost_empty_journals + cost_artifacts), "profit_refine": int(profit_refine), "profit_bm": int(profit_bm), "profit_journals": int(profit_journals), "grand_profit": int(profit_refine + profit_bm + profit_journals)},
        "used_artifacts": used_artifacts, "unit_margins": unit_margins, "analyzer_margins": analyzer_margins,
        "raw_crafting_data": raw_crafting_data, "raw_refine_data": raw_refine_data, "journals": formatted_journals
    }
