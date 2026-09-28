import streamlit as st
from google import genai
import json
import re
import time


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Study Buddy",
    page_icon="📚",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("📚 Study Buddy")

st.write(
    "Turn your notes into quizzes, flashcards, study guides, "
    "and easy explanations."
)

st.divider()


# =========================================================
# GEMINI API
# =========================================================

try:

    api_key = st.secrets["GEMINI_API_KEY"]

except KeyError:

    st.error("❌ Gemini API key was not found.")

    st.info(
        "Go to Streamlit Cloud → Manage app → Settings → "
        "Secrets and add GEMINI_API_KEY."
    )

    st.stop()


try:

    client = genai.Client(
        api_key=api_key
    )

except Exception as e:

    st.error("❌ Could not connect to Gemini.")

    st.code(str(e))

    st.stop()


# =========================================================
# GEMINI MODEL
# =========================================================

MODEL = "gemini-3.8-flash"


# =========================================================
# GEMINI FUNCTION
# =========================================================

def ask_gemini(prompt):

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            if response and response.text:

                return response.text

            st.error(
                "❌ Gemini returned an empty response."
            )

            return None

        except Exception as e:

            error_text = str(e)

            # ---------------------------------------------
            # TEMPORARY 503 ERROR
            # ---------------------------------------------

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "high demand" in error_text.lower()
            ):

                if attempt < 2:

                    time.sleep(3)

                    continue

                st.error(
                    "⚠️ Gemini is temporarily busy."
                )

                st.info(
                    "Please wait a few seconds and try again."
                )

                return None

            # ---------------------------------------------
            # MODEL ERROR
            # ---------------------------------------------

            if (
                "404" in error_text
                or "NOT_FOUND" in error_text
            ):

                st.error(
                    "❌ The Gemini model is not available "
                    "for this API key."
                )

                st.code(error_text)

                return None

            # ---------------------------------------------
            # OTHER ERROR
            # ---------------------------------------------

            st.error(
                "❌ Gemini error"
            )

            st.code(error_text)

            return None

    return None


# =========================================================
# NOTES
# =========================================================

st.header("📖 Your Notes")

notes = st.text_area(
    "Paste your notes here",
    height=300,
    placeholder=(
        "Example:\n\n"
        "Photosynthesis is the process plants use "
        "to convert light energy into chemical energy..."
    )
)


# =========================================================
# STUDY TOOL
# =========================================================

st.header("🎓 Choose a Study Tool")

option = st.selectbox(
    "What would you like to create?",
    [
        "📝 Quiz",
        "🧠 Flashcards",
        "📚 Study Guide",
        "💡 Explain My Notes"
    ]
)


# =========================================================
# QUIZ GENERATOR
# =========================================================

def generate_quiz(notes):

    prompt = f"""
Create a 10-question multiple-choice quiz using ONLY
the information in the student's notes.

Return ONLY valid JSON.

Use exactly this format:

[
  {{
    "question": "Question here",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": 0,
    "explanation": "Short explanation"
  }}
]

The answer number means:

0 = first option
1 = second option
2 = third option
3 = fourth option

Do not include markdown.
Do not include anything outside the JSON.

NOTES:

{notes}
"""

    result = ask_gemini(prompt)

    if not result:

        return None

    try:

        result = result.strip()

        result = re.sub(
            r"```json|```",
            "",
            result
        ).strip()

        return json.loads(result)

    except Exception as e:

        st.error(
            "❌ Gemini returned an invalid quiz."
        )

        st.code(str(e))

        return None


# =========================================================
# FLASHCARD GENERATOR
# =========================================================

def generate_flashcards(notes):

    prompt = f"""
Create 15 flashcards using ONLY the student's notes.

Return ONLY valid JSON.

Use exactly this format:

[
  {{
    "question": "Question here",
    "answer": "Answer here"
  }}
]

Make each question useful for studying.

Do not include markdown.
Do not include anything outside the JSON.

NOTES:

{notes}
"""

    result = ask_gemini(prompt)

    if not result:

        return None

    try:

        result = result.strip()

        result = re.sub(
            r"```json|```",
            "",
            result
        ).strip()

        return json.loads(result)

    except Exception as e:

        st.error(
            "❌ Gemini returned invalid flashcards."
        )

        st.code(str(e))

        return None


# =========================================================
# STUDY GUIDE
# =========================================================

def generate_study_guide(notes):

    return f"""
You are Study Buddy, a helpful school study assistant.

Turn the student's notes into a clear and organized
study guide.

Use these sections:

# 📌 Main Topics

# 📖 Important Vocabulary

# ⭐ Key Facts

# 🧠 Important Concepts

# ❗ Things to Remember

# 📝 Quick Review

Explain difficult ideas using simple language.

Only use information supported by the notes.

NOTES:

{notes}
"""


# =========================================================
# EXPLAIN NOTES
# =========================================================

