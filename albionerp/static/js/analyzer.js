import { getBMBaseVolume } from './utils.js';

export function setupAnalyzer(cfg, data, isAnalyzing, smartSetupResult) {
    const runSmartAnalyzer = async (mode) => {
        if (!data.value || !data.value.unit_margins) return alert("Kalkulasi dasar belum siap. Pastikan server nyala.");
        if (!cfg.value.smart_budget || cfg.value.smart_budget < 100000) return alert("Budget kekecilan, minimal 100k.");
        
        const ai = cfg.value.ai_settings;
        isAnalyzing.value = true;
        smartSetupResult.value = null;

        try {
            const res = await fetch(`/api/volume?tier=${cfg.value.tier}&days=7`, { cache: 'no-store' });
            const volData = await res.json();
            const history = volData.history || [];

            const volMap = {};
            history.forEach(r => {
                if (!volMap[r.item]) volMap[r.item] = {};
                if (!volMap[r.item][r.enchant]) volMap[r.item][r.enchant] = { volume: 0 };
                volMap[r.item][r.enchant].volume += r.volume;
            });

            let allCandidates = [];
            const margins = data.value.analyzer_margins || data.value.unit_margins;
            const volTargetMultiplier = (ai.vol_target || 20) / 100; 

            for (const cat in margins) {
                // 🎯 FILTER MODE: GEAR vs CONSUMABLE
                if (mode === 'gear') {
                    if (['foods', 'potions', 'luxury'].includes(cat)) continue;
                    
                    const isArtifact = cat.startsWith('artifact_');
                    if (ai.item_type === 'normal' && isArtifact) continue;
                    if (ai.item_type === 'artifact' && !isArtifact) continue;
                } else if (mode === 'consumable') {
                    if (!['foods', 'potions'].includes(cat)) continue;
                }

                for (const item in margins[cat]) {
                    const itemData = margins[cat][item];

                    ['.0', '.1', '.2', '.3', '.4'].forEach(e => {
                        if (ai.enc && ai.enc[e] === false) return;

                        const unitData = itemData[e];
                        if (!unitData || unitData.cost === 0) return; 

                        // 🚀 PROFIT ALIGNMENT: Use server profit (p) and unit cost
                        let unitProfit = unitData.p;
                        let unitMargin = unitData.pct;
                        let unitCost   = unitData.cost; 
                        let unitWeight = unitData.w;

                        if (unitProfit >= ai.min_profit && unitMargin >= ai.min_margin) {
                            let totalVol7Days = volMap[item]?.[e]?.volume || 0;
                            let dailyVol = totalVol7Days / 7;
                            
                            let isFallback = false;
                            let activeDailyVol = dailyVol;

                            if (dailyVol < 1) {
                                activeDailyVol = getBMBaseVolume(cat, cfg.value.tier, e);
                                isFallback = true;
                            }

                            // 📊 SCORING (Profit Density)
                            let score = unitProfit * (unitMargin / 100);
                            if (activeDailyVol > 20) score *= 1.2;

                            if (score > 0) {
                                allCandidates.push({
                                    cat, item, enchant: e,
                                    profit: unitProfit, margin: unitMargin, 
                                    activeDailyVol, cost: unitCost, weight: unitWeight, isFallback,
                                    score: score, y_yield: unitData.y || 1
                                });
                            }
                        }
                    });
                }
            }

            if (allCandidates.length === 0) {
                isAnalyzing.value = false;
                return alert("Gagal nemu barang! Perkecil filter Min Profit/Margin lu.");
            }

            allCandidates.sort((a, b) => b.score - a.score);

            let budget = cfg.value.smart_budget;
            let finalSelected = {}; 
            let finalAdjustedQty = {};
            let totalEstCost = 0;
            let totalEstProfit = 0;
            let totalEstWeight = 0;
            let acceptedItems = new Set();
            let aiReasoning = "Menganalisa dengan AI/Fallback...";
            const maxSlots = Math.min(ai.max_items || 48, 48); 

            try {
                const llmRes = await fetch('/api/smart_llm', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        budget: budget,
                        mode: mode,
                        candidates: allCandidates.slice(0, 100) // Send top 100 to save context
                    })
                });

                if (!llmRes.ok) throw new Error("Endpoint failed");
                const llmData = await llmRes.json();
                if (llmData.error) throw new Error(llmData.error);

                // Parse LLM Response
                const picks = llmData.picks || [];
                const adjQty = llmData.adjusted_qty || {};

                // Use backend-computed totals (accurate headless engine values)
                const hasBackendTotals = (llmData.total_cost > 0);
                if (hasBackendTotals) {
                    totalEstCost = llmData.total_cost;
                    totalEstProfit = llmData.total_profit;
                }

                for (const item of picks) {
                    if (adjQty[item]) {
                        for (const e in adjQty[item]) {
                            const cand = allCandidates.find(c => c.item === item && c.enchant === e);
                            if (cand) {
                                const qty = adjQty[item][e];
                                if (qty > 0) {
                                    if (!finalSelected[item]) finalSelected[item] = {};
                                    finalSelected[item][e] = true;

                                    if (!finalAdjustedQty[item]) finalAdjustedQty[item] = {};
                                    finalAdjustedQty[item][e] = qty;

                                    totalEstWeight += (cand.weight * qty * cand.y_yield);
                                    // Fallback: only accumulate from candidates if backend didn't send totals
                                    if (!hasBackendTotals) {
                                        totalEstCost   += (cand.cost   * qty);
                                        totalEstProfit += (cand.profit * qty);
                                    }
                                    acceptedItems.add(item);
                                }
                            }
                        }
                    }
                }

                aiReasoning = llmData.reasoning || "Analisa LLM selesai.";
            } catch (err) {
                console.error("LLM Error:", err);
                isAnalyzing.value = false;
                return alert("Gagal melakukan analisa AI dan Fallback: " + err.message);
            }

            if (totalEstCost === 0) {
                isAnalyzing.value = false;
                return alert("Budget kekecilan atau LLM gagal memilih item.");
            }

            let newSelected = JSON.parse(JSON.stringify(cfg.value.selected_items));
            let newAdjustedQty = JSON.parse(JSON.stringify(cfg.value.adjusted_qty_crafts || {}));

            // Clear existing selection for the active mode only
            const margins_all = data.value.unit_margins;
            for (const c in margins_all) {
                if (mode === 'gear' && ['foods', 'potions', 'luxury'].includes(c)) continue;
                if (mode === 'consumable' && !['foods', 'potions'].includes(c)) continue;
                for (const i in margins_all[c]) {
                    if (newSelected[i]) newSelected[i] = { '.0': false, '.1': false, '.2': false, '.3': false, '.4': false };
                    if (newAdjustedQty[i]) delete newAdjustedQty[i];
                }
            }

            for (const item in finalSelected) {
                if (!newSelected[item]) newSelected[item] = { '.0': false, '.1': false, '.2': false, '.3': false, '.4': false };
                for (const e in finalSelected[item]) {
                    newSelected[item][e] = true;
                    if (!newAdjustedQty[item]) newAdjustedQty[item] = {};
                    newAdjustedQty[item][e] = finalAdjustedQty[item][e];
                }
            }

            smartSetupResult.value = {
                picks: Array.from(acceptedItems),
                adjusted_qty: newAdjustedQty,
                selected_items: newSelected,
                estCost: Math.floor(totalEstCost),
                estProfit: Math.floor(totalEstProfit),
                estWeight: Math.ceil(totalEstWeight),
                reasoning: aiReasoning
            };
        } catch (error) {
            alert("Error Analyzer.");
            console.error(error);
        } finally {
            isAnalyzing.value = false;
        }
    };

    return { runSmartAnalyzer };
}