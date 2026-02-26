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
import re
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

# feedback summary prompt
def feedback_summary_prompt():
    return f"""
if submitted_answer is consist of more than 800 words then only do following if not then give output must be only
'You are not quite on the right track. Submitted answer is not sufficient to do assessment. Please provide a more detailed answer'

Considering the provided certification level, assessment criteria, study unit, and Submitted Answer, Evaluate the submitted answer.
Please Do not give any suggestions for improvement.
Evaluate Submitted answer for Chartered Institute of Personnel and Development (CIPD) certification level.
Give response in British English.
Give response without deviating from their original content.

EVALUATION CRITERIA:
Evaluate the submitted answer against the following criteria to determine if it demonstrates sufficient knowledge, understanding, or skill:

1. Focus: atleast one of the following must be present:
   - Does the answer directly address the command verb used in the question (e.g. analyse, evaluate, explain)?
   - Does it explicitly link each point back to the relevant assessment criteria?
   - Does all content remain tightly focused on the question, with no drift or irrelevant sections?

2. Depth & breadth of understanding: atleast one of the following must be present:
   - Does it develop points in sufficient depth rather than just listing information?
   - Does it critically analyse points rather than simply listing models or theories?
   - Does it expand and strengthen relevant arguments instead of introducing too many additional ones?

3. Strategic application & professional advice: atleast one of the following must be present:
   - Does it clearly explain the organisational context relevant to the answer?
   - Does it explicitly link theory to its practical impact on people practice?
   - Does it clearly identify the strategic implications for the organisation?

4. Research & wider reading: atleast one of the following must be present:
   - Does it support key points with relevant academic or professional sources?
   - Does it integrate references directly into the argument, rather than listing them separately?
   - Does it use recent evidence (from the last 5 years) to strengthen credibility and relevance?

5. Persuasiveness & originality: atleast one of the following must be present:
   - Does it present a clear and convincing argument, supported by logical reasoning and evidence?
   - Does it demonstrate independent thinking by critically evaluating ideas rather than simply describing them?
   - Does it apply theory in an insightful way that strengthens the relevance and impact of the argument?

6. Presentation & language: atleast one of the following must be present:
   - Is the text organised into three main parts: Introduction, Main Body, Conclusion?
   - Does it use clear signposting to help the reader follow the argument?
   - Does the conclusion clearly synthesise the key points?

DECISION RULES:
- The answer must meet atleast 4 out of 6 evaluation criteria listed above.
- The answer must address the command verb and link points to assessment criteria (Focus).
- The answer must demonstrate depth of understanding, not just surface-level listing.
- The answer must include at least one example where required to support the answer.
- The answer must not be too brief or insufficient.

If the answer meets atleast 4 out of 6 evaluation criteria, then output must be only
'You've made a good start. Here are some suggestions to help you further strengthen and refine your response.'
and briefly acknowledge and summarise the user's answer in one sentence without evaluation.

If the answer does not meet atleast 4 out of 6 evaluation criteria, then output must be only
'You are not yet on the right track. Here are some suggestions to help you strengthen and expand your response.'
and briefly acknowledge and summarise the user's answer in one sentence without evaluation.
"""

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

if level.lower().find("level 7") != -1:
    feedback_summary_prompt_text = st.text_area(
        "Feedback Summary Prompt:",
        value=feedback_summary_prompt(),
        height=220
    )
    answer = st.text_area(
        "Paste your answer here (max 1000 words):",
        height=220
    )
else:
    answer = st.text_area(
        "Paste your answer here (max 400 words):",
        height=220
    )

def calculateWordCount(answer):
  if not answer: return 0

  totalWords = 0

  if answer:
    totalWords = extractCountableWords(answer)

  return totalWords

def extractCountableWords(text):
    if not text or len(text.strip()) == 0: 
        return 0

    cleanText = text.strip()
    cleanText = stripHtmlWithDOMParser(cleanText)
    # Split by whitespace (spaces, newlines, tabs, etc.) and filter out empty strings
    calculatedWords = [word.strip() for word in re.split(r'[\s\n\r\t]+', cleanText.strip()) if word.strip()]
    return len(calculatedWords)

