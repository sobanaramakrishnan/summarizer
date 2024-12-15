import streamlit as st
from dotenv import load_dotenv
import os
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import google.generativeai as genai
from pytube import YouTube
from rake_nltk import Rake
from googletrans import Translator
from nltk.corpus import wordnet as wn
import nltk
nltk.download('wordnet')
# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompts for summary generation
prompts = {
    "short": "Summarize this video in brief within 100 words.",
    "medium": "Summarize this video in moderate detail within 250 words.",
    "detailed": "Provide a comprehensive summary of this video in 500 words."
}

# Helper Functions
def get_video_details(youtube_video_url):
    try:
        yt = YouTube(youtube_video_url)
        return yt.title
    except Exception:
        return "Unknown Title"

def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([i["text"] for i in transcript_data])
        return transcript
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except NoTranscriptFound:
        return "No transcript found for this video."
    except Exception as e:
        return f"An error occurred while retrieving the transcript: {str(e)}"

def generate_gemini_content(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt + transcript_text)
        return response.text
    except Exception as e:
        return f"Failed to generate summary: {str(e)}"

def translate_text(text, target_language):
    try:
        translator = Translator()
        return translator.translate(text, src='en', dest=target_language).text
    except Exception:
        return "Translation failed."

def get_word_meaning(word):
    synsets = wn.synsets(word)
    return synsets[0].definition() if synsets else "Sorry, no definition found for this word."

def chatbot_respond(query, transcript):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(f"Answer the following question based on the video transcript: {query}\nTranscript: {transcript}")
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Page Functions
# Show summarization page
def show_summarization_page():

    # Create two columns: one for the logo and one for the title
    col1, col2 = st.columns([2, 2])  # Adjust the columns' width ratio

    with col1:
        # Logo with width 350
        st.image("logo.png", width=350)

    with col2:
        # Title with Times New Roman font and centered with a little lower margin
        st.markdown("""
            <h1 style="text-align: left; font-family: 'Times New Roman', Times, serif; font-size: 40px; margin-top: 50px;">
                SumAize
            </h1>
        """, unsafe_allow_html=True)

    youtube_link = st.text_input("Enter the YouTube link:", help="Paste the URL of the YouTube video to summarize.")
    transcript, summary = "", ""

    if youtube_link:
        video_id = youtube_link.split("=")[1]
        title = get_video_details(youtube_link)
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True, caption=title)

    summary_length = st.selectbox("Select summary length:", ["short", "medium", "detailed"], index=0)

    translate_language = st.selectbox("Select language for translation:", ["Tamil", "Hindi", "French"])
    lang_map = {"Tamil": "ta", "Hindi": "hi", "French": "fr"}

    if st.button("Generate Summary"):
        with st.spinner("Extracting transcript and generating summary..."):
            transcript = extract_transcript_details(youtube_link)
            if "error" not in transcript.lower() and "disabled" not in transcript.lower():
                summary = generate_gemini_content(transcript, prompts[summary_length])
                st.markdown("### 📄 Summary")
                st.write(summary)

                translated_summary = translate_text(summary, lang_map[translate_language])
                st.markdown(f"### 📄 Translated Summary ({translate_language})")
                st.write(translated_summary)

                st.markdown("### 📥 Download Summary")
                st.download_button("Download Summary", summary, file_name="summary.txt")
            else:
                st.error(transcript)

def show_dictionary_page():
    st.markdown("### 📖 Dictionary")
    word = st.text_input("Enter a word to get its meaning:")
    if word:
        st.write(f"**Meaning:** {get_word_meaning(word)}")

def show_chatbot_section():
    st.markdown("### 🤖 Chatbot")
    youtube_link = st.text_input("Re-enter the YouTube link for chatbot:")
    transcript = extract_transcript_details(youtube_link) if youtube_link else ""
    user_query = st.text_input("Ask a question about the video:")
    if user_query:
        if transcript and "error" not in transcript.lower() and "disabled" not in transcript.lower():
            with st.spinner("Fetching answer..."):
                st.write(f"**Answer:** {chatbot_respond(user_query, transcript)}")
        else:
            st.warning("Please provide a valid YouTube link and ensure the transcript is available.")

# Main Function
def main():
    show_summarization_page()
    st.markdown("---")
    show_dictionary_page()
    st.markdown("---")
    show_chatbot_section()

if __name__ == "__main__":
    main() 
