"""
Albion Online ERP — AI Analyzer Module (Batch 2 Overhaul)

Responsibilities:
1. Smart API Key Rotation with dynamic cooldown (Retry-After / exponential backoff)
2. Local AI Fallback using real calculator.py math + volume trend analysis
3. Profit calculation synchronization — no standalone math, shares calculator.py functions
"""

import copy
import logging
import math
import threading
import time
import urllib.request
import urllib.error

import orjson

from core.calculator import (
    sfloat, sint,
    execute_calculation,
)
from core.constants import (
    ENCHANTS, ITEM_TO_MAIN_SPEC,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. API KEY MANAGER — Stateful rotation with dynamic cooldown
# ---------------------------------------------------------------------------

_MIN_COOLDOWN_S = 900       # 15 minutes floor
_MAX_COOLDOWN_S = 43200     # 12 hours ceiling
_BACKOFF_BASE_S = 900       # first backoff = 15 min


class ApiKeyManager:
    """Thread-safe pool of Gemini API keys with per-key dynamic cooldown."""

    def __init__(self):
        self._lock = threading.RLock()
        # key_index -> raw key string
        self._keys: list[str] = []
        # raw key string -> resume unix timestamp
        self._cooldowns: dict[str, float] = {}
        # raw key string -> consecutive failure count (for exponential backoff)
        self._fail_counts: dict[str, int] = {}
        # round-robin pointer
        self._next_idx: int = 0

    # -- Configuration --------------------------------------------------------

    def configure(self, keys_csv: str) -> None:
        """Parse comma-separated API keys and refresh the pool.
        Keys already tracked keep their cooldown state."""
        new_keys = [k.strip() for k in keys_csv.split(",") if k.strip()]
        with self._lock:
            old_set = set(self._keys)
            self._keys = new_keys
            # Prune cooldown/fail state for removed keys
            current_set = set(new_keys)
            for removed in old_set - current_set:
                self._cooldowns.pop(removed, None)
                self._fail_counts.pop(removed, None)
            # Reset pointer if pool changed
            if self._next_idx >= len(self._keys):
                self._next_idx = 0

    # -- Cooldown logic -------------------------------------------------------

    def _put_on_cooldown(self, key: str, retry_after: float | None) -> None:
        """Must be called INSIDE self._lock."""
        count = self._fail_counts.get(key, 0) + 1
        self._fail_counts[key] = count

        if retry_after and retry_after > 0:
            cooldown_s = max(retry_after, _MIN_COOLDOWN_S)
        else:
            # Exponential backoff: 15m, 30m, 60m, 120m ... capped at 12h
            cooldown_s = min(_BACKOFF_BASE_S * (2 ** (count - 1)), _MAX_COOLDOWN_S)

        self._cooldowns[key] = time.time() + cooldown_s
        logger.warning(
            "API key %s...%s on cooldown for %.0f seconds (fail #%d)",
            key[:4], key[-4:], cooldown_s, count,
        )

    def _clear_cooldown(self, key: str) -> None:
        """Must be called INSIDE self._lock."""
        self._cooldowns.pop(key, None)
        self._fail_counts.pop(key, None)

    def _is_available(self, key: str, now: float) -> bool:
        """Must be called INSIDE self._lock."""
        resume = self._cooldowns.get(key)
        if resume is None:
            return True
        if now >= resume:
            # Cooldown expired — auto-clear
            self._cooldowns.pop(key, None)
            # Keep fail_count so next failure backs off further
            return True
        return False

    # -- Public API -----------------------------------------------------------

    def get_available_key(self) -> str | None:
        """Return the next available key via round-robin, or None if all on cooldown."""
        now = time.time()
        with self._lock:
            n = len(self._keys)
            if n == 0:
                return None
            # Try each key starting from _next_idx
            for _ in range(n):
                key = self._keys[self._next_idx % n]
                self._next_idx = (self._next_idx + 1) % n
                if self._is_available(key, now):
                    return key
        return None

    def report_success(self, key: str) -> None:
        """Mark a key as healthy — clears cooldown and fail count."""
        with self._lock:
            self._clear_cooldown(key)

    def report_rate_limit(self, key: str, retry_after: float | None) -> None:
        """Mark a key as rate-limited with optional Retry-After seconds."""
        with self._lock:
            self._put_on_cooldown(key, retry_after)

    def report_error(self, key: str) -> None:
        """Mark a key as errored (non-429) — short cooldown."""
        with self._lock:
            self._put_on_cooldown(key, _MIN_COOLDOWN_S)

    def all_on_cooldown(self) -> bool:
        """True if every key in the pool is currently on cooldown."""
        now = time.time()
        with self._lock:
            if not self._keys:
                return True
            return all(not self._is_available(k, now) for k in self._keys)

    def get_status(self) -> dict:
        """Return a serializable status summary for debugging/UI."""
        now = time.time()
        with self._lock:
            entries = []
            for k in self._keys:
                cd = self._cooldowns.get(k)
                entries.append({
                    "key_hint": f"{k[:4]}...{k[-4:]}" if len(k) > 8 else "****",
                    "available": self._is_available(k, now),
                    "cooldown_remaining_s": max(0, int((cd or now) - now)),
                    "fail_count": self._fail_counts.get(k, 0),
                })
            return {"keys": entries, "total": len(self._keys)}


# Module-level singleton
_key_manager = ApiKeyManager()


def get_key_manager() -> ApiKeyManager:
    """Access the module-level ApiKeyManager singleton."""
    return _key_manager


# ---------------------------------------------------------------------------
# 2. GEMINI API CALL — Uses key manager for rotation
# ---------------------------------------------------------------------------

def _parse_retry_after(http_error: urllib.error.HTTPError) -> float | None:
    """Extract Retry-After header value in seconds. Returns None if absent/invalid."""
    raw = http_error.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def call_gemini_api(
    api_keys_str: str,
    prompt: str,
    fallback_data: dict | None = None,
    max_attempts: int = 6,
) -> dict:
    """Call Gemini API with smart key rotation and dynamic cooldown.

    Args:
        api_keys_str: Comma-separated API keys from config.
        prompt: The LLM prompt string.
        fallback_data: Dict to return if all attempts fail.
        max_attempts: Total call attempts across all keys.
    """
    mgr = get_key_manager()
    mgr.configure(api_keys_str)

    payload = orjson.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    })
    headers = {"Content-Type": "application/json"}

    last_error = None

    for attempt in range(max_attempts):
        key = mgr.get_available_key()
        if key is None:
            logger.warning(
                "All API keys on cooldown (attempt %d/%d). Falling back to local.",
                attempt + 1, max_attempts,
            )
            break

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={key}"
        )

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = response.read().decode("utf-8")

            res_json = orjson.loads(res_body)
            text_response = res_json["candidates"][0]["content"]["parts"][0]["text"]
            text_response = text_response.replace("```json", "").replace("```", "").strip()
            parsed = orjson.loads(text_response.encode("utf-8"))

            mgr.report_success(key)
            return parsed

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass

            logger.error(
                "Gemini HTTP %d with key %s...%s (attempt %d): %s",
                e.code, key[:4], key[-4:], attempt + 1, error_body[:300],
            )
            last_error = Exception(f"API Error: {e.code} - {error_body[:200]}")

            if e.code == 429:
                retry_after = _parse_retry_after(e)
                mgr.report_rate_limit(key, retry_after)
            else:
                mgr.report_error(key)

        except Exception as e:
            logger.error(
                "Gemini call error with key %s...%s (attempt %d): %s",
                key[:4], key[-4:], attempt + 1, e,
            )
            last_error = e
            mgr.report_error(key)

    # All attempts exhausted
    if fallback_data is not None:
        logger.info("Returning fallback data after exhausting all API keys.")
        return fallback_data

    raise last_error or Exception("All API keys failed or on cooldown.")


