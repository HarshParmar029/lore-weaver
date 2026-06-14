import os
import json
import time
import re
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# === Foundry IQ / Azure AI Foundry Configuration ===
# Set these as environment variables (do NOT hardcode in production)
FOUNDRY_ENDPOINT = os.environ.get("FOUNDRY_ENDPOINT", "")  # e.g. https://<your-resource>.services.ai.azure.com
FOUNDRY_API_KEY = os.environ.get("FOUNDRY_API_KEY", "")
FOUNDRY_AGENT_ID = os.environ.get("FOUNDRY_AGENT_ID", "")  # your agent/assistant id

# === Local knowledge base + world memory (used if Foundry isn't configured) ===
LORE_FILE = os.path.join(os.path.dirname(__file__), "lore_docs", "world_lore.json")
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "lore_docs", "story_log.json")


# ---------------------------------------------------------------------------
# Knowledge base + world-memory loading
# ---------------------------------------------------------------------------

def load_local_lore():
    if os.path.exists(LORE_FILE):
        with open(LORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_memory():
    """World memory: a running log of every story Lore Weaver has generated."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_memory(entries):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Could not persist world memory: {e}")


# ---------------------------------------------------------------------------
# STEP 1 — Grounded retrieval (Foundry IQ, with local agentic fallback)
# ---------------------------------------------------------------------------

def retrieve_lore_facts(character_name, setting, theme, lore):
    """
    Retrieve grounded facts about the character/world.
    If Foundry IQ is configured, query it. Otherwise run a local agentic
    retrieval pass over the lore knowledge graph (characters, settings,
    themes, factions, events, relationships).

    Returns: (facts list[dict{id, text, category}], source_label, trace[str])
    """
    trace = []

    if FOUNDRY_ENDPOINT and FOUNDRY_API_KEY and FOUNDRY_AGENT_ID:
        try:
            facts, source = query_foundry_iq(character_name, setting, theme)
            trace.append("Queried Foundry IQ agent for grounded, cited facts about the requested character/setting/theme.")
            return facts, source, trace
        except Exception as e:
            trace.append(f"Foundry IQ query failed ({e}); falling back to local agentic retrieval.")

    # --- Local agentic retrieval over the knowledge graph ---
    facts = []
    cid = character_name.lower().strip()
    sid = setting.lower().strip()
    tid = theme.lower().strip()

    trace.append(f"Looked up character '{character_name}' in the world knowledge base.")
    char = lore.get("characters", {}).get(cid)
    if char:
        facts.append({
            "category": "character",
            "text": f"{character_name} ({char.get('title', '')}): {char.get('backstory', '')}",
        })

    trace.append(f"Looked up setting '{setting}' in the world knowledge base.")
    world = lore.get("settings", {}).get(sid)
    if world:
        facts.append({
            "category": "setting",
            "text": f"{setting} ({world.get('title', '')}): {world.get('description', '')}",
        })

    trace.append(f"Looked up theme '{theme}' for tone and narrative conventions.")
    theme_info = lore.get("themes", {}).get(tid)
    if theme_info:
        facts.append({
            "category": "theme",
            "text": f"Theme '{theme}': {theme_info.get('notes', '')}",
        })

    # Cross-reference: factions linked to this character
    if char and char.get("factions"):
        trace.append("Cross-referenced character's faction memberships.")
        for fac_id in char["factions"]:
            fac = lore.get("factions", {}).get(fac_id)
            if fac:
                facts.append({
                    "category": "faction",
                    "text": f"{character_name} is affiliated with {fac['name']}: {fac['description']}",
                })

    # Cross-reference: historical events linked to this setting or character
    trace.append("Cross-referenced historical events tied to this setting and character.")
    for event in lore.get("events", []):
        linked_settings = [s.lower() for s in event.get("linked_settings", [])]
        linked_chars = [c.lower() for c in event.get("linked_characters", [])]
        if sid in linked_settings or cid in linked_chars:
            facts.append({
                "category": "event",
                "text": f"Historical event — {event['name']}: {event['summary']}",
            })

    # Cross-reference: relationships involving this character
    trace.append("Cross-referenced known relationships involving this character.")
    for rel in lore.get("relationships", []):
        if cid in (rel.get("a", "").lower(), rel.get("b", "").lower()):
            facts.append({
                "category": "relationship",
                "text": f"Relationship — {rel['description']}",
            })

    if not facts:
        trace.append("No direct matches found — proceeding with general fantasy conventions for this theme.")
        facts.append({
            "category": "general",
            "text": "No specific lore found — generating a fresh tale with general fantasy conventions.",
        })

    # Assign stable citation ids
    for i, fact in enumerate(facts, start=1):
        fact["id"] = i

    return facts, "Local Agentic Knowledge Graph", trace


def query_foundry_iq(character_name, setting, theme):
    """
    Query an Azure AI Foundry Agent (Foundry IQ) for grounded knowledge retrieval.
    Returns (facts list[dict{id, text, category}], source_label)
    """
    url = f"{FOUNDRY_ENDPOINT}/agents/{FOUNDRY_AGENT_ID}/runs"
    headers = {
        "Authorization": f"Bearer {FOUNDRY_API_KEY}",
        "Content-Type": "application/json",
    }
    query = (
        f"Retrieve any known lore, backstory, world facts, related events, factions, "
        f"and relationships for a character named '{character_name}' in a setting called "
        f"'{setting}', related to the theme '{theme}'. Return concise grounded facts with citations."
    )
    payload = {"input": query}

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    raw_text = data.get("output", data.get("response", str(data)))
    # Wrap Foundry's response as a single cited fact block
    facts = [{"id": 1, "category": "foundry", "text": raw_text}]
    return facts, "Foundry IQ (Grounded Retrieval)"


# ---------------------------------------------------------------------------
# STEP 2 — World memory: find connections to previously generated tales
# ---------------------------------------------------------------------------

def find_memory_connections(character_name, setting, theme, memory):
    """Search the world-memory log for past stories that share a character,
    setting, or theme — giving the world a sense of continuity."""
    cid = character_name.lower().strip()
    sid = setting.lower().strip()
    tid = theme.lower().strip()

    connections = []
    for entry in reversed(memory):  # most recent first
        if entry.get("character", "").lower() == cid or entry.get("setting", "").lower() == sid:
            connections.append(entry)
        if len(connections) >= 2:
            break

    return connections


# ---------------------------------------------------------------------------
# STEP 3 — Build the multi-step reasoning trace shown to the user
# ---------------------------------------------------------------------------

def build_reasoning_trace(character_name, setting, theme, facts, retrieval_trace, memory_hits, source):
    trace = list(retrieval_trace)

    trace.append(f"Retrieved {len(facts)} grounded fact(s) from: {source}.")

    if memory_hits:
        trace.append(
            f"Checked world memory and found {len(memory_hits)} previous tale(s) "
            f"connected to '{character_name}' or '{setting}' — the world will remember this."
        )
        for h in memory_hits:
            trace.append(
                f"  -> Previously: a '{h.get('theme')}' tale starring {h.get('character')} "
                f"in {h.get('setting')} (generated {h.get('timestamp')})."
            )
    else:
        trace.append("Checked world memory — no prior connected tales found. This will be a new thread in the world's history.")

    trace.append("Synthesizing retrieved facts, cross-references, and memory into a grounded story outline.")
    trace.append("Generating final narrative with inline citations back to the facts above.")

    return trace


# ---------------------------------------------------------------------------
# STEP 4 — Story generation (LLM if available, grounded template fallback)
# ---------------------------------------------------------------------------

def generate_story(character_name, setting, theme, facts, memory_hits):
    facts_block = "\n".join(f"[{f['id']}] {f['text']}" for f in facts)

    memory_block = ""
    if memory_hits:
        memory_lines = "\n".join(
            f"- A previous '{h.get('theme')}' tale featuring {h.get('character')} in {h.get('setting')}."
            for h in memory_hits
        )
        memory_block = (
            f"\n\nThis world has memory of prior tales. Where natural, let the new story "
            f"acknowledge or echo these past events (without contradicting them):\n{memory_lines}"
        )

    prompt = (
        f"Write a short, vivid creative story (around 250-350 words). "
        f"Main character: {character_name}. Setting: {setting}. Theme: {theme}.\n\n"
        f"Ground the story in these numbered world facts. When you use a fact, cite it "
        f"inline using its bracketed number, e.g. [1]:\n{facts_block}"
        f"{memory_block}\n\n"
        f"Make the story engaging, original, and consistent with the facts above. "
        f"Keep citation markers like [1], [2] inline in the prose where relevant."
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
                    "max_tokens": 900,
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
            print(f"LLM generation failed, using grounded template fallback: {e}")

    # --- Grounded template fallback (so the app always works, even without API keys) ---
    return build_template_story(character_name, setting, theme, facts, memory_hits)


def build_template_story(character_name, setting, theme, facts, memory_hits):
    """A richer, fact-citing template story used when no LLM API key is configured."""
    cite = lambda fid: f"[{fid}]"

    fact_by_cat = {}
    for f in facts:
        fact_by_cat.setdefault(f["category"], []).append(f)

    paragraphs = []

    opening = f"In {setting}, {character_name} arrived as the light turned to dusk, the weight of {theme} pressing close."
    if fact_by_cat.get("setting"):
        sf = fact_by_cat["setting"][0]
        opening += f" The place lived up to its reputation {cite(sf['id'])}."
    paragraphs.append(opening)

    if fact_by_cat.get("character"):
        cf = fact_by_cat["character"][0]
        paragraphs.append(
            f"{character_name} had not always walked alone {cite(cf['id'])}. "
            f"That history was never far from mind, especially now."
        )

    if fact_by_cat.get("event"):
        ef = fact_by_cat["event"][0]
        paragraphs.append(
            f"Old echoes of a different time still lingered here {cite(ef['id'])}. "
            f"{character_name} could feel the shape of that history pressing against the present."
        )

    if fact_by_cat.get("relationship"):
        rf = fact_by_cat["relationship"][0]
        paragraphs.append(
            f"And then there were the ties that bound this place to others {cite(rf['id'])}. "
            f"Nothing here existed in isolation."
        )

    if fact_by_cat.get("faction"):
        ff = fact_by_cat["faction"][0]
        paragraphs.append(f"Even allegiance was a kind of lore here {cite(ff['id'])}.")

    if memory_hits:
        h = memory_hits[0]
        paragraphs.append(
            f"This was not the first time the world had turned its attention here. "
            f"Once before, a tale of {h.get('theme')} had unfolded around {h.get('character')} "
            f"in {h.get('setting')} — and {character_name} could not shake the feeling that "
            f"this story was, in some quiet way, a continuation of that one."
        )

    paragraphs.append(
        f"As {character_name} moved forward, the world itself seemed to remember — "
        f"echoes of the past shaping the choices ahead. Every step was both new and familiar, "
        f"a tale woven from threads that had always been there, waiting to be told. "
        f"And so the story of {character_name} continued, one chapter in a much larger, living world."
    )

    return "\n\n".join(paragraphs)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(force=True)
    character_name = data.get("character", "").strip() or "Aria"
    setting = data.get("setting", "").strip() or "the Whispering Vale"
    theme = data.get("theme", "").strip() or "discovery"

    lore = load_local_lore()
    memory = load_memory()

    # Step 1: grounded retrieval
    facts, source, retrieval_trace = retrieve_lore_facts(character_name, setting, theme, lore)

    # Step 2: world-memory continuity check
    memory_hits = find_memory_connections(character_name, setting, theme, memory)

    # Step 3: build the visible multi-step reasoning trace
    reasoning_trace = build_reasoning_trace(character_name, setting, theme, facts, retrieval_trace, memory_hits, source)

    # Step 4: generate the cited story
    story = generate_story(character_name, setting, theme, facts, memory_hits)

    # Persist to world memory so future tales can reference this one
    entry = {
        "character": character_name,
        "setting": setting,
        "theme": theme,
        "summary": story[:240].rsplit(" ", 1)[0] + "...",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    memory.append(entry)
    memory = memory[-50:]  # keep the log bounded
    save_memory(memory)

    return jsonify({
        "story": story,
        "facts": facts,
        "source": source,
        "reasoning_trace": reasoning_trace,
        "memory_hits": memory_hits,
    })


@app.route("/api/lore")
def api_lore():
    """Expose the full knowledge graph for the World Atlas view."""
    return jsonify(load_local_lore())


@app.route("/api/history")
def api_history():
    """Expose the world-memory log for the Story Archive view."""
    memory = load_memory()
    return jsonify(list(reversed(memory)))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
