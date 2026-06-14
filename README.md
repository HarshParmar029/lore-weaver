# 📜 Lore Weaver

> Where every story remembers its world — AI-crafted tales grounded in living lore.

Lore Weaver is an AI-powered creative storytelling app built for the **Agents League Hackathon (Creative Apps track)**. It generates personalized, original short stories that stay consistent with a custom world-lore knowledge base, using **Microsoft Foundry IQ** for grounded, cited knowledge retrieval.

## ✨ What it does

1. You enter a **character name**, **setting**, and **theme**.
2. The app runs a **multi-step agentic pipeline**:
   - **Retrieve** — pulls grounded facts about the character, setting, and theme from the knowledge base via **Foundry IQ's agentic retrieval**.
   - **Cross-reference** — traverses the knowledge graph to find related factions, historical events, and relationships connected to the character/setting.
   - **Recall** — checks **world memory** (a log of every story ever generated) for past tales connected to this character or setting.
   - **Synthesize & Generate** — weaves all of this into an original short story, with inline **numbered citations `[1] [2]`** back to the exact facts used.
3. The story, the full **agent reasoning trace**, the **cited facts**, and any **memory connections** to past tales are all displayed.
4. The new story is saved into world memory — so the *next* tale can reference it too.

This ensures every generated story feels like part of a coherent, living world that **remembers what came before** — not a generic, disconnected tale.

## 🧠 Microsoft IQ Integration — Foundry IQ

Foundry IQ powers the knowledge retrieval layer of this app:

- A custom **world lore knowledge graph** (characters, settings, themes, factions, historical events, and relationships) is connected to a Foundry Agent.
- When a user submits a prompt, the app queries the Foundry Agent for grounded, cited facts relevant to the character/setting/theme.
- These cited facts are passed into the story-generation prompt with numbered citation markers, reducing hallucination and keeping the narrative consistent with established lore.

If Foundry IQ credentials are not configured, the app gracefully falls back to a **local agentic retrieval engine** that traverses the same knowledge graph structure (`lore_docs/world_lore.json`) — including faction lookups, historical event cross-referencing, and relationship discovery — so the demo always works and still demonstrates the full multi-step reasoning flow.

## 🪄 Advanced Features

- **Multi-step reasoning trace** — every generation shows the agent's step-by-step process: lookup character → lookup setting → lookup theme → cross-reference factions → cross-reference events → cross-reference relationships → check world memory → synthesize → generate.
- **Numbered citations** — the generated story includes `[1]`, `[2]`, etc. markers that map directly to the grounded facts panel, so you can verify exactly which lore informed which sentence.
- **World memory / continuity** — Lore Weaver remembers every story it has written (`lore_docs/story_log.json`). If you generate a new tale about a character or setting that appeared before, the agent surfaces that connection and the new story can acknowledge it — the world genuinely grows over time.
- **World Atlas tab** — explore the full interconnected knowledge graph (characters, settings, factions, historical events, relationships) that powers the retrieval.
- **Story Archive tab** — browse the full history of generated tales and how the world's memory has evolved.

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML / CSS / vanilla JS
- **Knowledge Retrieval:** Microsoft Foundry IQ (Azure AI Foundry Agent)
- **Story Generation:** LLM API (configurable)
- **Development:** GitHub Copilot

## 🤖 GitHub Copilot Usage

GitHub Copilot Chat was used extensively during development to:
- Scaffold the Flask app structure and routes
- Debug the Foundry IQ API integration
- Refine and iterate on story-generation prompt templates
- Write and clean up the frontend UI code

## 🚀 Running Locally

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Set environment variables for Foundry IQ and your LLM provider:
   ```bash
   set FOUNDRY_ENDPOINT=your-foundry-endpoint
   set FOUNDRY_API_KEY=your-foundry-key
   set FOUNDRY_AGENT_ID=your-agent-id
   set ANTHROPIC_API_KEY=your-llm-api-key
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Open `http://localhost:5000` in your browser.

> If no API keys are set, the app runs fully offline using a local lore knowledge base and a templated story generator — perfect for demos.

## 📂 Project Structure

```
lore-weaver/
├── app.py                  # Flask backend + multi-step agentic pipeline + Foundry IQ integration
├── requirements.txt
├── lore_docs/
│   ├── world_lore.json     # Knowledge graph: characters, settings, themes, factions, events, relationships
│   └── story_log.json      # World memory — log of every generated story
├── templates/
│   └── index.html          # Frontend UI (Weave a Tale / World Atlas / Story Archive)
└── README.md
```

## 🎯 Why It's Creative

Lore Weaver turns story generation into **world-building backed by a reasoning agent**. Instead of a single prompt-to-story call, it runs a visible multi-step pipeline — retrieve, cross-reference, recall memory, synthesize, generate, cite — so every tale is grounded in a shared, interconnected knowledge graph and in the world's own history of stories. Characters have consistent histories, settings have consistent rules, themes connect to deeper lore, and each new story can reference the ones that came before it. The result feels like reading a new chapter from a much larger, living world — one that remembers what you wrote into it.

## ⚠️ Disclaimer

No confidential information, API keys, or proprietary data are included in this repository. All lore content is original and fictional, created for demonstration purposes.
