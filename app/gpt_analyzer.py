from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "You are an expert volleyball coach. Be concise, actionable, and specific. "
    "For each event, provide 2–4 bullet points: what happened, 1–2 concrete adjustments, "
    "and a drill suggestion if relevant. Avoid generic filler."
)

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
