import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import time

# Configure Gemini API Key
genai.configure(api_key="YOUR_HUGGING_FACE_API_KEY")

# Function to extract video ID
def extract_video_id(url):
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([\w-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Function to fetch YouTube transcript in available language
def get_youtube_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_translatable_transcript(['en']).fetch()
        text = " ".join([t["text"] for t in transcript])
        return text
    except (TranscriptsDisabled, NoTranscriptFound):
        return "No transcript available for this video."
    except Exception as e:
        return f"Error fetching transcript: {str(e)}"

# Function to summarize text
def summarize_text(text, level="medium"):
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"Summarize the following text in {level} detail:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error summarizing text: {str(e)}"

# Function to translate text
def translate_text(text, target_language):
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"Translate the following text to {target_language}:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error translating text: {str(e)}"

# Function to generate MCQs
def generate_mcqs(text, num_questions=5):
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""
        Generate {num_questions} multiple-choice questions from this text in the format:
        Q: [Question]
        A) Option 1
        B) Option 2
        C) Option 3
        D) Option 4
        Answer: [Correct Option]
        Text: {text}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating MCQs: {str(e)}"

# Streamlit UI
st.title("📚 YouTube AI Tutor")
st.write("Enter a YouTube video URL to extract the transcript, summarize it, translate it, and generate multiple-choice questions.")

# User input
video_url = st.text_input("Enter YouTube Video URL:")
summary_level = st.radio("Select summary length:", ["short", "medium", "detailed"], index=1)
num_mcqs = st.slider("Number of MCQs:", 3, 10, 5)

if st.button("Get Transcript"):
    if video_url.strip():
        video_id = extract_video_id(video_url)
        if video_id:
            with st.spinner("Fetching transcript..."):
                transcript = get_youtube_transcript(video_id)
                st.session_state["transcript"] = transcript
                time.sleep(2)
        else:
            st.warning("Invalid YouTube URL. Please check the link.")
    else:
        st.warning("Please enter a valid YouTube URL.")

if "transcript" in st.session_state:
    st.subheader("📜 Extracted Transcript")
    st.write(st.session_state["transcript"])
    
    if st.button("Summarize Transcript"):
        with st.spinner("Generating summary..."):
            summary = summarize_text(st.session_state["transcript"], summary_level)
            st.session_state["summary"] = summary
            time.sleep(2)

if "summary" in st.session_state:
    st.subheader("📝 Summary")
    st.write(st.session_state["summary"])
    
    lang_code = st.selectbox("Select language for translation:", ["English", "Hindi", "Spanish", "French", "German", "Chinese", "Arabic", "Russian", "Japanese", "Korean"], index=0)
    if st.button("Translate Summary"):
        with st.spinner("Translating summary..."):
            translated_summary = translate_text(st.session_state["summary"], lang_code)
            st.session_state["translated_summary"] = translated_summary
            time.sleep(2)

if "translated_summary" in st.session_state:
    st.subheader("🌍 Translated Summary")
    st.write(st.session_state["translated_summary"])
    
    if st.button("Generate MCQs"):
        with st.spinner("Creating MCQs..."):
            mcq_text = generate_mcqs(st.session_state["summary"], num_mcqs)
            st.session_state["mcqs"] = mcq_text
            time.sleep(2)

if "mcqs" in st.session_state:
    st.subheader("✅ Multiple Choice Questions")
    mcqs = st.session_state["mcqs"].strip().split("\n\n")
    answers = {}
    
    for i, mcq in enumerate(mcqs):
        lines = mcq.split("\n")
        if len(lines) >= 5:
            question = lines[0]
            options = lines[1:5]
            correct_answer = lines[5].split(":")[-1].strip()
            
            st.write(question)
            user_answer = st.radio(f"Select answer for {question}", options, key=f"q{i}")
            answers[f"q{i}"] = (user_answer, correct_answer)
    
    if st.button("Submit Test"):
        score = sum(1 for key, (user_ans, correct_ans) in answers.items() if user_ans.startswith(correct_ans))
        st.success(f"🎉 Your Score: {score}/{len(answers)}")
        st.write("✅ Correct answers are highlighted below:")
        for key, (user_ans, correct_ans) in answers.items():
            st.write(f"{key}: **Correct Answer: {correct_ans}**")
