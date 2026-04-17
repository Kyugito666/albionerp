import {
    ITEM_NAMES_MAP, ALL_ROYAL_CITIES, ALL_SELL_CITIES, JOURNAL_TYPES, MAT_LIST, FARMING_MATS_LIST, SPEC_NODES,
    banditScheduleUTC, CITY_NEIGHBORS, RAW_OF, ENCHANT_COLORS, CHART_DEFAULTS, raw_crops, raw_herbs, raw_meat, animal_products, processed_ingredients, enchantments,
    CREST_HEART_LIST, TOME_OF_INSIGHT_TIERS
} from './constants.js';import { getRealName, levelToFame, fameToLevel, formatK, getStackInfo, getBMBaseVolume } from './utils.js';
import { setupAnalyzer } from './analyzer.js';

const { createApp, ref, computed, onMounted, nextTick, watch } = Vue;

createApp({
    setup() {
        const activeTab           = ref('dashboard');
        const showLogMenu         = ref(false);
        const showMainMenu        = ref(false);
        const showLogisticsSubMenu = ref(false);
        const showPriceSubMenu    = ref(false);
        const showListItemSubMenu = ref(false);
        const activePriceTab      = ref('materials'); 
        const activeListItemTab   = ref('gear');
        const currentTimeFormatted = ref('');
        const nextBanditStr       = ref('Calculating...');
        const acc                 = ref({});
        const data                = ref(null);
        const pricesData          = ref({});
        const isFetchingADC       = ref(false);
        const isSyncingScanned    = ref(false);
        const showProfitSpread    = ref(false); 
        const expandedLogs        = ref({}); 

        // 🔔 TOAST NOTIFICATION SYSTEM
        const notification = ref({ show: false, title: '', message: '', type: 'info', timeout: null });
        const showToast = (title, message, type = 'info', duration = 5000) => {
            if (notification.value.timeout) clearTimeout(notification.value.timeout);
            notification.value = { 
                show: true, title, message, type, 
                timeout: setTimeout(() => { notification.value.show = false; }, duration) 
            };
        };

        
        const tabLabels = {
            'dashboard': 'DASHBOARD',
            'logistics_refine': 'Raw To Refine',
            'logistics_craft': 'Refine To Craft',
            'logistics_consumables': 'Cooking & Alchemy',
            'logistics_luxury': 'Luxury Goods',
            'prices': 'PRICE DB',
            'list_item': 'LIST ITEM',
            'consumables': 'CONSUMABLES SETUP',
            'volume': 'VOLUME',
            'logs': 'TRADING LOGS'
        };
        const activeTabLabel = computed(() => tabLabels[activeTab.value] || activeTab.value.toUpperCase());

        const sortKey = ref('profit');
        const sortDesc = ref(true);
        const toggleSort = (key) => {
            if (sortKey.value === key) {
                sortDesc.value = !sortDesc.value;
            } else {
                sortKey.value = key;
                sortDesc.value = true;
            }
        };

        const isItemSelected = (itemName) => {
            const val = cfg.value.selected_items[itemName];
            if (typeof val === 'object' && val !== null) return Object.values(val).some(v => v);
            return !!val;
        };

        const toggleItem = (itemName) => {
            const current = isItemSelected(itemName);
            const target = !current;
            // Whole-object assignment to ensure deep reactivity detection
            cfg.value.selected_items[itemName] = { '.0': target, '.1': target, '.2': target, '.3': target, '.4': target };
            saveAndFetch();
        };

        const checkAccess = (targetTab, subType = '') => {
            const isConsMode = cfg.value.use_multi_consumables;
            let error = null;
            
            // LOGISTICS ENGINE ACCESS
            if (targetTab === 'logistics_refine') {
                if (isConsMode) error = "Tersedia saat 'Cooking & Alchemy Mode' OFF.";
                else if (cfg.value.use_refine_only) error = null;
                else if (cfg.value.do_refine === false) error = "Aktifkan 'REFINE ON' di Dashboard.";
            }
            else if (targetTab === 'logistics_craft') {
                if (isConsMode) error = "Tersedia saat 'Cooking & Alchemy Mode' OFF.";
                else if (cfg.value.use_refine_only) error = "Mode 'REFINE ONLY' aktif. Matikan untuk akses Crafting.";
                else if (cfg.value.do_craft === false) error = "Aktifkan 'CRAFT ON' di Dashboard.";
            }
            else if (targetTab === 'logistics_consumables') {
                if (!isConsMode) error = "Tersedia saat 'Cooking & Alchemy Mode' ON.";
            }

            // LIST ITEM ACCESS
            else if (targetTab === 'list_item') {
                if (subType === 'gear') {
                    if (isConsMode) error = "Tersedia saat 'Cooking & Alchemy Mode' OFF.";
                    else if (cfg.value.do_craft === false) error = "Aktifkan 'CRAFT ON' di Dashboard.";
                }
                else if (subType === 'consumable') {
                    if (!isConsMode) error = "Tersedia saat 'Cooking & Alchemy Mode' ON.";
                }
            }

            if (error) {
                return { allowed: false, reason: error };
            }
            return { allowed: true };
        };

        const cfg = ref({
            farming_tier: 4, tier: 4, q0: 0, q1: 0, q2: 0, q3: 0, q4: 0,
            qty_gear: { q0: 0, q1: 0, q2: 0, q3: 0, q4: 0 },
            qty_refine: { q0: 0, q1: 0, q2: 0, q3: 0, q4: 0 },
            qty_cook: { q0: 0, q1: 0, q2: 0, q3: 0, q4: 0 },
            selected_items: {},
            buy_city: "Lymhurst", sell_city: "Black Market", craft_city: "Lymhurst", route_from: "Lymhurst", route_to: "Fort Sterling",
            raw_cities: { fiber: "Thetford", hide: "Bridgewatch", ore: "Fort Sterling", wood: "Lymhurst", stone: "Bridgewatch" },
            refine_cities: { cloth: "Lymhurst", leather: "Martlock", steel: "Thetford", plank: "Fort Sterling", block: "Bridgewatch" },
            frag_cities: { rune: "Lymhurst", soul: "Lymhurst", relic: "Lymhurst" },
            tome_city: "Lymhurst", 
            gear: { bag: { t: 8, e: 0, q: 'normal' }, boots: { t: 8, e: 0, q: 'normal', s: 106 }, mount: { type: 'ox', t: 8, q: 'normal' }, food: 'pie_7_0' },
            focus_refine: true, focus_craft: false, focus_cooking: false, focus_alchemy: false, premium_tax: true, fee_refine: 0, fee_craft: 0, fee_cooking: 0, fee_alchemy: 0, use_own_journals: true,
            do_refine: true, do_craft: true, use_multi_refine: true, multi_refine_only_mode: true, use_multi_tier: false,
            cancelled_crafts: {}, 
            adjusted_qty_crafts: {}, 
            smart_budget: 16000000, 
            ai_settings: {
                max_items: 10,
                min_profit: 1000,
                min_margin: 15,
                vol_target: 20, 
                item_type: 'both',
                enc: { '.0': true, '.1': true, '.2': true, '.3': true, '.4': false }
            },
            active_profile: "Default", profiles: { "Default": { fiber:{s:100}, hide:{s:100}, ore:{s:100}, wood:{s:100}, stone:{s:100}, main_specs: {}, fame_exact: {} } }, specs: { fiber:{s:100}, hide:{s:100}, ore:{s:100}, wood:{s:100}, stone:{s:100} }
        });

        const granted_fame = ref({});
        const isInitializing = ref(true);

        // --- QTY MODE BUCKET LOGIC ---
        const activeQtyBucket = computed(() => {
            if (cfg.value.use_multi_consumables) return cfg.value.qty_cook;
            if (cfg.value.use_refine_only) return cfg.value.qty_refine;
            return cfg.value.qty_gear;
        });

        const syncQtyToFlat = () => {
            const bucket = activeQtyBucket.value;
            cfg.value.q0 = bucket.q0;
            cfg.value.q1 = bucket.q1;
            cfg.value.q2 = bucket.q2;
            cfg.value.q3 = bucket.q3;
            cfg.value.q4 = bucket.q4;
        };

        const syncFlatToBucket = () => {
            const bucket = activeQtyBucket.value;
            bucket.q0 = cfg.value.q0;
            bucket.q1 = cfg.value.q1;
            bucket.q2 = cfg.value.q2;
            bucket.q3 = cfg.value.q3;
            bucket.q4 = cfg.value.q4;
        };

                
        const syncFameExact = () => {
            let prof = cfg.value.profiles[cfg.value.active_profile];
            if (!prof) return;
            if (!prof.fame_exact) prof.fame_exact = {};
            
            if (prof.main_specs) {
                for (let node in prof.main_specs) {
                    let curLvl = parseInt(prof.main_specs[node]) || 1;
                    let exactKey = `craft_${node}`;
                    let expectedLvl = prof.fame_exact[exactKey] !== undefined ? fameToLevel(prof.fame_exact[exactKey]) : null;
                    if (curLvl !== expectedLvl) prof.fame_exact[exactKey] = levelToFame(curLvl);
                }
            }
            
            ['fiber', 'hide', 'ore', 'wood', 'stone'].forEach(mat => {
                if (prof[mat]) {
                    let curLvl = parseInt(prof[mat].s) || 1;
                    let exactKey = `refine_${mat}`;
                    let expectedLvl = prof.fame_exact[exactKey] !== undefined ? fameToLevel(prof.fame_exact[exactKey]) : null;
                    if (curLvl !== expectedLvl) prof.fame_exact[exactKey] = levelToFame(curLvl);
                }
            });
        };

                
        const applyFame = (node, type, amount) => {
            let prof = cfg.value.profiles[cfg.value.active_profile];
            if (!prof.fame_exact) prof.fame_exact = {};
            
            let targetNode = type === 'refine' ? RAW_OF[node] : node;
            if(!targetNode) return;

            let exactKey = type === 'craft' ? `craft_${targetNode}` : `refine_${targetNode}`;
            
            if (prof.fame_exact[exactKey] === undefined) {
                let curLvl = type === 'craft' ? (prof.main_specs[targetNode] || 1) : (prof[targetNode]?.s || 1);
                prof.fame_exact[exactKey] = levelToFame(curLvl);
            }
            
            prof.fame_exact[exactKey] += amount;
            if (prof.fame_exact[exactKey] < 0) prof.fame_exact[exactKey] = 0;
            
            let newLvl = fameToLevel(prof.fame_exact[exactKey]);
            
            if (type === 'craft') {
                if (!prof.main_specs) prof.main_specs = {};
                prof.main_specs[targetNode] = newLvl;
            } else {
                if (!prof[targetNode]) prof[targetNode] = { s: 1 };
                prof[targetNode].s = newLvl;
            }
        };

                                
        
        const tierKey = computed(() => `t${cfg.value.tier}`);

        const initPricesData = () => {
            const cities = ALL_SELL_CITIES;
            cities.forEach(city => {
                if (!pricesData.value[city]) pricesData.value[city] = {};

                [1,2,3,4,5,6,7,8].forEach(tier => {
                    const tk = `t${tier}`;
                    if (!pricesData.value[city][tk]) pricesData.value[city][tk] = { raw: {}, under: {}, ref: {}, journal: { fletcher: {empty:'', full:''}, imbuer: {empty:'', full:''}, blacksmith: {empty:'', full:''}, toolmaker: {empty:'', full:''} }, fragments: { rune: '', soul: '', relic: '' }, artifacts: {}, timestamps: {}, crafted: {}, farming_mats: {} };
                    if (!pricesData.value[city][tk].farming_mats) pricesData.value[city][tk].farming_mats = {};
                    if (!pricesData.value[city][tk].tome_of_insight) pricesData.value[city][tk].tome_of_insight = {};

                    // Scaffold Tome of Insight slots for T4-T8
                    if (tier >= 4 && tier <= 8) {
                        const tomeId = TOME_OF_INSIGHT_TIERS.find(t => t.tier === tier)?.id;
                        if (tomeId && pricesData.value[city][tk].tome_of_insight[tomeId] === undefined) {
                            pricesData.value[city][tk].tome_of_insight[tomeId] = '';
                        }
                    }

                    // Populate farming mats
                    const farmGroup = FARMING_MATS_LIST.find(g => g.t === tier);
                    if (farmGroup) {
                        farmGroup.mats.forEach(mat => {
                            if (pricesData.value[city][tk].farming_mats[mat] === undefined) {
                                pricesData.value[city][tk].farming_mats[mat] = '';
                            }
                        });
                    }
                });

                const tk = tierKey.value;
                if (!pricesData.value[city][tk]) pricesData.value[city][tk] = { raw: {}, under: {}, ref: {}, journal: { fletcher: {empty:'', full:''}, imbuer: {empty:'', full:''}, blacksmith: {empty:'', full:''}, toolmaker: {empty:'', full:''} }, fragments: { rune: '', soul: '', relic: '' }, artifacts: {}, timestamps: {}, crafted: {}, farming_mats: {} };
                if (!pricesData.value[city][tk].artifacts) pricesData.value[city][tk].artifacts = {};
                if (!pricesData.value[city][tk].fragments) pricesData.value[city][tk].fragments = { rune: '', soul: '', relic: '' };

                if (!pricesData.value[city][tk].journal) pricesData.value[city][tk].journal = { fletcher: {empty:'', full:''}, imbuer: {empty:'', full:''}, blacksmith: {empty:'', full:''}, toolmaker: {empty:'', full:''} };
                if (!pricesData.value[city][tk].journal.toolmaker) pricesData.value[city][tk].journal.toolmaker = {empty:'', full:''};

                if (!pricesData.value[city][tk].raw) pricesData.value[city][tk].raw = {};
                if (!pricesData.value[city][tk].under) pricesData.value[city][tk].under = {};
                if (!pricesData.value[city][tk].ref) pricesData.value[city][tk].ref = {};

                MAT_LIST.forEach(mat => {
                    const rawMat = RAW_OF[mat];
                    if (!rawMat) return;
                    if (!pricesData.value[city][tk].raw[rawMat]) pricesData.value[city][tk].raw[rawMat] = { '.0':'', '.1':'', '.2':'', '.3':'', '.4':'' };
                    if (!pricesData.value[city][tk].under[mat]) pricesData.value[city][tk].under[mat] = { '.0':'', '.1':'', '.2':'', '.3':'', '.4':'' };
                    if (!pricesData.value[city][tk].ref[mat]) pricesData.value[city][tk].ref[mat] = { '.0':'', '.1':'', '.2':'', '.3':'', '.4':'' };
                });
            });
        };
        watch(() => cfg.value.tier, initPricesData);

                
        const availableDestinations = computed(() => CITY_NEIGHBORS[cfg.value.route_from] || ALL_ROYAL_CITIES);

        watch(() => cfg.value.route_from, () => {
            if (!availableDestinations.value.includes(cfg.value.route_to)) {
                cfg.value.route_to = availableDestinations.value[0];
                saveAndFetch();
            }
        });

        const checkedTasks = ref({});
        let checkTimeout;

        watch(checkedTasks, (newVal) => {
            clearTimeout(checkTimeout);
            checkTimeout = setTimeout(() => { fetch('/api/checklist', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newVal) }); }, 300);

            if (isInitializing.value) return; 

            if (data.value && data.value.logistics) {
                let fameChanged = false;
                for (let city in data.value.logistics) {
                    let cData = data.value.logistics[city];
                    if (!cData) continue;
                    
                    (cData.refine || []).forEach(t => {
                        if (typeof t === 'string') return;
                        let isChecked = !!newVal[t.id];
                        let isGranted = !!granted_fame.value[t.id];
                        if (isChecked && !isGranted) {
                            applyFame(t.mat, 'refine', t.fame || 0);
                            granted_fame.value[t.id] = true;
                            fameChanged = true;
                        } else if (!isChecked && isGranted) {
                            applyFame(t.mat, 'refine', -(t.fame || 0));
                            granted_fame.value[t.id] = false;
                            fameChanged = true;
                        }
                    });
                    
                    (cData.craft || []).forEach(t => {
                        if (typeof t === 'string') return;
                        let isChecked = !!newVal[t.id];
                        let isGranted = !!granted_fame.value[t.id];
                        if (t.is_cancelled) isChecked = false; 
                        
                        if (isChecked && !isGranted) {
                            if (t.main_node) applyFame(t.main_node, 'craft', t.fame || 0);
                            granted_fame.value[t.id] = true;
                            fameChanged = true;
                        } else if (!isChecked && isGranted) {
                            if (t.main_node) applyFame(t.main_node, 'craft', -(t.fame || 0));
                            granted_fame.value[t.id] = false;
                            fameChanged = true;
                        }
                    });
                }
                if (fameChanged) saveAndFetch();
            }
        }, { deep: true });

        const clearChecks = async () => {
            // Save fame to profile BEFORE clearing
            syncFameExact();
            let prof = cfg.value.profiles[cfg.value.active_profile];
            if (prof) {
                cfg.value.specs = JSON.parse(JSON.stringify(prof));
            }
            await fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cfg.value) });
            // Now safe to clear
            granted_fame.value = {};
            checkedTasks.value = {};
            await fetch('/api/checklist', { method: 'DELETE' });
            saveAndFetch();
        };

        
        const dynamicPeakWeight = computed(() => {
            if (!data.value || !data.value.logistics) return { kg: 0, pct: 0, over: false };
            let peak = 0;
            for (const city of ALL_ROYAL_CITIES) {
                const cData = data.value.logistics[city];
                if (!cData) continue;
                let wIn = 0, wOut = 0;
                (cData.refine || []).forEach(t => { if (checkedTasks.value[t.id || t]) wOut += (t.weight_out || 0); else wIn += (t.weight_in || 0); });
                (cData.craft || []).forEach(t => { 
                    if (t.is_cancelled) return;
                    if (checkedTasks.value[t.id || t]) wOut += (t.weight_out || 0); else wIn += (t.weight_in || 0); 
                });
                if (wIn + wOut > peak) peak = wIn + wOut;
            }
            const maxL = data.value.weight_data?.max_load || 50;
            return { kg: peak, pct: Math.min((peak / maxL) * 100, 999).toFixed(1), over: peak > maxL };
        });

        const routeLogistics = computed(() => {
            if (!data.value || !data.value.logistics || !data.value.logistics[cfg.value.route_to]) return null;
            const cityData = data.value.logistics[cfg.value.route_to];
            let mats_orig = {}, mats_rem = {}, journals_orig = {}, journals_rem = {}, under_orig = {}, under_rem = {};
            const isT3Under = cfg.value.tier === 4;
            let live_in = 0, live_out = 0, live_slots = 0;

            const safeRefine = Array.isArray(cityData.refine) ? cityData.refine.map(t => typeof t === 'string' ? { id: t, text: t, weight_in: 0, weight_out: 0, u_qty: 0, u_enc: '.0', raw_qty: 0, out_qty: 0 } : t) : [];
            const safeCraft = Array.isArray(cityData.craft) ? cityData.craft.map(t => typeof t === 'string' ? { id: t, text: t, weight_in: 0, weight_out: 0, mats_dict: {}, j_type: '', j_amt: 0, out_qty: 0, is_cancelled: false } : t) : [];

            safeRefine.forEach(t => {
                const isChecked = checkedTasks.value[t.id || t];
                if (isChecked) { live_out += (t.weight_out || 0); if (t.out_qty > 0) live_slots += Math.ceil(t.out_qty / 999); } 
                else { live_in += (t.weight_in || 0); if (t.raw_qty > 0) live_slots += Math.ceil(t.raw_qty / 999); }
                if (t.u_qty > 0) {
                    if (!under_orig[t.mat]) { under_orig[t.mat] = {'.0':0, '.1':0, '.2':0, '.3':0, '.4':0}; under_rem[t.mat] = {'.0':0, '.1':0, '.2':0, '.3':0, '.4':0}; }
                    under_orig[t.mat][t.u_enc] += t.u_qty;
                    if (!isChecked) under_rem[t.mat][t.u_enc] += t.u_qty;
                }
            });

            safeCraft.forEach(t => {
                const isChecked = checkedTasks.value[t.id || t] || t.is_cancelled;
                
                if (t.is_cancelled) {
                    live_in += (t.weight_in || 0);
                } else {
                    if (isChecked) { live_out += (t.weight_out || 0); if (t.out_qty > 0) live_slots += Math.ceil(t.out_qty / 999); if (t.j_amt > 0) live_slots += Math.ceil(t.j_amt / 999); } 
                    else { live_in += (t.weight_in || 0); }
                }

                for (const mName in t.mats_dict) {
                    if (!mats_orig[mName]) { mats_orig[mName] = {'.0':0, '.1':0, '.2':0, '.3':0, '.4':0}; mats_rem[mName] = {'.0':0, '.1':0, '.2':0, '.3':0, '.4':0}; }
                    for (const enc in t.mats_dict[mName]) { mats_orig[mName][enc] += t.mats_dict[mName][enc]; if (!isChecked) mats_rem[mName][enc] += t.mats_dict[mName][enc]; }
                }
                if (t.j_type && t.j_amt > 0) {
                    if (!journals_orig[t.j_type]) { journals_orig[t.j_type] = 0; journals_rem[t.j_type] = 0; }
                    journals_orig[t.j_type] += t.j_amt; if (!isChecked) journals_rem[t.j_type] += t.j_amt;
                }
            });

            for (const mat in under_rem) for (const enc in under_rem[mat]) if (under_rem[mat][enc] > 0) live_slots += Math.ceil(under_rem[mat][enc] / 999);
            for (const mat in mats_rem) for (const enc in mats_rem[mat]) if (mats_rem[mat][enc] > 0) live_slots += Math.ceil(mats_rem[mat][enc] / 999);
            for (const jt in journals_rem) if (journals_rem[jt] > 0) live_slots += Math.ceil(journals_rem[jt] / 999);

            let under_summary = "";
            for (const [m_name, enchants] of Object.entries(under_orig)) {
                const active = Object.entries(enchants).filter(([e, q]) => q > 0);
                if (active.length > 0) {
                    under_summary += `<div class='mb-2'><span class='text-sm font-black text-rose-400 uppercase tracking-widest block mb-1'>UNDER-REFINE ${m_name} (T${isT3Under ? 3 : cfg.value.tier - 1})</span><div class='flex flex-wrap gap-2'>`;
                    if (isT3Under) {
                        const total_orig = active.reduce((sum, [, q]) => sum + q, 0), total_rem = Object.values(under_rem[m_name]).reduce((sum, q) => sum + q, 0);
                        const textVal = total_rem === 0 ? `DONE (${getStackInfo(total_orig)})` : `${getStackInfo(total_rem)} / ${getStackInfo(total_orig)}`;
                        under_summary += `<span class='bg-rose-950/40 px-3 py-1.5 rounded border border-rose-900/50 text-xs font-mono text-white ${total_rem === 0 ? 'opacity-50 grayscale line-through' : ''}'>TOTAL FLAT: ${textVal}</span>`;
                    } else {
                        for (const [e, q_orig] of active) {
                            const q_rem = under_rem[m_name][e], textVal = q_rem === 0 ? `DONE (${getStackInfo(q_orig)})` : `${getStackInfo(q_rem)} / ${getStackInfo(q_orig)}`;
                            under_summary += `<span class='bg-rose-950/40 px-3 py-1.5 rounded border border-rose-900/50 text-xs font-mono ${q_rem === 0 ? 'opacity-50 grayscale line-through' : ''}'><span class='${e === '.0' ? 'enc-0' : e === '.1' ? 'enc-1' : e === '.2' ? 'enc-2' : e === '.3' ? 'enc-3' : 'enc-4'} font-black'>${e}</span>: ${textVal}</span>`;
                        }
                    }
                    under_summary += `</div></div>`;
                }
            }

            let mats_summary = "";
            for (const [m_name, enchants] of Object.entries(mats_orig)) {
                const active = Object.entries(enchants).filter(([e, q]) => q > 0);
                if (active.length > 0) {
                    mats_summary += `<div class='mb-3'><span class='text-sm font-black text-amber-300 uppercase tracking-widest block mb-1.5'>${m_name}</span><div class='flex flex-wrap gap-2'>`;
                    for (const [e, q_orig] of active) {
                        const q_rem = mats_rem[m_name][e], textVal = q_rem === 0 ? `DONE (${getStackInfo(q_orig)})` : `${getStackInfo(q_rem)} / ${getStackInfo(q_orig)}`;
                        mats_summary += `<span class='bg-black/40 px-3 py-1.5 rounded border border-[#1E2D45] text-xs font-mono ${q_rem === 0 ? 'opacity-50 grayscale line-through' : ''}'><span class='${e === '.0' ? 'enc-0' : e === '.1' ? 'enc-1' : e === '.2' ? 'enc-2' : e === '.3' ? 'enc-3' : 'enc-4'} font-black'>${e}</span>: ${textVal}</span>`;
                    }
                    mats_summary += `</div></div>`;
                }
            }

            let journal_summary = "";
            if (cfg.value.use_own_journals) {
                const activeJ = Object.entries(journals_orig).filter(([, q]) => q > 0);
                if (activeJ.length > 0) {
                    journal_summary += `<div class='flex flex-wrap gap-2'>`;
                    for (const [jt, jq_orig] of activeJ) {
                        const jq_rem = journals_rem[jt], textVal = jq_rem === 0 ? `DONE (${getStackInfo(jq_orig)})` : `${getStackInfo(jq_rem)} / ${getStackInfo(jq_orig)}`;
                        journal_summary += `<span class='bg-purple-950/40 px-4 py-2 rounded border border-purple-900/50 text-xs font-mono text-purple-300 ${jq_rem === 0 ? 'opacity-50 grayscale line-through' : ''}'><span class='font-black capitalize'>${jt}</span>: ${textVal}</span>`;
                    }
                    journal_summary += `</div>`;
                } else journal_summary = `<p class='text-sm text-gray-500 italic'>Tidak butuh jurnal di kota ini.</p>`;
            } else journal_summary = `<p class='text-sm text-gray-500 italic'>Fitur 'Local Laborer' dimatikan.</p>`;

            return { refine: safeRefine, craft: safeCraft, live_in, live_out, current_total: live_in + live_out, live_slots, under_summary: under_summary || `<p class='text-sm text-gray-500 italic'>Tidak ada under-refine.</p>`, mats_summary: mats_summary || `<p class='text-sm text-gray-500 italic'>Tidak butuh material.</p>`, journal_summary };
        });

        const toggleCancelCraft = (rawData) => {
            if (!rawData || !rawData.item || !rawData.enchant) return;
            const item = rawData.item;
            const enc = rawData.enchant;

            if (!cfg.value.cancelled_crafts) cfg.value.cancelled_crafts = {};
            if (!cfg.value.cancelled_crafts[item]) cfg.value.cancelled_crafts[item] = {};

            const isNowCancelled = !cfg.value.cancelled_crafts[item][enc];
            cfg.value.cancelled_crafts[item][enc] = isNowCancelled;

            if (isNowCancelled) {
                const taskIdsToUncheck = Object.keys(checkedTasks.value).filter(id => id.includes(`craft_`) && id.includes(item.replace(' ', '')) && id.includes(enc));
                taskIdsToUncheck.forEach(id => checkedTasks.value[id] = false);
            }

            clearTimeout(window._cancelTimeout);
            window._cancelTimeout = setTimeout(() => {
                saveAndFetch();
            }, 150);
        };

        const setCraftQty = (item, enchant, val) => {
            if (!cfg.value.adjusted_qty_crafts) cfg.value.adjusted_qty_crafts = {};
            if (!cfg.value.adjusted_qty_crafts[item]) cfg.value.adjusted_qty_crafts[item] = {};
            
            let parsedVal = parseInt(val);
            if (isNaN(parsedVal) || parsedVal < 0 || val === '') {
                delete cfg.value.adjusted_qty_crafts[item][enchant];
                if (Object.keys(cfg.value.adjusted_qty_crafts[item]).length === 0) {
                    delete cfg.value.adjusted_qty_crafts[item];
                }
            } else {
                cfg.value.adjusted_qty_crafts[item][enchant] = parsedVal;
            }
            saveAndFetch();
        };

        const selectedItemList = computed(() => {
            if (cfg.value.use_refine_only) return [];
            const list = [];
            const margins = data.value?.analyzer_margins || data.value?.unit_margins || {};

            for (const cat in margins) {
                for (const item in margins[cat]) {
                    const encs = cfg.value.selected_items[item];
                    if (!encs) continue;
                    for (const e of ['.0','.1','.2','.3','.4']) {
                        if (encs[e]) {
                            const unitData = margins[cat][item][e] || {p: 0, pct: 0};
                            list.push({
                                cat: cat.replace('artifact_', 'Art. '),
                                item: item,
                                enchant: e,
                                profit: unitData.p,
                                margin: unitData.pct
                            });
                        }
                    }
                }
            }

            list.sort((a, b) => {
                let valA = a[sortKey.value];
                let valB = b[sortKey.value];
                if (typeof valA === 'string') return sortDesc.value ? valB.localeCompare(valA) : valA.localeCompare(valB);
                return sortDesc.value ? (valB - valA) : (valA - valB);
            });

            return list;
        });

        // 🚀 KATEGORI GROUPING SUDAH MENCAKUP BAGS DAN CAPES
        const groupedCategories = computed(() => {
            if (!p_sell.value || !p_sell.value.crafted) return { normal: [], artifact: [] };
            const crafted = p_sell.value.crafted;
            return {
                normal: ['helmets', 'armors', 'shoes', 'offhands', 'weapons', 'bags', 'capes'].filter(c => crafted[c]),
                artifact: ['artifact_helmets', 'artifact_armors', 'artifact_shoes', 'artifact_offhands', 'artifact_weapons', 'artifact_bags', 'artifact_capes'].filter(c => crafted[c])
            };
        });

        const categoryProfits = computed(() => {
            const res = { weapons: 0, armors: 0, helmets: 0, shoes: 0, offhands: 0, bags: 0, capes: 0 };
            if (!data.value || (!data.value.analyzer_margins && !data.value.unit_margins)) return res;
            
            const margins = data.value.analyzer_margins || data.value.unit_margins;
            const globalQMap = { '.0': cfg.value.q0, '.1': cfg.value.q1, '.2': cfg.value.q2, '.3': cfg.value.q3, '.4': cfg.value.q4 };

            for (const cat in margins) {
                let baseCat = cat.replace('artifact_', '');
                if (res[baseCat] === undefined) res[baseCat] = 0;

                for (const item in margins[cat]) {
                    const encs = cfg.value.selected_items[item];
                    if (!encs) continue;
                    
                    for (const e of ['.0','.1','.2','.3','.4']) {
                        if (encs[e] && margins[cat][item][e] && margins[cat][item][e].p) {
                            const adjustedQ = cfg.value.adjusted_qty_crafts?.[item]?.[e];
                            const activeQ = adjustedQ !== undefined ? adjustedQ : globalQMap[e];
                            res[baseCat] += (margins[cat][item][e].p * activeQ);
                        }
                    }
                }
            }
            return res;
        });

        const unselectAllItems = async () => {
            if(!confirm("Hapus semua checklist barang?")) return;

            // 1. Save current fame to profile BEFORE clearing
            let prof = cfg.value.profiles[cfg.value.active_profile];
            if (prof) {
                syncFameExact();
            }

            // 2. Clear all selected items
            for (const item in cfg.value.selected_items) {
                cfg.value.selected_items[item] = { '.0': false, '.1': false, '.2': false, '.3': false, '.4': false };
            }
            cfg.value.adjusted_qty_crafts = {};
            cfg.value.cancelled_crafts = {};

            // 3. Clear logistics checklist (preserve fame already saved above)
            granted_fame.value = {};
            checkedTasks.value = {};
            await fetch('/api/checklist', { method: 'DELETE' });

            saveAndFetch();
        };

        const volFilter = ref({ tier: '', cat: '', enchant: '', days: '30' });
        const volHistory = ref([]); const volSummary = ref(null); const volItemList = ref([]); const volChartItem = ref(''); const volAmountMode = ref('volume');
        const volSearch = ref('');
        const filteredVolItemList = computed(() => {
            if (!volSearch.value) return volItemList.value;
            const lower = volSearch.value.toLowerCase();
            return volItemList.value.filter(i => getRealName(i).toLowerCase().includes(lower) || i.toLowerCase().includes(lower));
        });
        
        let trendChartInst = null, amountChartInst = null, profitChartInst = null;

        const p_buy = computed(() => {
            if (!pricesData.value || Object.keys(pricesData.value).length === 0) return { raw: {}, under: {}, ref: {}, journal: { fletcher: {}, imbuer: {}, blacksmith: {}, toolmaker: {} }, fragments: {}, artifacts: {}, timestamp: null };
            return pricesData.value[cfg.value.buy_city]?.[tierKey.value] || { raw: {}, under: {}, ref: {}, journal: { fletcher: {}, imbuer: {}, blacksmith: {}, toolmaker: {} }, fragments: {}, artifacts: {}, timestamp: null };
        });

        const getRefineCity = (mat) => {
            if (cfg.value.use_refine_only) {
                return cfg.value.multi_refine_only_mode
                    ? (cfg.value.refine_cities?.[mat] || cfg.value.buy_city)
                    : cfg.value.buy_city;
            }
            if (cfg.value.use_multi_refine) return cfg.value.refine_cities?.[mat] || cfg.value.buy_city;
            return cfg.value.craft_city || cfg.value.buy_city;
        };

        const p_buy_farm = computed(() => pricesData.value?.[cfg.value.buy_city]?.[tierKey.value]?.farming_mats || {});
        
        const luxuryArbitrage = computed(() => {
            if (!data.value || !data.value.unit_margins || !data.value.unit_margins.luxury) return [];
            let lux = data.value.unit_margins.luxury;
            let list = [];
            for (let name in lux) {
                let details = lux[name]['.0'];
                if (details && details.p > 0) {
                    list.push({name, ...details});
                }
            }
            return list.sort((a, b) => b.p - a.p);
        });

        const p_buy_mat = computed(() => {
            const result = {}; const em = () => ({ '.0':'', '.1':'', '.2':'', '.3':'', '.4':'' });
            if (!pricesData.value || Object.keys(pricesData.value).length === 0) {
                for (const mat of MAT_LIST) result[mat] = { ref: { [mat]: em() }, under: { [mat]: em() }, raw: { [RAW_OF[mat]]: em() } };
                return result;
            }
            for (const mat of MAT_LIST) {
                const cityRef = getRefineCity(mat);
                const rawMat  = RAW_OF[mat];
                const cityRaw = cfg.value.raw_cities?.[rawMat] || cfg.value.buy_city;
                result[mat] = {
                    ref:   { [mat]: pricesData.value[cityRef]?.[tierKey.value]?.ref?.[mat] || em() },
                    under: { [mat]: pricesData.value[cityRef]?.[tierKey.value]?.under?.[mat] || em() },
                    raw:   { [rawMat]: pricesData.value[cityRaw]?.[tierKey.value]?.raw?.[rawMat] || em() }
                };
            }
            return result;
        });

        const p_sell = computed(() => {
            if (!pricesData.value || Object.keys(pricesData.value).length === 0) return { crafted: {} };
            return pricesData.value[cfg.value.sell_city]?.[tierKey.value] || { crafted: {} };
        });

        const fragmentPrices = computed(() => {
            const res = { rune: { p:0, city:'', ts:null }, soul: { p:0, city:'', ts:null }, relic: { p:0, city:'', ts:null } };
            if (!pricesData.value || Object.keys(pricesData.value).length === 0) return res;
            for(const ft of ['rune', 'soul', 'relic']) {
                const c = cfg.value.frag_cities?.[ft] || cfg.value.buy_city;
                res[ft].city = c;
                res[ft].p = pricesData.value[c]?.[tierKey.value]?.fragments?.[ft] || 0;
                res[ft].ts = pricesData.value[c]?.[tierKey.value]?.timestamps?.[`frag_${ft}`];
            }
            return res;
        });

        // 🌽 FARMING GROUPS COMPUTED
                                                
        const farmingGroups = computed(() => {
            let res = {
                raw_crops: {},
                raw_herbs: {},
                raw_meat: {},
                animal_products: {},
                processed_ingredients: {},
                enchantments: {}
            };
            if (!pricesData.value || !pricesData.value[cfg.value.buy_city]) return res;
            
            for(let t of [8,7,6,5,4,3,2,1]) {
                let mats = pricesData.value[cfg.value.buy_city]['t'+t]?.farming_mats || {};
                for (let mat in mats) {
                    if (raw_crops.includes(mat)) { if(!res.raw_crops[t]) res.raw_crops[t]={}; res.raw_crops[t][mat] = mats[mat]; }
                    else if (raw_herbs.includes(mat)) { if(!res.raw_herbs[t]) res.raw_herbs[t]={}; res.raw_herbs[t][mat] = mats[mat]; }
                    else if (raw_meat.includes(mat)) { if(!res.raw_meat[t]) res.raw_meat[t]={}; res.raw_meat[t][mat] = mats[mat]; }
                    else if (animal_products.includes(mat)) { if(!res.animal_products[t]) res.animal_products[t]={}; res.animal_products[t][mat] = mats[mat]; }
                    else if (processed_ingredients.includes(mat)) { if(!res.processed_ingredients[t]) res.processed_ingredients[t]={}; res.processed_ingredients[t][mat] = mats[mat]; }
                    else if (enchantments.includes(mat)) { if(!res.enchantments[t]) res.enchantments[t]={}; res.enchantments[t][mat] = mats[mat]; }
                    else { if(!res.processed_ingredients[t]) res.processed_ingredients[t]={}; res.processed_ingredients[t][mat] = mats[mat]; } // fallback
                }
            }
            return res;
        });

        const artifactBestBuy = computed(() => {
            const result = {};
            if (!pricesData.value || Object.keys(pricesData.value).length === 0 || !data.value || !data.value.used_artifacts) return result;
            const tk = tierKey.value;
            for (const art of Object.keys(data.value.used_artifacts)) {
                let cityPrices = [];
                for (const city of ALL_ROYAL_CITIES) {
                    const val = parseFloat(pricesData.value?.[city]?.[tk]?.artifacts?.[art] || 0);
                    if (val > 0) cityPrices.push({ city, price: val });
                }
                cityPrices.sort((a, b) => a.price - b.price);
                result[art] = cityPrices.length > 0 ? cityPrices[0] : null;
            }
            return result;
        });

        const journalBestSell = computed(() => {
            const result = {};
            if (!pricesData.value || Object.keys(pricesData.value).length === 0) return result;
            const tk = tierKey.value;
            for (const jt of JOURNAL_TYPES) {
                let cityPrices = [];
                for (const city of ALL_ROYAL_CITIES) {
                    const fullVal = parseFloat(pricesData.value?.[city]?.[tk]?.journal?.[jt]?.full || 0);
                    if (fullVal > 0) cityPrices.push({ city, price: fullVal });
                }
                cityPrices.sort((a, b) => b.price - a.price); 
                result[jt] = cityPrices.length > 0 ? cityPrices[0] : null; 
            }
            return result;
        });

        const logsData = ref([]);

        const liveLogs = computed(() => {
            return logsData.value.map(log => {
                if (!log.items || !log.setup || log.original_gear_rev === undefined) {
                    return { ...log, live_profit: (log.revenue || 0) - (log.cost || 0), live_revenue: log.revenue, diff: 0, items: log.items || [] };
                }

                const tk = `t${log.setup.tier}`;
                const sellCity = log.setup.sell_city;
                const tax = log.setup.premium_tax ? 0.04 : 0.08;
                const setupFee = sellCity === 'Black Market' ? 0 : 0.025;
                
                let current_gear_rev = 0;
                let item_updates = [];

                log.items.forEach(i => {
                    const actualTk = i.t ? `t${i.t}` : tk;
                    const curSell = parseFloat(pricesData.value?.[sellCity]?.[actualTk]?.crafted?.[i.cat]?.[i.item]?.[i.enchant] || 0);
                    const netSell = curSell * (1.0 - tax - setupFee);
                    current_gear_rev += (netSell * i.qty);

                    const curProfit = netSell - i.unit_cost; 
                    const curPct = i.unit_cost > 0 ? (curProfit / i.unit_cost) * 100 : 0;
                    const origPct = i.unit_cost > 0 ? ((i.orig_profit || 0) / i.unit_cost) * 100 : 0;
                    
                    let diffPct = 0;
                    if (i.orig_sell > 0) {
                        diffPct = (((curSell - i.orig_sell) / i.orig_sell) * 100).toFixed(1);
                    }

                    item_updates.push({
                        ...i,
                        cur_sell: curSell,
                        cur_profit: Math.floor(curProfit),
                        cur_pct: curPct.toFixed(1),
                        orig_pct: origPct.toFixed(1),
                        is_down: curSell < (i.orig_sell || 0), 
                        is_up: curSell > (i.orig_sell || 0),
                        price_diff_pct: diffPct
                    });
                });

                const diff = current_gear_rev - log.original_gear_rev;
                const live_revenue = log.revenue + diff;
                const live_profit = live_revenue - log.cost;

                return {
                    ...log,
                    live_revenue,
                    live_profit,
                    diff,
                    items: item_updates
                };
            });
        });

        const logsProfitStats = computed(() => {
            let totalProfit = 0;
            let winCount = 0;
            let currentMonthProfit = 0;
            const currentMonthStr = new Date().toISOString().slice(0, 7); 

            logsData.value.forEach(log => {
                const profit = log.revenue - log.cost;
                totalProfit += profit;
                if (profit > 0) winCount++;
                if (log.date.startsWith(currentMonthStr)) currentMonthProfit += profit;
            });

            return {
                totalProfit,
                currentMonthProfit,
                winRate: logsData.value.length ? ((winCount / logsData.value.length) * 100).toFixed(1) : 0
            };
        });

        
                
        let liveChartInsts = {};

        const toggleLiveMonitor = (idx) => {
            expandedLogs.value[idx] = !expandedLogs.value[idx];
            if (expandedLogs.value[idx]) {
                nextTick(() => {
                    renderLiveChart(idx);
                });
            }
        };

        const renderLiveChart = (idx) => {
            const ctx = document.getElementById('liveChart-' + idx);
            if (!ctx) return;
            if (liveChartInsts[idx]) {
                liveChartInsts[idx].destroy();
            }

            const log = liveLogs.value[idx];
            if (!log || !log.items) return;

            const labels = log.items.map(i => getRealName(i.item) + ' ' + i.enchant);
            const data = log.items.map(i => i.cur_profit);
            const bgColors = data.map(v => v > 0 ? 'rgba(52, 211, 153, 0.8)' : 'rgba(244, 63, 94, 0.8)');

            liveChartInsts[idx] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Profit Margin',
                        data: data,
                        backgroundColor: bgColors,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { ticks: { color: '#94A3B8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                        x: { ticks: { color: '#94A3B8', display: false }, grid: { display: false } }
                    }
                }
            });
        };

        const renderProfitChart = () => {
            const ctx = document.getElementById('profitChart');
            if (!ctx) return;
            if (profitChartInst) profitChartInst.destroy();

            const dateMap = {};
            const reversedLogs = [...logsData.value].reverse();
            
            reversedLogs.forEach(log => {
                if (!dateMap[log.date]) dateMap[log.date] = 0;
                dateMap[log.date] += (log.revenue - log.cost);
            });

            const labels = Object.keys(dateMap).slice(-30);
            const chartData = Object.values(dateMap).slice(-30);
            let gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(52, 211, 153, 0.5)');   
            gradient.addColorStop(1, 'rgba(52, 211, 153, 0.0)');

            profitChartInst = new Chart(ctx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Net Profit',
                        data: chartData,
                        borderColor: '#34D399',
                        backgroundColor: gradient,
                        borderWidth: 2,
                        pointBackgroundColor: '#0A101C',
                        pointBorderColor: '#34D399',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { ticks: { color: '#94A3B8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                        x: { ticks: { color: '#94A3B8' }, grid: { display: false } }
                    }
                }
            });
        };

        const loadVolumeData = async () => {
            try {
                const params = new URLSearchParams();
                if (volFilter.value.tier) params.set('tier', volFilter.value.tier);
                if (volFilter.value.cat) params.set('cat', volFilter.value.cat);
                if (volFilter.value.enchant) params.set('enchant', volFilter.value.enchant);
                if (volFilter.value.days) params.set('days', volFilter.value.days);

                const res = await fetch(`/api/volume?${params}`, { cache: 'no-store' });
                const resp = await res.json();
                volHistory.value = resp.history || [];
                volSummary.value = resp.summary || null;

                if (volSummary.value && volSummary.value.last_capture) {
                    const d = new Date(volSummary.value.last_capture + 'Z');
                    volSummary.value.last_capture_time = d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) + ' WIB';
                    volSummary.value.last_capture_date = d.toLocaleDateString('id-ID');
                }

                const allGearItems = new Set();
                const crafted = p_sell.value?.crafted || {};
                
                let targetCategories = [];
                if (volFilter.value.cat) {
                    targetCategories = [volFilter.value.cat];
                } else {
                    targetCategories = [
                        'weapons', 'armors', 'helmets', 'shoes', 'offhands', 'bags', 'capes',
                        'artifact_weapons', 'artifact_armors', 'artifact_helmets', 'artifact_shoes', 'artifact_offhands', 'artifact_bags', 'artifact_capes'
                    ];
                }

                for (const cat of targetCategories) {
                    if (crafted[cat]) {
                        for (const item in crafted[cat]) {
                            allGearItems.add(item);
                        }
                    }
                }
                
                for (const r of volHistory.value) {
                    allGearItems.add(r.item);
                }
                
                volItemList.value = Array.from(allGearItems).sort();
                if (!volItemList.value.includes(volChartItem.value)) {
                    volChartItem.value = volItemList.value.length ? volItemList.value[0] : '';
                }

                await nextTick(); renderTrendChart(); renderAmountChart();
            } catch (e) {}
        };

        const renderTrendChart = () => {
            const ctx = document.getElementById('trendChart'); if (!ctx) return;
            if (trendChartInst) trendChartInst.destroy();
            const dateMap = {};
            const daysFilter = parseInt(volFilter.value.days);
            let isShortTerm = daysFilter <= 7 && daysFilter !== 0;
            
            let minDate = new Date("2100-01-01"), maxDate = new Date("2000-01-01");
            let hasData = false;

            for (const r of volHistory.value) {
                if (r.item !== volChartItem.value) continue;
                if (r.ts) {
                    hasData = true;
                    const d = new Date(r.ts.replace(' ', 'T') + 'Z'); 
                    if (d < minDate) minDate = d;
                    if (d > maxDate) maxDate = d;
                }
            }

            if (!hasData) {
                trendChartInst = new Chart(ctx, { type: 'line', data: { labels: [], datasets: [] }, options: CHART_DEFAULTS });
                return;
            }

            if (!isShortTerm) {
                const diffDays = (maxDate - minDate) / (1000 * 60 * 60 * 24);
                if (diffDays <= 3) isShortTerm = true;
            }

            for (const r of volHistory.value) {
                if (r.item !== volChartItem.value) continue; 
                
                let timeKey = "";
                if (r.ts) {
                    const d = new Date(r.ts.replace(' ', 'T') + 'Z'); 
                    if (isShortTerm) {
                        const hh = String(d.getHours()).padStart(2, '0');
                        timeKey = `${d.toLocaleDateString('en-CA')} ${hh}:00`;
                    } else {
                        timeKey = d.toLocaleDateString('en-CA'); 
                    }
                } else {
                    timeKey = "Unknown";
                }

                if (!dateMap[timeKey]) dateMap[timeKey] = {};
                dateMap[timeKey][r.enchant] = (dateMap[timeKey][r.enchant] || 0) + r.volume;
            }
            
            const labels = [];
            let current = new Date(minDate);
            if (isShortTerm) {
                current.setMinutes(0, 0, 0);
            } else {
                current.setHours(0, 0, 0, 0);
            }

            while (current <= maxDate) {
                let labelKey = "";
                if (isShortTerm) {
                    const hh = String(current.getHours()).padStart(2, '0');
                    labelKey = `${current.toLocaleDateString('en-CA')} ${hh}:00`;
                    labels.push(labelKey);
                    current.setHours(current.getHours() + 1);
                } else {
                    labelKey = current.toLocaleDateString('en-CA');
                    labels.push(labelKey);
                    current.setDate(current.getDate() + 1);
                }
            }
            
            const uniqueLabels = [...new Set([...labels, ...Object.keys(dateMap)])].sort((a, b) => {
                if (a === "Unknown") return -1;
                if (b === "Unknown") return 1;
                return a.localeCompare(b);
            });

            const displayLabels = uniqueLabels.map(l => {
                if (l === "Unknown") return l;
                if (isShortTerm) {
                    const parts = l.split(' ');
                    if (parts.length === 2) {
                        const dateParts = parts[0].split('-');
                        if (dateParts.length === 3) {
                            return `${dateParts[2]}/${dateParts[1]} ${parts[1]}`;
                        }
                    }
                }
                return l;
            });

            const enchants = ['.0', '.1', '.2', '.3', '.4'];
            const datasets = enchants.map(e => ({
                label: e, data: uniqueLabels.map(d => dateMap[d]?.[e] !== undefined ? dateMap[d][e] : null),
                borderColor: ENCHANT_COLORS[e], backgroundColor: ENCHANT_COLORS[e].replace('0.85', '0.15'),
                borderWidth: 2, tension: 0.3, fill: true, pointRadius: 4, spanGaps: true
            })).filter(ds => ds.data.some(v => v !== null && v > 0));

            trendChartInst = new Chart(ctx, { type: 'line', data: { labels: displayLabels, datasets }, options: { responsive: true, maintainAspectRatio: false, ...CHART_DEFAULTS } });
        };

        const renderAmountChart = () => {
            const ctx = document.getElementById('amountChart'); if (!ctx) return;
            if (amountChartInst) amountChartInst.destroy();
            
            const itemVol = {};
            for (const r of volHistory.value) {
                const key = `${getRealName(r.item)} ${r.enchant}`;
                if (!itemVol[key]) itemVol[key] = { volume: 0, count: 0, max_price: 0 };
                
                itemVol[key].volume += r.volume;
                itemVol[key].count += 1;
                if (r.price > itemVol[key].max_price) itemVol[key].max_price = r.price;
            }
            
            const mode = volAmountMode.value;
            const top10 = Object.entries(itemVol).sort((a, b) => b[1][mode] - a[1][mode]).slice(0, 10);

            amountChartInst = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: top10.map(([k]) => k),
                    datasets: [{
                        label: mode === 'volume' ? 'Volume' : mode === 'count' ? 'Count' : 'Max Price',
                        data: top10.map(([, v]) => v[mode]),
                        backgroundColor: top10.map(([k]) => ENCHANT_COLORS[k.slice(-2)] || 'rgba(148,163,184,0.7)'),
                        borderWidth: 0, borderRadius: 6
                    }]
                },
                options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#64748B', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } }, y: { ticks: { color: '#94A3B8', font: { size: 12 } }, grid: { display: false } } } }
            });
        };

        const clearVolumeHistory = async () => { 
            if (!confirm('Hapus semua volume history?')) return; 
            await fetch('/api/volume', { method: 'DELETE' }); 
            await loadVolumeData(); 
        };

        const smartSetupResult = ref(null);
        const isAnalyzing = ref(false);

        
                const { runSmartAnalyzer } = setupAnalyzer(cfg, data, isAnalyzing, smartSetupResult);

        const applySmartSetup = () => {
            if (!smartSetupResult.value) return;
            
            cfg.value.q0 = 0;
            cfg.value.q1 = 0;
            cfg.value.q2 = 0;
            cfg.value.q3 = 0;
            cfg.value.q4 = 0;

            cfg.value.adjusted_qty_crafts = smartSetupResult.value.adjusted_qty;
            cfg.value.selected_items = smartSetupResult.value.selected_items; 
            
            saveAndFetch();
            activeTab.value = 'dashboard'; 
        };

        watch(logsData, () => {
            if (activeTab.value === 'logs') nextTick(renderProfitChart);
        }, { deep: true });

        watch(() => cfg.value.use_refine_only, (val, oldVal) => {
            if (val) {
                // Force craft OFF — refine-only means no crafting whatsoever
                cfg.value.do_craft = false;
                if (activePriceTab.value !== 'materials') activePriceTab.value = 'materials';
                if (activeTab.value === 'logistics_craft') activeTab.value = 'logistics_refine';
            } else {
                // Restore craft when leaving refine-only mode
                cfg.value.do_craft = true;
            }
            if (oldVal !== undefined) syncQtyToFlat();
            saveAndFetch();
        });

        watch(() => cfg.value.use_multi_consumables, (val, oldVal) => {
            if (oldVal === undefined) return; // skip init hydration

            // 1. Sync QTY buckets so flat q0-q4 reflect the new mode's bucket
            syncQtyToFlat();

            // 2. Reset tab to dashboard — previous logistics tab is now access-gated
            if (val) {
                // Switched TO Consumables mode → craft/refine logistics are locked
                if (['logistics_refine', 'logistics_craft'].includes(activeTab.value)) {
                    activeTab.value = 'dashboard';
                }
                // Sub-tab: gear list is locked in consumables mode
                if (activeListItemTab.value === 'gear') {
                    activeListItemTab.value = 'consumable';
                }
            } else {
                // Switched FROM Consumables mode → consumables logistics is locked
                if (activeTab.value === 'logistics_consumables') {
                    activeTab.value = 'dashboard';
                }
                // Sub-tab: consumable list is locked outside consumables mode
                if (activeListItemTab.value === 'consumable') {
                    activeListItemTab.value = 'gear';
                }
            }

            // 3. Clear mode-specific cancelled/adjusted crafts — they belong to previous mode's item set
            cfg.value.cancelled_crafts = {};
            cfg.value.adjusted_qty_crafts = {};

            // 4. Clear analyzer result — stale from previous mode
            smartSetupResult.value = null;

            // 5. Trigger full recalculation with new mode context
            saveAndFetch();
        });

        watch(activeTab, (val) => {
            if (val === 'logs') nextTick(renderProfitChart);
            if (val === 'volume') loadVolumeData(); 
            // Sync tab to backend so manifest logic knows context
            cfg.value.activeTab = val;
            saveAndFetch();
        });

        watch(activePriceTab, (val) => {
            cfg.value.activePriceTab = val;
            saveAndFetch();
        });

        watch(activeListItemTab, (val) => {
            cfg.value.activeListItemTab = val;
            saveAndFetch();
            smartSetupResult.value = null;
        });

        const fetchConfigAndData = async () => {
            isInitializing.value = true;
            try {
                const [resCfg, resPrices, resCheck, resLogs] = await Promise.all([ 
                    fetch('/api/config', { cache: 'no-store' }), 
                    fetch('/api/prices', { cache: 'no-store' }), 
                    fetch('/api/checklist', { cache: 'no-store' }), 
                    fetch('/api/logs', { cache: 'no-store' })
                ]);
                if (resCfg.ok) {
                    const fetchedCfg = await resCfg.json();
                    for (const key in fetchedCfg) {
                        if (key !== 'selected_items') cfg.value[key] = fetchedCfg[key];
                    }
                    if (fetchedCfg.activeTab) activeTab.value = fetchedCfg.activeTab;
                    if (fetchedCfg.activePriceTab) activePriceTab.value = fetchedCfg.activePriceTab;
                    if (fetchedCfg.activeListItemTab) activeListItemTab.value = fetchedCfg.activeListItemTab;
                    
                    if (fetchedCfg.selected_items) {
                        for (const item in fetchedCfg.selected_items) {
                            const val = fetchedCfg.selected_items[item];
                            if (typeof val === 'boolean' || val === null || val === undefined) {
                                cfg.value.selected_items[item] = { '.0': val, '.1': val, '.2': val, '.3': val, '.4': val };
                            } else {
                                cfg.value.selected_items[item] = val;
                            }
                        }
                    }
                    if(!cfg.value.frag_cities) cfg.value.frag_cities = { rune: cfg.value.buy_city, soul: cfg.value.buy_city, relic: cfg.value.buy_city };
                    if(!cfg.value.tome_city) cfg.value.tome_city = cfg.value.buy_city;
                    if(!cfg.value.smart_budget) cfg.value.smart_budget = 16000000;
                    
                    if(!cfg.value.ai_settings) {
                        cfg.value.ai_settings = { max_items: 10, min_profit: 1000, min_margin: 15, vol_target: 20, gear_filter: 'mixed', enc: {'.0':true, '.1':true, '.2':true, '.3':true, '.4':false} };
                    } else {
                        if (cfg.value.ai_settings.vol_target === undefined) cfg.value.ai_settings.vol_target = 20; 
                        if (!cfg.value.ai_settings.gear_filter) cfg.value.ai_settings.gear_filter = 'mixed';
                        if (!cfg.value.ai_settings.enc) cfg.value.ai_settings.enc = {'.0':true, '.1':true, '.2':true, '.3':true, '.4':false};
                    }

                    if(!cfg.value.cancelled_crafts) cfg.value.cancelled_crafts = {};
                    if(!cfg.value.adjusted_qty_crafts) cfg.value.adjusted_qty_crafts = {}; 
                    if(cfg.value.use_multi_tier === undefined) cfg.value.use_multi_tier = false;

                    // --- QTY BUCKET MIGRATION: populate buckets from flat q0-q4 if buckets are empty ---
                    if (!cfg.value.qty_gear) cfg.value.qty_gear = { q0: 0, q1: 0, q2: 0, q3: 0, q4: 0 };
                    if (!cfg.value.qty_refine) cfg.value.qty_refine = { q0: 0, q1: 0, q2: 0, q3: 0, q4: 0 };
                    if (!cfg.value.qty_cook) cfg.value.qty_cook = { q0: 0, q1: 0, q2: 0, q3: 0, q4: 0 };
                    const allBucketsEmpty = [cfg.value.qty_gear, cfg.value.qty_refine, cfg.value.qty_cook].every(b => !b.q0 && !b.q1 && !b.q2 && !b.q3 && !b.q4);
                    if (allBucketsEmpty && (cfg.value.q0 || cfg.value.q1 || cfg.value.q2 || cfg.value.q3 || cfg.value.q4)) {
                        const activeBucket = cfg.value.use_multi_consumables ? cfg.value.qty_cook : cfg.value.use_refine_only ? cfg.value.qty_refine : cfg.value.qty_gear;
                        activeBucket.q0 = cfg.value.q0; activeBucket.q1 = cfg.value.q1; activeBucket.q2 = cfg.value.q2; activeBucket.q3 = cfg.value.q3; activeBucket.q4 = cfg.value.q4;
                    } else {
                        syncQtyToFlat();
                    }
                }
                if (resPrices.ok) {
                    pricesData.value = await resPrices.json();
                    initPricesData();
                }
                if (resCheck.ok) {
                    const loadedChecks = await resCheck.json();
                    for (let id in loadedChecks) {
                        if (loadedChecks[id]) granted_fame.value[id] = true; 
                    }
                    checkedTasks.value = loadedChecks;
                }
                if (resLogs.ok) {
                    logsData.value = await resLogs.json();
                    if (activeTab.value === 'logs') nextTick(renderProfitChart);
                }
                
                if (!cfg.value.profiles) cfg.value.profiles = { "Default": { ...cfg.value.specs, fame_exact: {} } };
                if (!cfg.value.active_profile || !cfg.value.profiles[cfg.value.active_profile]) cfg.value.active_profile = "Default";

                // Migration: ensure all profiles have stone refining spec
                for (const pName in cfg.value.profiles) {
                    const p = cfg.value.profiles[pName];
                    if (!p.stone) p.stone = { s: 1 };
                }
                if (!availableDestinations.value.includes(cfg.value.route_to)) cfg.value.route_to = availableDestinations.value[0];
                const crafted = pricesData.value?.[cfg.value.sell_city]?.[tierKey.value]?.crafted;
                if (crafted) for (const cat in crafted) if (!(cat in acc.value)) acc.value[cat] = false;
                
                triggerCalculate();
            } catch (e) {}
            
            await nextTick();
            isInitializing.value = false;
        };

        const fetchFromADC = async () => {
            if (isFetchingADC.value) return;
            isFetchingADC.value = true;
            showToast("ADC Data Sync", "Proses tarik data sedang berjalan. Halaman akan otomatis refresh dalam 5 detik.", "info");
            try {
                const res = await fetch('/api/adc_fetch', { method: 'POST' });
                if (res.ok) {
                    setTimeout(async () => {
                        await fetchConfigAndData();
                        isFetchingADC.value = false;
                        showToast("ADC Sync Complete", "Data market terbaru berhasil disinkronisasi!", "success");
                    }, 5000);
                } else {
                    isFetchingADC.value = false;
                    showToast("ADC Sync Error", "Gagal menghubungi server ADC.", "error");
                }
            } catch (e) {
                isFetchingADC.value = false;
                showToast("Connection Error", "Gagal konek ke server API ADC.", "error");
            }
        };

        let calcTimer = null;
        const triggerCalculate = () => {
            clearTimeout(calcTimer);
            calcTimer = setTimeout(async () => {
                try {
                    const resData = await fetch('/api/calculate', { cache: 'no-store' });
                    if (resData.ok) {
                        data.value = await resData.json();
                        if (data.value.ai_recovery_reasoning) {
                            console.warn("AI AUTO-RECOVERY TRIGGERED:", data.value.ai_recovery_reasoning);
                            // Optional: can show an alert or just log to avoid spamming the user on every type event
                            // alert("AI Auto-Recovery: " + data.value.ai_recovery_reasoning);
                        }
                    }
                } catch (e) {}
            }, 300);
        };

        const saveAndFetch = async () => {
            try {
                syncFlatToBucket();
                syncFameExact();
                if (cfg.value.profiles?.[cfg.value.active_profile]) cfg.value.specs = JSON.parse(JSON.stringify(cfg.value.profiles[cfg.value.active_profile]));
                if (!availableDestinations.value.includes(cfg.value.route_to)) cfg.value.route_to = availableDestinations.value[0];
                await fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cfg.value) });
                triggerCalculate();
            } catch (e) {}
        };

        const savePricesAndFetch = async (city, tier, cat, enchant) => {
            try {
                if (typeof city === 'string' && tier && cat && enchant) {
                    if (!pricesData.value[city]) pricesData.value[city] = {};
                    if (!pricesData.value[city][tier]) pricesData.value[city][tier] = {};
                    if (!pricesData.value[city][tier].timestamps) pricesData.value[city][tier].timestamps = {};
                    pricesData.value[city][tier].timestamps[`${cat}_${enchant}`] = new Date().toISOString() + "Z";
                }
                fetch('/api/prices', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(pricesData.value) });
                triggerCalculate();
            } catch (e) {}
        };

        const exportToLogs = () => {
            if (!data.value) return;
            const itemsList = [];
            const tk = `t${cfg.value.tier}`;
            const targetMargins = data.value.analyzer_margins || data.value.unit_margins;
            if (data.value && targetMargins) {
                for (const cat in targetMargins) {
                    for (const itemName in targetMargins[cat]) {
                        const encs = cfg.value.selected_items[itemName];
                        if (!encs) continue;
                        for (const e of Object.keys(encs)) {
                            if (encs[e]) {
                                const eIdx = e.replace('.', '');
                                const globalQ = cfg.value[`q${eIdx}`];
                                const adjustedQ = cfg.value.adjusted_qty_crafts?.[itemName]?.[e];
                                const q = adjustedQ !== undefined ? adjustedQ : globalQ;
                                
                                if (q > 0) {
                                    const uData = targetMargins[cat][itemName][e];
                                    const actualTk = `t${uData.t}`;
                                    const sellP = pricesData.value?.[cfg.value.sell_city]?.[actualTk]?.crafted?.[cat]?.[itemName]?.[e] || 0;
                                    itemsList.push({
                                        cat: cat,
                                        item: itemName,
                                        enchant: e,
                                        qty: q,
                                        unit_cost: uData.cost, 
                                        orig_sell: sellP,
                                        orig_profit: uData.p,
                                        t: uData.t
                                    });
                                }
                            }
                        }
                    }
                }
            }

            const totalCost = data.value.financial.total_capital;
            const totalRev = totalCost + data.value.financial.grand_profit;
            const origGearRev = data.value.financial.rev_bm_gears || 0;

            const setupSnapshot = {
                tier: cfg.value.tier,
                q0: cfg.value.q0, q1: cfg.value.q1, q2: cfg.value.q2, q3: cfg.value.q3, q4: cfg.value.q4,
                adjusted_qty_crafts: JSON.parse(JSON.stringify(cfg.value.adjusted_qty_crafts || {})),
                selected_items: JSON.parse(JSON.stringify(cfg.value.selected_items)),
                buy_city: cfg.value.buy_city, sell_city: cfg.value.sell_city, craft_city: cfg.value.craft_city,
                use_multi_refine: cfg.value.use_multi_refine,
                route_from: cfg.value.route_from, route_to: cfg.value.route_to,
                raw_cities: JSON.parse(JSON.stringify(cfg.value.raw_cities)),
                refine_cities: JSON.parse(JSON.stringify(cfg.value.refine_cities)),
                frag_cities: JSON.parse(JSON.stringify(cfg.value.frag_cities))
            };

            logsData.value.unshift({
                date: new Date().toISOString().split('T')[0],
                item: `Batch T${cfg.value.tier} (Q: ${cfg.value.q0}/${cfg.value.q1}/${cfg.value.q2}/${cfg.value.q3}/${cfg.value.q4})`,
                notes: "Setup Saved",
                cost: totalCost,
                revenue: totalRev,
                original_gear_rev: origGearRev,
                setup: setupSnapshot,
                items: itemsList
            });
            saveLogs();
            alert("Data sukses diekspor ke Trading Logs!");
        };

        const loadLogSetup = (idx) => {
            const log = liveLogs.value[idx];
            const setup = log.setup;
            if (!setup) return alert("Log ini tidak memiliki data setup yang tersimpan.");
            
            if (confirm("Load setup ini? Sistem akan OTOMATIS nge-bersihin (uncheck) barang yang sekarang profitnya MINUS.")) {
                cfg.value.tier = setup.tier;
                cfg.value.q0 = setup.q0; cfg.value.q1 = setup.q1; cfg.value.q2 = setup.q2; cfg.value.q3 = setup.q3; cfg.value.q4 = setup.q4;
                syncFlatToBucket();
                
                cfg.value.adjusted_qty_crafts = setup.adjusted_qty_crafts ? JSON.parse(JSON.stringify(setup.adjusted_qty_crafts)) : {};

                cfg.value.buy_city = setup.buy_city; cfg.value.sell_city = setup.sell_city; cfg.value.craft_city = setup.craft_city || "Lymhurst";
                cfg.value.use_multi_refine = setup.use_multi_refine ?? true;
                cfg.value.route_from = setup.route_from; cfg.value.route_to = setup.route_to;
                cfg.value.raw_cities = JSON.parse(JSON.stringify(setup.raw_cities));
                cfg.value.refine_cities = JSON.parse(JSON.stringify(setup.refine_cities));
                if(setup.frag_cities) cfg.value.frag_cities = JSON.parse(JSON.stringify(setup.frag_cities));
                
                let newSelected = JSON.parse(JSON.stringify(setup.selected_items));
                let removedCount = 0;

                if (log.items) {
                    log.items.forEach(i => {
                        if (i.cur_profit < 0) {
                            newSelected[i.item][i.enchant] = false;
                            removedCount++;
                        }
                    });
                }
                
                cfg.value.selected_items = newSelected;
                saveAndFetch();
                activeTab.value = 'dashboard';
                
                if (removedCount > 0) {
                    setTimeout(() => alert(`Load sukses! Ada ${removedCount} variasi barang yang di-uncheck otomatis karena harganya sekarang MINUS.`), 500);
                }
            }
        };

        const mergeLogSetup = (idx) => {
            const log = liveLogs.value[idx];
            const setup = log.setup;
            if (!setup) return alert("Log ini tidak memiliki data setup yang tersimpan.");
            
            if (confirm("Merge (Gabung) setup ini ke Dashboard? Item yang profitnya MINUS akan otomatis diabaikan/uncheck.")) {
                cfg.value.q0 = Math.max(cfg.value.q0, setup.q0 || 0);
                cfg.value.q1 = Math.max(cfg.value.q1, setup.q1 || 0);
                cfg.value.q2 = Math.max(cfg.value.q2, setup.q2 || 0);
                cfg.value.q3 = Math.max(cfg.value.q3, setup.q3 || 0);
                cfg.value.q4 = Math.max(cfg.value.q4, setup.q4 || 0);
                
                if (setup.adjusted_qty_crafts) {
                    for (let item in setup.adjusted_qty_crafts) {
                        if (!cfg.value.adjusted_qty_crafts[item]) cfg.value.adjusted_qty_crafts[item] = {};
                        for (let enc in setup.adjusted_qty_crafts[item]) {
                            let oldQ = cfg.value.adjusted_qty_crafts[item][enc] || 0;
                            let newQ = setup.adjusted_qty_crafts[item][enc];
                            cfg.value.adjusted_qty_crafts[item][enc] = Math.max(oldQ, newQ);
                        }
                    }
                }

                let addedCount = 0;
                let ignoredCount = 0;

                if (log.items) {
                    log.items.forEach(i => {
                        if (!cfg.value.selected_items[i.item]) {
                            cfg.value.selected_items[i.item] = { '.0': false, '.1': false, '.2': false, '.3': false, '.4': false };
                        }
                        
                        if (i.cur_profit < 0) {
                            cfg.value.selected_items[i.item][i.enchant] = false;
                            ignoredCount++;
                        } else {
                            if (!cfg.value.selected_items[i.item][i.enchant]) {
                                cfg.value.selected_items[i.item][i.enchant] = true;
                                addedCount++;
                            }
                        }
                    });
                }
                
                saveAndFetch();
                activeTab.value = 'dashboard';
                
                setTimeout(() => alert(`Merge sukses!\n✅ ${addedCount} variasi barang ditambahkan.\n❌ ${ignoredCount} barang diabaikan (karena profitnya minus).`), 500);
            }
        };

        const saveLogs = async () => {
            await fetch('/api/logs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(logsData.value) });
        };

        const addLogEntry = () => {
            logsData.value.unshift({ date: new Date().toISOString().split('T')[0], item: "", notes: "", cost: 0, revenue: 0 });
            saveLogs();
        };

        const deleteLogEntry = (idx) => {
            if (confirm('Hapus log ini?')) { logsData.value.splice(idx, 1); saveLogs(); }
        };

        const addProfile = () => { 
            const name = prompt("Nama Akun/Profile Baru:"); 
            if (name && name.trim() && !cfg.value.profiles[name]) { 
                cfg.value.profiles[name] = {
                    fiber:{s:100}, hide:{s:100}, ore:{s:100}, wood:{s:100}, stone:{s:100},
                    main_specs: {}, fame_exact: {}
                }; 
                cfg.value.active_profile = name; 
                saveAndFetch(); 
            } 
        };
        const deleteProfile = () => { if (cfg.value.active_profile !== 'Default' && confirm(`Hapus profile?`)) { delete cfg.value.profiles[cfg.value.active_profile]; cfg.value.active_profile = "Default"; saveAndFetch(); } };
        
        const selectAllCat = (catName) => { 
            const items = pricesData.value?.[cfg.value.sell_city]?.[tierKey.value]?.crafted?.[catName]; 
            if (!items) return; 
            for (const item in items) {
                // Whole-object assignment to ensure deep reactivity detection
                cfg.value.selected_items[item] = { '.0': true, '.1': true, '.2': true, '.3': true, '.4': true };
            }
            saveAndFetch(); 
        };
        const deselectAllCat = (catName) => { 
            const items = pricesData.value?.[cfg.value.sell_city]?.[tierKey.value]?.crafted?.[catName]; 
            if (!items) return; 
            for (const item in items) {
                cfg.value.selected_items[item] = { '.0': false, '.1': false, '.2': false, '.3': false, '.4': false };
            }
            saveAndFetch(); 
        };

        const getItemFreshnessTime = (city, tier, cat, enchant) => {
            if (!pricesData.value?.[city]?.[tier]?.timestamps) return '—';
            let ts = pricesData.value[city][tier].timestamps[`${cat}_${enchant}`];
            if (!ts) return '—';
            if (!ts.endsWith('Z')) ts += 'Z'; 
            return new Date(ts).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
        };
        const getItemFreshnessTextClass = (city, tier, cat, enchant) => {
            if (!pricesData.value?.[city]?.[tier]?.timestamps) return 'text-gray-600';
            let ts = pricesData.value[city][tier].timestamps[`${cat}_${enchant}`];
            if (!ts) return 'text-gray-600'; 
            if (!ts.endsWith('Z')) ts += 'Z';
            const diffHours = (Date.now() - new Date(ts).getTime()) / (1000 * 60 * 60);
            return diffHours < 2 ? 'text-emerald-400' : diffHours < 24 ? 'text-amber-400' : 'text-rose-500';
        };
        const getItemFreshnessClass = (city, tier, cat, enchant) => {
            if (!pricesData.value?.[city]?.[tier]?.timestamps) return '';
            let ts = pricesData.value[city][tier].timestamps[`${cat}_${enchant}`];
            if (!ts) return ''; 
            if (!ts.endsWith('Z')) ts += 'Z';
            const diffHours = (Date.now() - new Date(ts).getTime()) / (1000 * 60 * 60);
            if (diffHours < 2) return '!border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]';
            return diffHours < 24 ? '!border-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.3)]' : '!border-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.3)]';
        };

        const updateRealTimeData = () => {
            const now = new Date(); currentTimeFormatted.value = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
            const currentUTCHour = now.getUTCHours(); const nextEntry = banditScheduleUTC.find(e => e.h > currentUTCHour) || banditScheduleUTC[0];
            const wibHour = (nextEntry.h + 7) % 24; nextBanditStr.value = `${String(wibHour).padStart(2,'0')}:00 WIB (Chance: ${nextEntry.c})`;
        };

        let currentPriceVersion = -1;
        const _deepMerge = (target, source) => {
            for (const key in source) {
                if (source[key] instanceof Object && key in target && !Array.isArray(source[key])) {
                    _deepMerge(target[key], source[key]);
                } else {
                    target[key] = source[key];
                }
            }
        };

        const syncScannedPrices = async () => {
            if (isSyncingScanned.value || isFetchingADC.value || isAnalyzing.value) return;
            isSyncingScanned.value = true;
            try {
                const res = await fetch('/api/prices_version', { cache: 'no-store' });
                if (res.ok) {
                    const data = await res.json();
                    if (currentPriceVersion === -1 || data.version > currentPriceVersion) {
                        currentPriceVersion = data.version;
                        const pRes = await fetch('/api/prices', { cache: 'no-store' });
                        if (pRes.ok) {
                            const newPrices = await pRes.json();
                            _deepMerge(pricesData.value, newPrices);
                            initPricesData();
                            triggerCalculate();
                        }
                    }
                }
            } catch (e) {
                console.error("Manual sync failed:", e);
            } finally {
                isSyncingScanned.value = false;
            }
        };

        onMounted(() => {
            fetchConfigAndData();
            updateRealTimeData();
            setInterval(updateRealTimeData, 1000);
            setInterval(fetchConfigAndData, 30000); // Auto-sync config from server every 30s
            setTimeout(() => { if (window.lucide) lucide.createIcons(); }, 500);
        });
        watch(activeTab, () => {
            nextTick(() => { if (window.lucide) lucide.createIcons(); });
        });

        // REMOVED: deep cfg watcher that called lucide.createIcons().
        // lucide.createIcons() destructively replaces <i> with <svg>,
        // corrupting Vue's VDOM anchors and causing insertBefore crashes.
        // Icons are already initialized by onMounted and activeTab watcher.

        return {
            activeTab, showLogMenu, showMainMenu, showLogisticsSubMenu, showPriceSubMenu, showListItemSubMenu, activePriceTab, activeListItemTab, activeTabLabel, acc, cfg, data, pricesData, p_buy, p_buy_mat, p_buy_farm, luxuryArbitrage, p_sell, tierKey, MAT_LIST, ALL_ROYAL_CITIES, ALL_SELL_CITIES, JOURNAL_TYPES, availableDestinations,
            journalBestSell, getItemFreshnessClass, getItemFreshnessTime, getItemFreshnessTextClass, getRefineCity, getRealName,
            saveAndFetch, savePricesAndFetch, fetchConfigAndData, fetchFromADC, isFetchingADC, isSyncingScanned, syncScannedPrices, currentTimeFormatted, nextBanditStr, selectAllCat, deselectAllCat, addProfile, deleteProfile,
            volFilter, volHistory, volSummary, volItemList, volChartItem, volAmountMode, volSearch, filteredVolItemList, loadVolumeData, clearVolumeHistory, renderTrendChart, renderAmountChart, formatK,
            checkedTasks, clearChecks, routeLogistics, dynamicPeakWeight, toggleCancelCraft, setCraftQty,
            logsData, liveLogs, expandedLogs, logsProfitStats, saveLogs, addLogEntry, deleteLogEntry, exportToLogs, loadLogSetup, mergeLogSetup, toggleLiveMonitor,
            selectedItemList, categoryProfits, groupedCategories, fragmentPrices, artifactBestBuy, farmingGroups, SPEC_NODES,
            unselectAllItems, sortKey, sortDesc, toggleSort,
            runSmartAnalyzer, smartSetupResult, isAnalyzing, applySmartSetup, isItemSelected, toggleItem, checkAccess,
            notification, showToast, CREST_HEART_LIST, RAW_OF, TOME_OF_INSIGHT_TIERS
        };
    }
}).mount('#app');