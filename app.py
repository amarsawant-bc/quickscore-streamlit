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
# Validation prompt
# -------------------------
def validation_prompt():
    validation_criteria = ""
    minimum_criteria = ""
    if level.lower().find("level 3") != -1:
        minimum_criteria = "2 out of 3"
        validation_criteria = f"""
1. Presentation: atleast one of the following must be present:
   - Is the answer presented in an appropriate structure?
   - Is the answer easy to read and to make sense of?
   - Is the formatting of the text appropriate?

2. Response to question: atleast one of the following must be present:
   - Does the answer address the commend verb outlined in the question?
   - Does the answers demonstrate sufficient knowledge and understanding to meet the assessment criteria question?

3. Reference To The Scenario: atleast one of the following must be present:
   - Is the answer applied to the case organisation outlined on the assessment brief?
   - Does the answer relate to the context of the scenario?
        """
    elif level.lower().find("level 5") != -1:
        minimum_criteria = "4 out of 5"
        validation_criteria = f"""
1. Referencing: atleast one of the following must be present:
   - Are intext citations present?
   - Do they align with the reference list if there is one. If no reference list present advice should be offered on this in terms of reminding the learner to do it before they submit?
   - Are they formatted using the Harvard referencing system?
   - Is the formatting of all in text citations consistent?

2. Presentation: atleast one of the following must be present:
   - Is the answer presented in an appropriate structure?
   - Is the answer easy to read and to make sense of?
   - Is the formatting of the text appropriate?

3. Wider Reading: atleast one of the following must be present:
   - Does the answers include evidence of wider reading?
   - Are the sources cited of a good quality eg from recognised textbooks, published sources, academic papers?
   - Are the sources cited from within the last five years?
   - Are they used to support the arguments developed?

4. Reference To The Scenario: atleast one of the following must be present:
   - Is the answer applied to the case organisation outlined on the assessment brief?
   - Does the answer relate to the context of the scenario?

5. Response to question: atleast one of the following must be present:
   - Does the answer address the commend verb outlined in the question?
   - Does the answers demonstrate sufficient knowledge and understanding to meet the assessment criteria question?
        """
    elif level.lower().find("level 7") != -1:
        minimum_criteria = "4 out of 6"
        validation_criteria = f"""
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
    """

    return f"""
certification level: {level}
Assessment criteria: {assessment}
Study unit: {study_unit}
Question: {question}
Submitted Answer: {answer}

if submitted_answer is consist of more than {800 if level.lower().find("level 7") != -1 else 21} words then only do following if not then give output must be only
'You're not quite on the right track yet. Please consider the suggestions below and revise your response.'

Considering the provided certification level, assessment criteria, study unit, and Submitted Answer, Evaluate the submitted answer.
Please Do not give any suggestions for improvement.
Evaluate Submitted answer for Chartered Institute of Personnel and Development (CIPD) certification level.
Give response in British English.
Give response without deviating from their original content.

EVALUATION CRITERIA:
Evaluate the submitted answer against the following criteria to determine if it demonstrates sufficient knowledge, understanding, or skill:

{validation_criteria}

DECISION RULES:
- The answer must meet atleast {minimum_criteria} evaluation criteria listed above.
- The answer must address the command verb and link points to assessment criteria (Focus).
- The answer must demonstrate depth of understanding, not just surface-level listing.
- The answer must include at least one example where required to support the answer.
- The answer must not be too brief or insufficient.

If the answer meets atleast {minimum_criteria} evaluation criteria, then output must be only
'You've made a good start. Here are some suggestions to help you further strengthen and refine your response.'
and briefly acknowledge and summarise the user's answer in one sentence without evaluation.

If the answer does not meet atleast {minimum_criteria} evaluation criteria, then output must be only
'You are not yet on the right track. Here are some suggestions to help you strengthen and expand your response.'
and briefly acknowledge and summarise the user's answer in one sentence without evaluation.
"""

