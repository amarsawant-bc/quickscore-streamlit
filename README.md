# QuickScore – Streamlit Prompt Reference

## Overview

This repository contains the **LOCKED** prompt reference implementation for the QuickScore feedback tool used by Avado PQ Limited.

This Streamlit app is the canonical source of truth for:

- Prompt wording
- Prompt execution order
- Output formatting rules
- LLM decision logic

If this implementation and the WordPress (PHP) version diverge, **this repository takes precedence.**

The app evaluates CIPD (Chartered Institute of Personnel and Development) certification submissions against assessment criteria and returns feedback summaries and suggestions for improvement.

---

## Version

- **Prompt Reference ID:** QS-PROMPT-REF-1.0
- **Status:** LOCKED
- **Date:** 22 January 2026

---

## Local Development

### Prerequisites

- Python 3.11+
- Azure OpenAI API access

### Setup

1. Clone the repository and create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with:

   ```env
   openai_ai_endpoint=<your-azure-openai-chat-endpoint-url>
   openai_api_key=<your-azure-openai-api-key>
   ```

### Run

```bash
streamlit run app.py
```

The app will open in your browser (default: http://localhost:8501).

---

## Deployment (Streamlit Cloud)

1. Fork or clone this repository.
2. Push to GitHub.
3. Go to [Streamlit Cloud](https://streamlit.io/cloud).
4. Create a new app and select:
   - **Repository:** your `quickscore-streamlit` repo
   - **Branch:** main
   - **Main file path:** `app.py`
5. Add **Secrets** (or environment variables in your Streamlit Cloud app settings):
   - `openai_ai_endpoint` – Azure OpenAI chat completions endpoint URL
   - `openai_api_key` – Azure OpenAI API key

The app uses **Azure OpenAI** (REST API), not the standard OpenAI API key.

---

## Project Structure

| Path        | Description                          |
| ----------- | ------------------------------------ |
| `app.py`    | Streamlit app and prompt reference   |
| `data.json` | Assessment criteria and reference data |
| `assets/`   | Logo and static assets               |
| `requirements.txt` | Python dependencies            |

---

## Governance Rules

- Prompt text must not be altered.
- System role must remain: **"You are a helpful assistant."**
- No frontend logic may override prompt behaviour.
- Output must remain plain text (no Markdown from the model).
- Any changes must be approved in this Streamlit implementation first.

---
