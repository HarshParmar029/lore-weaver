import os
import json
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# === Foundry IQ / Azure AI Foundry Configuration ===
# Set these as environment variables (do NOT hardcode in production)
FOUNDRY_ENDPOINT = os.environ.get("FOUNDRY_ENDPOINT", "")  # e.g. https://<your-resource>.services.ai.azure.com
FOUNDRY_API_KEY = os.environ.get("FOUNDRY_API_KEY", "")
FOUNDRY_AGENT_ID = os.environ.get("FOUNDRY_AGENT_ID", "")  # your agent/assistant id

# === Local fallback lore database (used if Foundry isn't configured) ===
LORE_FILE = os.path.join(os.path.dirname(__file__), "lore_docs", "world_lore.json")


def load_local_lore():
    if os.path.exists(LORE_FILE):
        with open(LORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def retrieve_lore_facts(character_name, setting, theme):
    """
    Retrieve grounded facts about the character/world.
    If Foundry IQ is configured, query it. Otherwise fall back to local JSON lore.
    Returns: (facts_text, source_label)
    """
    if FOUNDRY_ENDPOINT and FOUNDRY_API_KEY and FOUNDRY_AGENT_ID:
        try:
            return query_foundry_iq(character_name, setting, theme)
        except Exception as e:
            print(f"Foundry IQ query failed, falling back to local lore: {e}")

    # --- Local fallback ---
    lore = load_local_lore()
    facts = []
    char = lore.get("characters", {}).get(character_name.lower())
    if char:
        facts.append(f"{character_name}: {char.get('backstory', '')}")
    world = lore.get("settings", {}).get(setting.lower())
    if world:
        facts.append(f"Setting '{setting}': {world.get('description', '')}")
    theme_info = lore.get("themes", {}).get(theme.lower())
    if theme_info:
        facts.append(f"Theme '{theme}': {theme_info.get('notes', '')}")

    if not facts:
        facts.append("No specific lore found — generating a fresh tale with general fantasy conventions.")

    return "\n".join(facts), "Local Lore Knowledge Base"


def query_foundry_iq(character_name, setting, theme):
    """
    Query an Azure AI Foundry Agent (Foundry IQ) for grounded knowledge retrieval.
    Returns (facts_text, source_label)
    """
    url = f"{FOUNDRY_ENDPOINT}/agents/{FOUNDRY_AGENT_ID}/runs"
    headers = {
        "Authorization": f"Bearer {FOUNDRY_API_KEY}",
        "Content-Type": "application/json",
    }
    query = (
        f"Retrieve any known lore, backstory, or world facts about a character named "
        f"'{character_name}' in a setting called '{setting}', related to the theme '{theme}'. "
        f"Return concise grounded facts with citations."
    )
    payload = {"input": query}

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Extract text response (structure depends on Foundry Agent API version)
    facts_text = data.get("output", data.get("response", str(data)))
    return facts_text, "Foundry IQ (Grounded Retrieval)"


def generate_story(character_name, setting, theme, grounded_facts):
    """
    Generate the story text. Uses Anthropic Claude API if ANTHROPIC available,
    otherwise produces a templated story using the grounded facts.
    """
    prompt = (
        f"Write a short, vivid creative story (around 250-350 words). "
        f"Main character: {character_name}. Setting: {setting}. Theme: {theme}.\n\n"
        f"Incorporate these grounded world facts naturally into the story:\n{grounded_facts}\n\n"
        f"Make the story engaging, original, and consistent with the facts above."
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 800,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
            if text_blocks:
                return "\n".join(text_blocks)
        except Exception as e:
            print(f"LLM generation failed, using template fallback: {e}")

    # --- Template fallback (so the app always works, even without API keys) ---
    return (
        f"In the realm of {setting}, {character_name} stood at the edge of an old path, "
        f"the weight of {theme} pressing close.\n\n"
        f"Grounded in the lore: {grounded_facts}\n\n"
        f"As {character_name} moved forward, the world itself seemed to remember their story — "
        f"echoes of the past shaping the choices ahead. Every step was both new and familiar, "
        f"a tale woven from threads that had always been there, waiting to be told.\n\n"
        f"And so the story of {character_name} continued, one chapter in a much larger, "
        f"living world."
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(force=True)
    character_name = data.get("character", "").strip() or "Aria"
    setting = data.get("setting", "").strip() or "the Whispering Vale"
    theme = data.get("theme", "").strip() or "discovery"

    facts, source = retrieve_lore_facts(character_name, setting, theme)
    story = generate_story(character_name, setting, theme, facts)

    return jsonify({
        "story": story,
        "grounded_facts": facts,
        "source": source,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