#
# Suggestion prompt
#
def suggestion_prompt():
    suggestion_prompt = ""
    if level.lower().find("level 3") != -1:
        suggestion_prompt = f"""
1. Presentation:
   [1-2 sentences on whether the answer has appropriate structure, is easy to read and make sense of, and has appropriate formatting]

2. Response to question:
   [1-2 sentences on whether the answer addresses the command verb outlined in the question and demonstrates sufficient knowledge and understanding to meet the assessment criteria]

3. Reference To The Scenario:
   [1-2 sentences on whether the answer is applied to the case organisation outlined in the assessment brief and relates to the context of the scenario]
"""
    elif level.lower().find("level 5") != -1:
        suggestion_prompt = f"""
1. Referencing:
   [1-2 sentences on whether in-text citations are present, align with the reference list (or advise adding a reference list if absent), use Harvard formatting, and are consistent]

2. Presentation:
   [1-2 sentences on whether the answer has appropriate structure, is easy to read and make sense of, and has appropriate formatting]

3. Wider Reading:
   [1-2 sentences on whether the answer includes evidence of wider reading, uses good-quality sources (e.g. recognised textbooks, published or academic sources), uses sources from the last five years, and uses them to support the arguments developed. If the question specifies a particular model or framework, do not suggest that additional models need to be explored.]

4. Reference To The Scenario:
   [1-2 sentences on whether the answer is applied to the case organisation outlined in the assessment brief and relates to the context of the scenario]

5. Response to question:
   [1-2 sentences on whether the answer addresses the command verb outlined in the question and demonstrates sufficient knowledge and understanding to meet the assessment criteria]
"""
    elif level.lower().find("level 7") != -1:
        suggestion_prompt = f"""
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
"""
    
    return f"""
certification level: {level}
Assessment criteria: {assessment}
Study unit: {study_unit}
Question: {question}
Submitted Answer: {answer}

Using the provided certification level, Assessment criteria, Study unit, Question and Submitted Answer,
offer brief suggestions for improvement in the Submitted Answer. Keep feedback concise - only 1-2 sentences per point.

The learner is expected to provide their response as a written paragraph, using full sentences in an academic tone.
They should not use bullet points or lists in their submitted answer.

Provide constructive feedback addressed directly to 'you'.
Use British English.
Do not use Markdown formatting.

Evaluation criteria as below:
{suggestion_prompt}

Output format rules:
- Return feedback in the exact same numbered structure and order as the evaluation criteria above.
- For each numbered point, start with the criterion heading exactly as shown (e.g. `1. Presentation:`) followed by your 1-2 sentence feedback on the same line.
- Provide exactly 1-2 sentences for each numbered point.
- Do not add an overall summary, introduction, conclusion, or any extra text outside the numbered points.

Make sure suggestions for improvement are written as clear, single paragraphs rather than long run-on text.
Keep each suggestion brief and actionable. Focus on the most important improvements needed.
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
            # print("validation=====", validation_prompt())
            st.subheader("Word Count")
            st.markdown(f""" Calculated Word Count: {calculateWordCount(answer)} """, unsafe_allow_html=True)
            # print("validation_prompt=====", validation_prompt())
            # print("suggestion_prompt=====", suggestion_prompt())

            st.divider()
            st.subheader("Feedback Summary")
            st.text(validation)

            # if validation.startswith("You appear to be on the right track"):
            suggestions = call_azure_openai(suggestion_prompt())

            st.divider()
            st.subheader("Suggestions for Improvement")
            st.text(suggestions)

            if level.lower().find("level 3") != -1:
                st.markdown("")  # Add spacing before disclaimer
                st.markdown(""" 
                <b>Top tips:</b>
                <ul>
                    <li><b>Address the command verb</b> used in the question (e.g. evaluate, assess, analyse) and ensure your response clearly demonstrates that level of thinking.</li>
                    <li><b>Apply your answer directly to the case study</b> provided rather than responding in general terms.</li>
                    <li><b>Follow the required format</b> specified in the assignment brief (e.g. report structure, headings, or specific sections requested).</li>
                    <li><b>Check that your response stays within the maximum word limit</b> set out in the assignment brief.</li>
                </ul>
                """, unsafe_allow_html=True)
            elif level.lower().find("level 5") != -1:
                st.markdown("")  # Add spacing before disclaimer
                st.markdown(""" 
                <b>Always remember to:</b>
                <ul>
                    <li><b>Address the command verb</b> used in the question (e.g. evaluate, assess, analyse) and ensure your response clearly demonstrates that level of thinking.</li>
                    <li><b>Include at least one credible reference</b> to support your answer (e.g. CIPD resources, academic sources, or recognised industry research).</li>
                    <li><b>Apply your answer directly to the case study</b> provided rather than responding in general terms.</li>
                    <li><b>Follow the required format</b> specified in the assignment brief (e.g. report structure, headings, or specific sections requested).</li>
                    <li><b>Check that your response stays within the maximum word limit</b> set out in the assignment brief.</li>
                </ul>
                """, unsafe_allow_html=True)
            elif level.lower().find("level 7") != -1:
                st.markdown("""
                <b>Remember to:</b>
                <ul>
                    <li><b>Evaluate, don't describe:</b> Focus on critical evaluation rather than mere description. Answer in line with the command verbs.</li>
                    <li><b>Use recent research:</b> Ensure your references are from the last 5 years, except for classic theories.</li>
                    <li><b>Consider both sides:</b> Discuss both advantages and disadvantages in your evaluations, where appropriate.</li>
                    <li><b>Support claims with evidence:</b> Avoid making bold claims without solid evidence to back them up.</li>
                    <li><b>Use the Hub writing resources:</b> Visit the <a href="https://hub.avadolearning.com/learn/learning-path/level-7-writing-resources" target="_blank">writing resources area</a> in the Hub for guidance on structure, referencing and academic writing.</li>
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