# ---------------------------------------------------------------------------
# 3. LOCAL FALLBACK — Deep analysis using real calculator.py math
# ---------------------------------------------------------------------------

def _compute_volume_trend(volume_records: list, item_name: str, enchant: str) -> dict:
    """Compute basic trend metrics for a specific item+enchant from volume history.

    Returns dict with: avg_price, price_trend (slope direction), avg_daily_volume,
    liquidity_score (0-100), data_points.
    """
    # Filter records for this item
    relevant = [
        r for r in volume_records
        if r.get("item") == item_name and r.get("enchant") == enchant
    ]

    if not relevant:
        return {
            "avg_price": 0,
            "price_trend": "unknown",
            "avg_daily_volume": 0,
            "liquidity_score": 0,
            "data_points": 0,
        }

    prices = [sfloat(r.get("price", 0)) for r in relevant if sfloat(r.get("price", 0)) > 0]
    volumes = [sfloat(r.get("volume", 0)) for r in relevant]

    avg_price = sum(prices) / len(prices) if prices else 0

    # Simple trend: compare first half avg vs second half avg
    if len(prices) >= 4:
        mid = len(prices) // 2
        first_half = sum(prices[:mid]) / mid
        second_half = sum(prices[mid:]) / (len(prices) - mid)
        if second_half > first_half * 1.03:
            trend = "rising"
        elif second_half < first_half * 0.97:
            trend = "falling"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    avg_daily_vol = sum(volumes) / max(len(volumes), 1)

    # Liquidity score: 0-100 based on volume and data freshness
    # Higher volume and more data points = better liquidity
    vol_score = min(avg_daily_vol / 50.0, 1.0) * 60  # volume component (0-60)
    data_score = min(len(relevant) / 20.0, 1.0) * 40  # data richness component (0-40)
    liquidity = min(100, int(vol_score + data_score))

    return {
        "avg_price": round(avg_price, 2),
        "price_trend": trend,
        "avg_daily_volume": round(avg_daily_vol, 2),
        "liquidity_score": liquidity,
        "data_points": len(relevant),
    }


