# QuickScore – Streamlit Prompt Reference

## Overview
This repository contains the LOCKED prompt reference implementation
for the QuickScore feedback tool used by Avado PQ Limited.

This Streamlit app is the canonical source of truth for:
- Prompt wording
- Prompt execution order
- Output formatting rules
- LLM decision logic

If this implementation and the WordPress (PHP) version diverge,
this repository takes precedence.

---

## Version
- Prompt Reference ID: QS-PROMPT-REF-1.0
- Status: LOCKED
- Date: 22 January 2026

---

## Deployment (Streamlit Cloud)

1. Fork or clone this repository
2. Push to GitHub
3. Go to https://streamlit.io/cloud
4. Create a new app
5. Select:
   - Repository: quickscore-streamlit
   - Branch: main
   - File: app.py
6. Add environment variable:
   - OPENAI_API_KEY

---

## Governance Rules

- Prompt text must not be altered
- System role must remain:
  "You are a helpful assistant."
- No frontend logic may override prompt behaviour
- Any changes must be approved in Streamlit first

---

