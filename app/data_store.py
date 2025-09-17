import json, os
from typing import List, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PLAYERS_PATH = os.path.join(DATA_DIR, "players.json")

def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PLAYERS_PATH):
        with open(PLAYERS_PATH, "w") as f:
            json.dump([], f)

def load_players() -> List[Dict[str, Any]]:
    _ensure_files()
    with open(PLAYERS_PATH, "r") as f:
        return json.load(f)

def save_players(players: List[Dict[str, Any]]) -> None:
    with open(PLAYERS_PATH, "w") as f:
        json.dump(players, f, indent=2)

def upsert_player(p: Dict[str, Any]) -> None:
    players = load_players()
    # upsert by jersey OR name
    key = (str(p.get("jersey","")).strip(), p.get("name","").strip().lower())
    found = False
    for i, row in enumerate(players):
        if (str(row.get("jersey","")).strip(), row.get("name","").strip().lower()) == key:
            players[i] = p
            found = True
            break
    if not found:
        players.append(p)
    save_players(players)

def compute_lineup_simple(players: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Stats-driven heuristic lineup (no LLM):
    - Normalizes stats per metric across roster (min-max).
    - Uses role-specific weights to compute a composite score.
    - Picks 2xOH, 2xMB, 1xS, 1xOPP, and 1xL (L listed separately).
    - Gracefully falls back to next-best players if a role is undersupplied.
    """

    if not players:
        return {"lineup": {"OH": [], "MB": [], "S": [], "OPP": [], "L": [], "bench": []}}

    # 1) Collect raw metrics with safe defaults
    metrics = ["attack_pct", "block_eff", "dig_pct", "serve_pct", "pass_rating"]
    raw = []
    for p in players:
        row = {m: float(p.get(m, 0) or 0) for m in metrics}
        row.update({
            "name": p.get("name", ""),
            "jersey": p.get("jersey", ""),
            "role": (p.get("role") or "").upper() or "OH",  # default OH
            "notes": p.get("notes", "")
        })
        raw.append(row)

    # 2) Min-max normalize each metric to [0,1] across roster
    mins = {m: min(r[m] for r in raw) for m in metrics}
    maxs = {m: max(r[m] for r in raw) for m in metrics}
    def norm(m, v):
        lo, hi = mins[m], maxs[m]
        return 0.0 if hi == lo else (v - lo) / (hi - lo)

    for r in raw:
        for m in metrics:
            r[f"n_{m}"] = norm(m, r[m])

    # 3) Role-specific weights (sum ~= 1.0). Adjust freely.
    WEIGHTS = {
        "OH":  {"attack":0.38, "pass":0.24, "dig":0.14, "block":0.12, "serve":0.12},
        "OPP": {"attack":0.45, "block":0.22, "serve":0.12, "dig":0.11, "pass":0.10},
        "MB":  {"block":0.42, "attack":0.32, "serve":0.10, "dig":0.08, "pass":0.08},
        "S":   {"serve":0.20, "dig":0.22, "pass":0.22, "attack":0.18, "block":0.18},  # lacking assist metric, proxy with all-around
        "L":   {"pass":0.48, "dig":0.40, "serve":0.07, "attack":0.03, "block":0.02},
        "DS":  {"pass":0.45, "dig":0.43, "serve":0.08, "attack":0.02, "block":0.02},
    }

    def composite(r, role):
        w = WEIGHTS.get(role, WEIGHTS["OH"])
        return (
            w["attack"] * r["n_attack_pct"] +
            w["block"]  * r["n_block_eff"] +
            w["dig"]    * r["n_dig_pct"] +
            w["serve"]  * r["n_serve_pct"] +
            w["pass"]   * r["n_pass_rating"]
        )

    # 4) Score each player for their own role AND for general value (for fallback/bench)
    for r in raw:
        r["score_role"] = composite(r, r["role"])
        r["score_general"] = composite(r, "OH") * 0.5 + composite(r, "DS") * 0.5  # general floor value

    # 5) Bucket by role and sort by role score
    by_role = {"OH": [], "MB": [], "S": [], "OPP": [], "L": [], "DS": []}
    for r in raw:
        by_role.setdefault(r["role"], []).append(r)
    for k in by_role:
        by_role[k].sort(key=lambda x: x["score_role"], reverse=True)

    # 6) Pick slots with graceful fallback
    def pop_best(role):
        if by_role.get(role):
            return by_role[role].pop(0)
        # fallback: take best remaining across all by role score, then by general
        pool = [x for lst in by_role.values() for x in lst]
        if not pool: return None
        pool.sort(key=lambda x: (x["score_role"], x["score_general"]), reverse=True)
        picked = pool[0]
        # remove picked from its bucket
        for k in by_role:
            if picked in by_role[k]:
                by_role[k].remove(picked)
                break
        return picked

    lineup = {
        "OH":  [p for p in [pop_best("OH"), pop_best("OH")] if p],
        "MB":  [p for p in [pop_best("MB"), pop_best("MB")] if p],
        "S":   [p for p in [pop_best("S")] if p],
        "OPP": [p for p in [pop_best("OPP")] if p],
        "L":   [p for p in [pop_best("L")] if p],
    }

    # 7) Bench = remaining, sorted by general value
    remaining = [x for lst in by_role.values() for x in lst]
    remaining.sort(key=lambda x: (x["score_general"], x["score_role"]), reverse=True)

    # 8) Convert to the original shape you render
    def slim(p):
        return {
            "name": p["name"], "jersey": p["jersey"], "role": p["role"],
        }
    lineup_out = {
        "OH":  [slim(p) for p in lineup["OH"]],
        "MB":  [slim(p) for p in lineup["MB"]],
        "S":   [slim(p) for p in lineup["S"]],
        "OPP": [slim(p) for p in lineup["OPP"]],
        "L":   [slim(p) for p in lineup["L"]],
        "bench": [slim(p) for p in remaining[:6]]
    }
    return {"lineup": lineup_out}


def collect_struggles(players: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate 'struggles' free text (comma-separated tags).
    """
    from collections import Counter
    c = Counter()
    for p in players:
        tags = (p.get("struggles") or "").strip()
        if not tags:
            continue
        for t in [x.strip().lower() for x in tags.split(",") if x.strip()]:
            c[t] += 1
    return dict(c)

# --- Practice data (settings + last plan) ---
PRACTICE_PATH = os.path.join(DATA_DIR, "practice.json")

def _ensure_practice():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PRACTICE_PATH):
        with open(PRACTICE_PATH, "w") as f:
            json.dump({
                "days": "Mon, Wed, Fri",
                "start_time": "18:00",
                "duration_min": 90,
                "location": "",
                "last_plan": ""  # store latest generated text
            }, f)

def load_practice() -> Dict[str, Any]:
    _ensure_practice()
    with open(PRACTICE_PATH, "r") as f:
        return json.load(f)

def save_practice(settings: Dict[str, Any]) -> None:
    _ensure_practice()
    # merge into current file (preserve last_plan unless provided)
    current = load_practice()
    current.update(settings)
    with open(PRACTICE_PATH, "w") as f:
        json.dump(current, f, indent=2)

def save_practice_plan(plan_text: str) -> None:
    save_practice({"last_plan": plan_text})
