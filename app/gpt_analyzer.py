from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a professional volleyball coach with NCAA Division I experience. 
Your job is to provide precise, actionable feedback for each detected play event.

Guidelines:
- Tone: concise, professional, and specific (like feedback given in film review).
- Use volleyball terminology correctly (e.g., OH, MB, libero, transition footwork).
- Always output 2–4 bullet points only, never paragraphs.

Format for every event:
• Observation — factual description of what happened
• Improvement — 1–2 technical or tactical adjustments
• Drill — one named drill that directly addresses the improvement

Rules:
- Do not hedge or say “I need more details.”
- Do not give generic advice (avoid “work hard,” “communicate more” without specifics).
- Always leverage the provided player role, jersey number, and focus notes if available.
- Keep language crisp; this should read like a coach’s scouting/practice notes.
"""


def analyze_play(play_description: str, extra_context: str = "") -> str:
    if not OPENAI_API_KEY:
        return "[Setup] Add OPENAI_API_KEY in .env to enable analysis."

    user_prompt = (
        f"Analyze this detected moment from a volleyball clip:\n"
        f"- Event: {play_description}\n"
    )
    if extra_context:
        user_prompt += f"- Player/context: {extra_context}\n"

    user_prompt += (
        "\nReturn:\n"
        "• Brief observation\n"
        "• 1–2 actionable improvements (mechanics, decision, or positioning)\n"
        "• Optional drill suggestion\n"
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=250,
            temperature=0.6,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"[OpenAI API error] {e}"


def suggest_lineup(players: list, simple_lineup: dict) -> str:
    """
    Use GPT to critique/improve the heuristic lineup and note rotations/subs.
    """
    if not OPENAI_API_KEY:
        return "[Setup] Add OPENAI_API_KEY in .env to enable lineup suggestions."
    # Keep it compact; send summarized stats only
    def summarize(p):
        return {
            "name": p.get("name"), "jersey": p.get("jersey"), "role": p.get("role"),
            "atk": p.get("attack_pct", 0), "blk": p.get("block_eff", 0),
            "dig": p.get("dig_pct", 0), "srv": p.get("serve_pct", 0), "pass": p.get("pass_rating", 0),
            "notes": p.get("notes", "")
        }

    payload = {
        "players": [summarize(p) for p in players],
        "lineup": simple_lineup.get("lineup", {})
    }

    prompt = (
        "You are a volleyball coach. Given the roster and a proposed starting lineup, "
        "review it for balance (serve-receive, block height, out-of-system options, back-row defense). "
        "Suggest rotation notes and one substitution plan. Keep it concise (bullets)."
        f"\n\nData:\n{payload}"
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"Be specific, compact, and practical."},
                  {"role":"user","content":prompt}],
        max_tokens=350, temperature=0.6
    )
    return resp.choices[0].message.content.strip()

def build_practice_schedule(players: list, struggle_counts: dict, *, days: str, start_time: str, duration_min: int, location: str = "") -> str:
    """
    Generate a 1-week practice plan using the team struggles and user-provided schedule.
    Not auto-called; the route will call this only when the user clicks the button.
    """
    if not OPENAI_API_KEY:
        return "[Setup] Add OPENAI_API_KEY in .env to enable practice planning."

    schedule_note = (
        f"Constraints:\n"
        f"- Days: {days}\n"
        f"- Start time: {start_time}\n"
        f"- Duration: {duration_min} minutes\n"
        f"- Location: {location or 'N/A'}\n"
    )

    prompt = (
        "Create a 1-week volleyball practice plan (one session per listed day) using the constraints below. "
        "Each session should be ~the given duration with drill names, time blocks, groupings, and measurable goals. "
        "Emphasize the most common struggles. Keep it concise and scannable (bullets, times).\n\n"
        f"{schedule_note}\n"
        f"Struggles tally: {struggle_counts}\n"
        f"Roster (names/roles): {[{'name':p.get('name'), 'role':p.get('role')} for p in players]}"
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"Return a structured plan with headings per day and time-block bullets."},
            {"role":"user","content":prompt}
        ],
        max_tokens=700,
        temperature=0.6
    )
    return (resp.choices[0].message.content or "").strip()