def _compute_moving_average(volume_records: list, item_name: str, enchant: str, window: int = 5) -> float:
    """Compute simple moving average of recent prices for item+enchant."""
    prices = [
        sfloat(r.get("price", 0))
        for r in reversed(volume_records)
        if r.get("item") == item_name and r.get("enchant") == enchant and sfloat(r.get("price", 0)) > 0
    ]
    if not prices:
        return 0.0
    recent = prices[:window]
    return round(sum(recent) / len(recent), 2)


def _calc_candidate_profit_synced(
    candidate: dict,
    cfg: dict,
    db: dict,
    prices: dict,
    volume_records: list,
) -> dict:
    """Headless wrapper around execute_calculation — extracts financial totals
    (total_capital, grand_profit) to guarantee 0% variance with the Dashboard."""
    item_name = candidate.get("item", "")
    e = candidate.get("enchant", ".0")

    # 1. Isolate config for a single unit run
    test_cfg = copy.deepcopy(cfg)
    test_cfg["selected_items"] = {item_name: {e: True}}
    test_cfg["do_craft"] = True
    test_cfg["use_refine_only"] = False
    test_cfg["q0"] = 1 if e == ".0" else 0
    test_cfg["q1"] = 1 if e == ".1" else 0
    test_cfg["q2"] = 1 if e == ".2" else 0
    test_cfg["q3"] = 1 if e == ".3" else 0
    test_cfg["q4"] = 1 if e == ".4" else 0
    test_cfg["adjusted_qty_crafts"] = {}
    test_cfg["cancelled_crafts"] = {}

    # 2. Run the main engine
    try:
        res = execute_calculation(test_cfg, db, prices)
    except Exception as exc:
        logger.error("execute_calculation failed for candidate '%s': %s", item_name, exc)
        return {
            **candidate,
            "est_profit": 0, "est_cost": 0, "est_pct": 0,
            "trend": _compute_volume_trend(volume_records, item_name, e),
            "sma_price": _compute_moving_average(volume_records, item_name, e),
            "source": "headless_calculator_error",
        }

    # 3. Extract exact UI totals (total_capital is usually negative in calculator)
    total_cost = abs(sfloat(res.get("financial", {}).get("total_capital", 0)))
    grand_profit = sfloat(res.get("financial", {}).get("grand_profit", 0))

    trend = _compute_volume_trend(volume_records, item_name, e)
    sma_price = _compute_moving_average(volume_records, item_name, e)

    return {
        **candidate,
        "est_profit": grand_profit,
        "est_cost": total_cost,
        "est_pct": (grand_profit / total_cost * 100) if total_cost > 0 else 0,
        "trend": trend,
        "sma_price": sma_price,
        "source": "headless_calculator"
    }


