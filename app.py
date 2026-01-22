# ==============================================================
# QuickScore Prompt Reference Implementation
#
# Version: QS-PROMPT-REF-1.0
# Status: LOCKED
# Date Locked: 22 January 2026
#
# PURPOSE
# -------
# This Streamlit application is the canonical reference
# implementation for all QuickScore prompt behaviour.
#
# It defines the authoritative:
# - Prompt wording (Validation & Suggestions)
# - Prompt ordering and execution flow
# - System and user role usage
# - Output constraints and formatting rules
# - Decision logic delegated to the LLM
#
# GOVERNANCE RULES
# ----------------
# 1. Prompt text must match the WordPress (PHP) implementation
#    character-for-character.
# 2. No semantic logic (e.g. word count thresholds) may be moved
#    to the frontend.
# 3. The system role MUST remain:
#       "You are a helpful assistant."
# 4. Output must remain plain text (no Markdown).
# 5. Any future changes must be:
#       Streamlit → approved → ported to PHP
#
# If PHP and Streamlit outputs diverge, this Streamlit version
# is the source of truth.
#
# ============================================================== 

import json
import streamlit as st
from openai import OpenAI

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(
    page_title="QuickScore",
    page_icon="✅",
    layout="centered"
)

client = OpenAI(
    api_key=os.getenv("openai_api_key"),
    base_url=os.getenv("openai_api_endpoint")
)


# -------------------------
# LOAD DATA
# -------------------------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

# -------------------------
# UI
# -------------------------
st.image("quickscore_logo.png", width=220)

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
        "Select an assessment criterion:",
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
# PROMPTS (PHP-IDENTICAL)
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
offer suggestions in brief for improvement so that the submitted answer aligns with the assessment criteria.

The learner is expected to provide their response as a written paragraph using full sentences in an academic tone.
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
# SUBMIT
# -------------------------
if st.button("Submit"):
    with st.spinner("Evaluating submission..."):
        validation = client.chat.completions.create(
            model="gpt-35-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": validation_prompt()}
            ]
        ).choices[0].message.content.strip()

        st.subheader("Validation Result")
        st.text(validation)

        if validation.startswith("You appear to be on the right track"):
            suggestions = client.chat.completions.create(
                model="gpt-35-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": suggestion_prompt()}
                ]
            ).choices[0].message.content.strip()

            st.divider()
            st.subheader("Suggestions for Improvement")
            st.text(suggestions)
