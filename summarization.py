import streamlit as st
from dotenv import load_dotenv
import os
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from pytube import YouTube
import whisper

load_dotenv()

prompts = {
    "short": "Summarize this video in brief within 100 words.",
    "medium": "Summarize this video in moderate detail within 250 words.",
    "detailed": "Provide a comprehensive summary of this video in 500 words."
}

def get_video_details(youtube_video_url):
    try:
        yt = YouTube(youtube_video_url)
        return yt.title
    except Exception:
        return "Unknown Title"

def get_captions(youtube_url):
    try:
        yt = YouTube(youtube_url)
        captions = yt.captions.get_by_language_code('en')
        return captions.generate_srt_captions() if captions else "No captions available."
    except Exception as e:
        return f"Error fetching captions: {str(e)}"

def transcribe_audio(youtube_url):
    try:
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_path = audio_stream.download(filename="audio.mp3")

        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([i["text"] for i in transcript_data])
    except (TranscriptsDisabled, NoTranscriptFound):
        captions = get_captions(youtube_video_url)
        if "No captions available." not in captions:
            return captions

        return transcribe_audio(youtube_video_url)
    except Exception as e:
        return f"An error occurred: {str(e)}"

def show_summarization_page():
    st.title("YouTube Video Summarizer")
    youtube_link = st.text_input("Enter the YouTube link:", help="Paste the URL of the YouTube video to summarize.")
    transcript, summary = "", ""

    if youtube_link:
        video_id = youtube_link.split("=")[1]
        title = get_video_details(youtube_link)
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True, caption=title)

    summary_length = st.selectbox("Select summary length:", ["short", "medium", "detailed"], index=0)

    if st.button("Generate Summary"):
        with st.spinner("Extracting transcript and generating summary..."):
            transcript = extract_transcript_details(youtube_link)
            if "error" not in transcript.lower() and "disabled" not in transcript.lower():
                summary = f"Summary based on selected length ({summary_length}).\nTranscript: {transcript[:500]}..."
                st.markdown("### 📄 Summary")
                st.write(summary)

                st.markdown("### 📥 Download Summary")
                st.download_button("Download Summary", summary, file_name="summary.txt")
            else:
                st.error(transcript)

def main():
    show_summarization_page()

if __name__ == "__main__":
    main()