def generate_explanation(notes):

    return f"""
You are Study Buddy, a helpful school study assistant.

Explain the student's notes in simple language.

For each major topic:

- Explain what it means.
- Explain the important idea.
- Define difficult vocabulary.
- Give a simple example when useful.
- Explain what the student should remember.

Make the explanation easy for a student to understand.

Do not invent information that is not supported by
the student's notes.

NOTES:

{notes}
"""


# =========================================================
# GENERATE BUTTON
# =========================================================

if st.button(
    "✨ Generate",
    use_container_width=True
):

    if not notes.strip():

        st.warning(
            "⚠️ Please paste your notes first."
        )

        st.stop()


    # =====================================================
    # QUIZ
    # =====================================================

    if option == "📝 Quiz":

        with st.spinner(
            "🤖 Creating your quiz..."
        ):

            quiz = generate_quiz(notes)

        if quiz:

            st.session_state.quiz = quiz

            st.session_state.quiz_answers = {}

            st.session_state.quiz_submitted = {}


    # =====================================================
    # FLASHCARDS
    # =====================================================

    elif option == "🧠 Flashcards":

        with st.spinner(
            "🤖 Creating your flashcards..."
        ):

            flashcards = generate_flashcards(notes)

        if flashcards:

            st.session_state.flashcards = flashcards


    # =====================================================
    # STUDY GUIDE
    # =====================================================

    elif option == "📚 Study Guide":

        with st.spinner(
            "🤖 Creating your study guide..."
        ):

            result = ask_gemini(
                generate_study_guide(notes)
            )

        if result:

            st.session_state.study_guide = result


    # =====================================================
    # EXPLAIN NOTES
    # =====================================================

    else:

        with st.spinner(
            "🤖 Explaining your notes..."
        ):

            result = ask_gemini(
                generate_explanation(notes)
            )

        if result:

            st.session_state.explanation = result


# =========================================================
# FLASHCARDS
# =========================================================

if "flashcards" in st.session_state:

    st.divider()

    st.header("🧠 Flashcards")

    st.write(
        "Click a question to reveal the answer."
    )

    for i, card in enumerate(
        st.session_state.flashcards
    ):

        with st.expander(
            f"❓ {card['question']}"
        ):

            st.success(
                f"💡 {card['answer']}"
            )


# =========================================================
# QUIZ
# =========================================================

if "quiz" in st.session_state:

    st.divider()

    st.header("📝 Quiz")

    quiz = st.session_state.quiz

    for i, question in enumerate(quiz):

        st.subheader(
            f"Question {i + 1} of {len(quiz)}"
        )

        st.write(
            question["question"]
        )

        submitted = (
            st.session_state.quiz_submitted.get(
                i,
                False
            )
        )

        if not submitted:

            answer = st.radio(
                "Choose your answer:",
                question["options"],
                key=f"quiz_answer_{i}",
                index=None
            )

            if st.button(
                "Submit Answer",
                key=f"submit_{i}"
            ):

                if answer is None:

                    st.warning(
                        "Please choose an answer first."
                    )

                else:

                    selected_index = (
                        question["options"].index(
                            answer
                        )
                    )

                    st.session_state.quiz_answers[i] = (
                        selected_index
                    )

                    st.session_state.quiz_submitted[i] = (
                        True
                    )

                    st.rerun()

        else:

            selected_index = (
                st.session_state.quiz_answers[i]
            )

            correct_index = (
                question["answer"]
            )

            if selected_index == correct_index:

                st.success(
                    "✅ Correct!"
                )

            else:

                st.error(
                    "❌ Incorrect."
                )

            st.info(
                "Correct answer: "
                + question["options"][correct_index]
            )

            st.write(
                "**Explanation:** "
                + question["explanation"]
            )


# =========================================================
# QUIZ SCORE
# =========================================================

if "quiz" in st.session_state:

    quiz = st.session_state.quiz

    submitted_count = len(
        st.session_state.quiz_submitted
    )

    if submitted_count == len(quiz):

        score = 0

        for i, question in enumerate(quiz):

            if (
                st.session_state.quiz_answers.get(i)
                == question["answer"]
            ):

                score += 1

        st.divider()

        st.header("🏆 Quiz Complete!")

        st.write(
            f"You scored **{score}/{len(quiz)}**."
        )

        if st.button(
            "🔄 Make Another Quiz"
        ):

            del st.session_state.quiz

            st.session_state.quiz_answers = {}

            st.session_state.quiz_submitted = {}

            st.rerun()


# =========================================================
# STUDY GUIDE
# =========================================================

if "study_guide" in st.session_state:

    st.divider()

    st.header("📚 Your Study Guide")

    st.markdown(
        st.session_state.study_guide
    )


# =========================================================
# EXPLANATION
# =========================================================

if "explanation" in st.session_state:

    st.divider()

    st.header("💡 Explanation")

    st.markdown(
        st.session_state.explanation
    )