def stripHtmlWithDOMParser(htmlString):
    cleanText = htmlString.strip()
    cleanText = cleanText.replace('</th>', '</th> ')
    cleanText = cleanText.replace('</td>', '</td> ')
    cleanText = cleanText.replace('</tr>', '</tr> ')
    cleanText = cleanText.replace('</table>', '</table> ')
    cleanText = cleanText.replace('<p', ' <p')
    cleanText = cleanText.replace('</p>', '</p> ')
    # Remove table tags including inner text so that tables are also removed
    cleanText = re.sub(r'<table\b[^>]*>[\s\S]*?</table>', '', cleanText, flags=re.IGNORECASE)
    # Remove <s> tags including inner text so that strikethrough text is also removed
    cleanText = re.sub(r'<s\b[^>]*>[\s\S]*?</s>', '', cleanText, flags=re.IGNORECASE)
    # Remove all tags and keep inner text
    cleanText = re.sub(r'<[^>]+>', '', cleanText)
    # Remove AC 1.5 from the beginning of the text
    cleanText = re.sub(r'^AC\s?[1-9]\.[1-9]\s*', '', cleanText, flags=re.IGNORECASE)
    cleanText = cleanText.replace('&nbsp;', ' ')
    # Replace multiple whitespace with single space and trim
    cleanText = re.sub(r'\s+', ' ', cleanText).strip()
    return cleanText


# -------------------------
# PROMPTS (LOCKED)
# -------------------------
def validation_prompt():
    if level.lower().find("level 7") != -1:
        return f"""
certification level: {level}
Assessment criteria: {assessment}
Study unit: {study_unit}
Question: {question}
Submitted Answer: {answer}

{feedback_summary_prompt_text}
"""
    else:
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
    if level.lower().find("level 7") != -1:
        return f"""
certification level: {level}
Assessment criteria: {assessment}
Study unit: {study_unit}
Question: {question}
Submitted Answer: {answer}

Using the provided certification level, Assessment criteria, Study unit, Question and Submitted Answer,
offer brief suggestions for improvement in the Submitted Answer. Keep feedback concise - only 1-2 sentences per point.

Provide constructive feedback addressed directly to 'you'.
Use British English.
Do not use Markdown formatting.

Evaluation criteria:
1. Focus:
   [1-2 sentences on addressing the command verb and linking to assessment criteria]

2. Depth & breadth of understanding:
   [1-2 sentences on developing points in depth and critical analysis]

3. Strategic application & professional advice:
   [1-2 sentences on organisational context and linking theory to practice]

4. Research & wider reading:
   [1-2 sentences on supporting points with sources and using recent evidence]

5. Persuasiveness & originality:
   [1-2 sentences on presenting a clear argument with independent thinking]

6. Presentation & language:
   [1-2 sentences on structure (Introduction, Main Body, Conclusion) and signposting]

Keep each suggestion brief and actionable. Focus on the most important improvements needed.
"""
    else:
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
            st.subheader("Word Count")
            st.text("Calculated word count: " + str(calculateWordCount(answer)) + " words")
            if level.lower().find("level 7") != -1:
                st.text("Acceptable Range (±10% tolerance): 900 - 1100 words") #1000 words ± 10% = 900 - 1100 words
            else:
                st.text("Acceptable Range (±10% tolerance): 360 - 440 words") #400 words ± 10% = 360 - 440 words

            st.divider()
            st.subheader("Feedback Summary")
            st.text(validation)

            # if validation.startswith("You appear to be on the right track"):
            suggestions = call_azure_openai(suggestion_prompt())

            st.divider()
            st.subheader("Suggestions for Improvement")
            st.text(suggestions)

            if level.lower().find("level 7") != -1:
                st.markdown("")  # Add spacing before disclaimer
                st.markdown(""" 
                <b>Remember to:</b>
                <ul>
                    <li><b>Evaluate, don't describe:</b> Focus on critical evaluation rather than mere description. Answer in line with the command verbs.</li>
                    <li><b>Use recent research:</b> Ensure your references are from the last 5 years, except for classic theories.</li>
                    <li><b>Consider both sides:</b> Discuss both advantages and disadvantages in your evaluations, where appropriate.</li>
                    <li><b>Support claims with evidence:</b> Avoid making bold claims without solid evidence to back them up.</li>
                </ul>
                """, unsafe_allow_html=True)
        except requests.exceptions.RequestException as e:
            st.error(f"❌ **API Error:** Failed to connect to Azure OpenAI. Please check your endpoint and API key.")
            st.code(str(e))
        except Exception as e:
            st.error(f"❌ **Error:** {str(e)}")

# -------------------------
# DISCLAIMER
# -------------------------
st.markdown("")  # Add spacing before disclaimer
st.markdown("""
<small>
<i>
<b>Disclaimer:</b>  
QuickScore feedback is designed to support learning and does not replace tutor assessment or grading decisions. Always refer to the official CIPD assessment brief and grading criteria.
</i>
</small>
""", unsafe_allow_html=True)