def _local_fallback_analyze(
    budget: float,
    candidates: list,
    mode: str,
    cfg: dict,
    db: dict,
    prices: dict,
    volume_records: list,
) -> dict:
    """Deep local fallback: uses real calculator math + volume trends to
    build a portfolio selection that mirrors what the LLM would produce.

    This function NEVER calls the Gemini API. It is the offline brain.
    """
    # Enrich every candidate with real profit calculations
    enriched = []
    for c in candidates:
        try:
            enriched_c = _calc_candidate_profit_synced(
                c, cfg, db, prices, volume_records,
            )
            enriched.append(enriched_c)
        except Exception as exc:
            logger.warning("Local fallback: error enriching candidate '%s': %s", c.get("item", "?"), exc)
            enriched.append({
                **c, "est_profit": 0, "est_cost": 0, "est_pct": 0,
                "trend": {}, "sma_price": 0, "source": "local_fallback_error",
            })

    # Filter out items with non-positive profit or missing data
    profitable = [c for c in enriched if c.get("est_profit", 0) > 0 and c.get("est_cost", 0) > 0]

    # Sort by a composite score:
    # 70% weight on profit percentage, 30% weight on liquidity score
    for c in profitable:
        liq = c.get("trend", {}).get("liquidity_score", 0)
        pct = c.get("est_pct", 0)
        c["_score"] = (pct * 0.7) + (liq * 0.3)

    profitable.sort(key=lambda x: x.get("_score", 0), reverse=True)

    # Greedy knapsack: pick items within budget
    picks = []
    adjusted_qty = {}
    remaining_budget = budget
    total_expected_profit = 0.0
    reasoning_parts = []

    for c in profitable:
        item = c.get("item", "")
        enchant = c.get("enchant", ".0")
        unit_cost = c.get("est_cost", 0)
        if unit_cost <= 0:
            continue

        # Determine quantity: use activeDailyVol as demand signal
        daily_vol = c.get("activeDailyVol", 0)
        trend_info = c.get("trend", {})
        trend_dir = trend_info.get("price_trend", "unknown")

        # Base qty from daily volume (craft 20-40% of daily volume)
        vol_fraction = 0.3 if trend_dir == "rising" else (0.15 if trend_dir == "falling" else 0.2)
        base_qty = max(1, int(sfloat(daily_vol) * vol_fraction))

        # How many can we afford?
        affordable = max(1, int(remaining_budget / unit_cost))
        qty = min(base_qty, affordable)

        if qty <= 0:
            continue

        total_item_cost = unit_cost * qty
        if total_item_cost > remaining_budget:
            qty = max(1, int(remaining_budget / unit_cost))
            total_item_cost = unit_cost * qty

        if total_item_cost > remaining_budget:
            continue

        if item not in [p for p in picks]:
            picks.append(item)
        if item not in adjusted_qty:
            adjusted_qty[item] = {}
        adjusted_qty[item][enchant] = qty
        remaining_budget -= total_item_cost

        unit_profit = c.get("est_profit", 0)
        total_expected_profit += unit_profit * qty
        liq_score = trend_info.get("liquidity_score", 0)
        reasoning_parts.append(
            f"{item} {enchant}: {qty}x @ {int(unit_cost)}/ea, "
            f"est.profit {int(unit_profit * qty)}, "
            f"trend={trend_dir}, liquidity={liq_score}/100"
        )

        if remaining_budget < 1000:
            break

    # Deduplicate picks
    picks = list(dict.fromkeys(picks))

    total_invested = budget - remaining_budget
    reasoning = (
        f"[LOCAL ANALYZER] Budget: {int(budget):,} | Invested: {int(total_invested):,} | "
        f"Remaining: {int(remaining_budget):,}\n"
        f"Selected {len(picks)} items based on synchronized calculator profit, "
        f"volume trends, and liquidity scoring.\n"
        + "\n".join(reasoning_parts[:20])
    )

    return {
        "picks": picks,
        "adjusted_qty": adjusted_qty,
        "reasoning": reasoning,
        "source": "local_calculator",
        "enriched_candidates": enriched[:50],  # Return top 50 for UI detail
        "total_cost": total_invested,
        "total_profit": total_expected_profit,
    }


# ---------------------------------------------------------------------------
# 4. PUBLIC API FUNCTIONS — Called by routes/api.py
# ---------------------------------------------------------------------------

