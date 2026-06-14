# 📜 Lore Weaver

> Where every story remembers its world — AI-crafted tales grounded in living lore.

Lore Weaver is an AI-powered creative storytelling app built for the **Agents League Hackathon (Creative Apps track)**. It generates personalized, original short stories that stay consistent with a custom world-lore knowledge base, using **Microsoft Foundry IQ** for grounded, cited knowledge retrieval.

## ✨ What it does

1. You enter a **character name**, **setting**, and **theme**.
2. The app retrieves relevant lore facts (character backstories, world descriptions, thematic notes) from a knowledge base via **Foundry IQ's agentic retrieval**.
3. An AI model weaves those grounded facts into an original short story.
4. The story, the grounded facts used, and the retrieval source are displayed.

This ensures every generated story feels like part of a coherent, living world — not a generic, disconnected tale.

## 🧠 Microsoft IQ Integration — Foundry IQ

Foundry IQ powers the knowledge retrieval layer of this app:

- A custom **world lore knowledge base** (character backstories, settings, themes) is connected to a Foundry Agent.
- When a user submits a prompt, the app queries the Foundry Agent for grounded facts relevant to the character/setting/theme.
- These cited facts are passed into the story-generation prompt, reducing hallucination and keeping the narrative consistent with established lore.

If Foundry IQ credentials are not configured, the app gracefully falls back to a local JSON lore knowledge base (`lore_docs/world_lore.json`) so the demo always works.

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
├── app.py                  # Flask backend + Foundry IQ integration
├── requirements.txt
├── lore_docs/
│   └── world_lore.json     # Local fallback lore knowledge base
├── templates/
│   └── index.html          # Frontend UI
└── README.md
```

## 🎯 Why It's Creative

Lore Weaver turns story generation into **world-building**. Instead of producing isolated, generic stories, it grounds each tale in a shared knowledge base — so characters have consistent histories, settings have consistent rules, and themes connect to deeper lore. The result feels like reading a chapter from a much larger, living world.

## ⚠️ Disclaimer

No confidential information, API keys, or proprietary data are included in this repository. All lore content is original and fictional, created for demonstration purposes.
