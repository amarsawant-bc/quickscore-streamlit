# ==============================================================
# QuickScore Prompt Reference Implementation
#
# Version: QS-PROMPT-REF-1.0
# Status: LOCKED
# Date Locked: 22 January 2026
# Owner: Avado PQ Limited
#
# PURPOSE
# -------
# This Streamlit application is the canonical reference
# implementation for all QuickScore prompt behaviour.
#
# GOVERNANCE RULES
# ----------------
# 1. Prompt text must match the WordPress (PHP) implementation
#    character-for-character.
# 2. No semantic logic may be moved to the frontend.
# 3. System role MUST remain:
#       "You are a helpful assistant."
# 4. Output must remain plain text (no Markdown).
# 5. Any changes must be approved in Streamlit first.
#
# ==============================================================

import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# -------------------------
# STREAMLIT CONFIG
# -------------------------
st.set_page_config(
    page_title="QuickScore",
    page_icon="✅",
    layout="centered"
)

# -------------------------
# LOAD DATA
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "data.json"), "r", encoding="utf-8") as f:
    DATA = json.load(f)

# -------------------------
# LOAD LOGO (SAFE)
# -------------------------
logo_path = os.path.join(BASE_DIR, "assets", "quickscore_logo.png")
if os.path.exists(logo_path):
    st.image(logo_path, width=220)

# -------------------------
# AZURE OPENAI CONFIG
# -------------------------
AZURE_OPENAI_ENDPOINT = os.getenv("openai_ai_endpoint")
AZURE_OPENAI_API_KEY = os.getenv("openai_api_key")

def validate_config() -> tuple[bool, str]:
    """Validate that required environment variables are set."""
    if not AZURE_OPENAI_ENDPOINT:
        return False, "Missing environment variable: `openai_ai_endpoint`"
    if not AZURE_OPENAI_API_KEY:
        return False, "Missing environment variable: `openai_api_key`"
    return True, ""

def call_azure_openai(prompt: str) -> str:
    """Call Azure OpenAI API with the given prompt."""
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY:
        raise ValueError("Azure OpenAI configuration is missing. Please set environment variables.")
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY
    }

    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 800
    }

    response = requests.post(
        AZURE_OPENAI_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=60
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

# -------------------------
# UI INPUTS
# -------------------------
level = st.selectbox(
    "Select your CIPD qualification level:",
    ["Select an option"] + list(DATA.keys())
)

study_unit = assessment = question = None

if level != "Select an option":
    study_unit = st.selectbox(
        "Select your study unit:",
        list(DATA[level].keys())
    )

if study_unit:
    ac_items = DATA[level][study_unit]
    assessment = st.selectbox(
        "Select your assessment criterion:",
        [i["Assessment Criteria"] for i in ac_items]
    )

if assessment:
    question = next(
        i["Question"] for i in ac_items
        if i["Assessment Criteria"] == assessment
    )
    st.text_area("Question:", question, height=120, disabled=True)

answer = st.text_area(
    "Paste your answer here (max 400 words):",
    height=220
)

# -------------------------
# PROMPTS (LOCKED)
# -------------------------
def validation_prompt():
    return f"""
certification level: {level}
Assessment criteria: {assessment}
Study unit: {study_unit}
Question: {question}
Submitted Answer: {answer}

if submitted_answer is consist of more than 21 words then only do following if not then give output must be only
'You are not quite on the right track. Submitted answer is not sufficient to do assessment. Please provide a more detailed answer'

Considering the provided certification level, assessment criteria, study unit, and Submitted Answer, Evaluate the submitted answer.
Please Do not give any suggestions for improvement.
Evaluate Submitted answer for Chartered Institute of Personnel and Development (CIPD) certification level.
Give response in British English.
Give response without deviating from their original content.

Does the Submitted Answer demonstrate sufficient knowledge, understanding, or skill as appropriate to meet the assessment criteria?
Does at least one example included in Submitted Answer where required to support the answer?

If the submitted answer is too brief or insufficient, respond with
'The submitted answer is not sufficient to meet the assessment criteria. Please provide a more detailed answer.'

If Yes then output must be only
'You appear to be on the right track. Your answer aligns with the assessment criteria'
and briefly acknowledge and summarise the user's answer in one sentence without evaluation.

If No then output must be only
'You are not quite on the right track yet. Your answer should align more with the assessment criteria'
and briefly acknowledge and summarise the user's answer in one sentence without evaluation.
"""

def suggestion_prompt():
    return f"""
certification level: {level}
Assessment criteria: {assessment}
Study unit: {study_unit}
Question: {question}
Submitted Answer: {answer}

Using the provided certification level, Assessment criteria, Study unit, Question and Submitted Answer,
offer some suggestions in brief for improvement in the Submitted Answer so that the submitted answer
should align well with the assessment criteria.

The learner is expected to provide their response as a written paragraph, using full sentences in an academic tone.
They should not use bullet points or lists in their submitted answer.

Provide constructive feedback addressed directly to 'you'.
Use British English.
Do not use Markdown formatting.

Here are some suggestions to improve your answer:

1. Command verb identification:
    - Suggestion text here.

2. Answer structure:
    - Suggestion text here.

3. Coherence and clarity:
    - Suggestion text here.

4. Evidence and examples:
    - Suggestion text here.

5. Grammar and style:
    - Suggestion text here.

6. Feedback summary:
    - Suggestion text here.
"""

# -------------------------
# CONFIGURATION CHECK
# -------------------------
config_valid, config_error = validate_config()
if not config_valid:
    st.error(f"⚠️ **Configuration Error:** {config_error}")
    st.info("""
    **To fix this:**
    
    1. Create a `.env` file in the project root with:
       ```
       openai_ai_endpoint=https://your-endpoint.openai.azure.com
       openai_api_key=your-api-key-here
       ```
    
    2. Or set environment variables in your shell:
       ```bash
       export openai_ai_endpoint="https://your-endpoint.openai.azure.com"
       export openai_api_key="your-api-key-here"
       ```
    
    3. Restart the Streamlit app after setting the variables.
    """)
    st.stop()

# -------------------------
# SUBMIT
# -------------------------
if st.button("Submit"):
    with st.spinner("Evaluating submission..."):
        try:
            validation = call_azure_openai(validation_prompt())

            st.subheader("Validation Result")
            st.text(validation)

            if validation.startswith("You appear to be on the right track"):
                suggestions = call_azure_openai(suggestion_prompt())

                st.divider()
                st.subheader("Suggestions for Improvement")
                st.text(suggestions)
        except requests.exceptions.RequestException as e:
            st.error(f"❌ **API Error:** Failed to connect to Azure OpenAI. Please check your endpoint and API key.")
            st.code(str(e))
        except Exception as e:
            st.error(f"❌ **Error:** {str(e)}")

# -------------------------
# DISCLAIMER
# -------------------------
st.markdown("""
**Disclaimer:**  
QuickScore feedback is designed to support learning and does not replace tutor assessment or grading decisions.
Always refer to the official CIPD assessment brief and grading criteria.
""")