def analyze_portfolio(
    api_key: str,
    budget: float,
    candidates: list,
    mode: str,
    cfg: dict | None = None,
    db: dict | None = None,
    prices: dict | None = None,
    volume_records: list | None = None,
) -> dict:
    """Analyze portfolio with Gemini API, falling back to local calculator.

    When cfg/db/prices/volume_records are provided (from MemoryState snapshot),
    the local fallback will use them for real profit calculations.
    """
    budget = sfloat(budget)

    # Check if we should go straight to local mode
    mgr = get_key_manager()
    force_local = not api_key or not api_key.strip()

    if not force_local:
        mgr.configure(api_key)
        force_local = mgr.all_on_cooldown()

    # If we have state data, always prepare a local fallback
    has_state_data = all(x is not None for x in [cfg, db, prices])
    vol = volume_records if volume_records is not None else []

    if has_state_data:
        local_result = _local_fallback_analyze(
            budget, candidates, mode, cfg, db, prices, vol,
        )
    else:
        # Legacy fallback (no state data available)
        local_result = _build_legacy_fallback(budget, candidates)

    if force_local:
        logger.info("All keys on cooldown or no key configured. Using local analyzer.")
        return local_result

    # Attempt Gemini API call
    prompt = _build_portfolio_prompt(budget, candidates, mode)

    try:
        result = call_gemini_api(api_key, prompt, fallback_data=local_result)
        return result
    except Exception as e:
        logger.error("analyze_portfolio: Gemini call failed entirely: %s", e)
        return local_result


def auto_recover_error(
    api_key: str,
    error_traceback: str,
    state_context: dict,
) -> dict:
    """AI-assisted error recovery. Falls back to safe static response on failure."""
    prompt = f"""
    You are an AI Auto-Recovery Assistant.
    An internal server error occurred.

    Error Traceback:
    {error_traceback}

    State Context:
    {orjson.dumps(state_context, option=orjson.OPT_INDENT_2).decode('utf-8')}

    Diagnose the issue quickly and provide a safe fallback JSON response so the client app doesn't crash.
    Return ONLY a valid JSON object matching exactly this schema:
    {{
      "picks": [],
      "adjusted_qty": {{}},
      "reasoning": "Explain the error and the fallback."
    }}
    """
    fallback = {
        "picks": [],
        "adjusted_qty": {},
        "reasoning": "Critical error recovery activated. System returned safe defaults.",
    }
    return call_gemini_api(api_key, prompt, fallback_data=fallback)


# ---------------------------------------------------------------------------
# 5. INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _build_portfolio_prompt(budget: float, candidates: list, mode: str) -> str:
    """Build the Gemini prompt for portfolio analysis."""
    # Limit candidates to avoid token overflow
    capped = candidates[:100]
    candidates_json = orjson.dumps(capped, option=orjson.OPT_INDENT_2).decode("utf-8")

    return f"""
    You are an Albion Online economy analyzer.
    Budget: {budget}
    Mode: {mode}

    CRITICAL INSTRUCTIONS:
    1. STRICTLY use ONLY the provided local data candidates below. DO NOT use external knowledge, imagination, or hallucinate items/prices.
    2. Select a combination of items that maximizes profit while staying within the {budget} budget.
    3. The total cost of selected items MUST NOT exceed the budget.
    4. To calculate cost for an item: cost = candidate.cost * quantity * candidate.y_yield.
    5. Output MUST be valid JSON.

    Local Data Candidates:
    {candidates_json}

    Return ONLY a valid JSON object matching exactly this schema:
    {{
      "picks": ["item_name_1", "item_name_2"],
      "adjusted_qty": {{
        "item_name_1": {{ ".0": 1, ".1": 0 }},
        "item_name_2": {{ ".1": 5 }}
      }},
      "reasoning": "Explain briefly why you chose this based ON LOCAL DATA."
    }}
    """


def _build_legacy_fallback(budget: float, candidates: list) -> dict:
    """Legacy fallback when no state data is available. Simple budget-greedy."""
    fallback = {
        "picks": [],
        "adjusted_qty": {},
        "reasoning": "Legacy fallback active (no state data). Basic budget-greedy selection.",
        "source": "legacy_fallback",
    }
    current_budget = budget
    for c in candidates:
        qty = max(1, int(sfloat(c.get("activeDailyVol", 1)) * 0.2))
        cost = sfloat(c.get("cost", 0)) * qty * sfloat(c.get("y_yield", 1))
        if cost <= 0:
            continue
        if current_budget >= cost:
            item = c.get("item", "")
            fallback["picks"].append(item)
            if item not in fallback["adjusted_qty"]:
                fallback["adjusted_qty"][item] = {}
            fallback["adjusted_qty"][item][c.get("enchant", ".0")] = qty
            current_budget -= cost

    fallback["picks"] = list(dict.fromkeys(fallback["picks"]))
    return fallback
