
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage
from youtube_transcript_api import YouTubeTranscriptApi
import re
import requests
from dotenv import load_dotenv
import os


load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: return match.group(1)
    return None


def get_video_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([item['text'] for item in transcript])
    except Exception as e:
        st.error(f"Error getting transcript: {e}")
        return None

def get_video_info(url):
    video_id = extract_video_id(url)
    if not video_id:
        return None, "Invalid YouTube URL"

    try:
        oembed_data = requests.get(f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json').json()
        transcript = get_video_transcript(video_id)
        if not transcript:
            return None, "Could not get video transcript"

        return {
            'title': oembed_data.get('title', 'Unknown Title'),
            'author': oembed_data.get('author_name', 'Unknown Author'),
            'url': f'https://www.youtube.com/watch?v={video_id}'
        }, transcript
    except Exception as e:
        st.error(f"Error extracting video info: {e}")
        return None, str(e)


def get_summary(prompt):
    try:
        chat = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0.7)
        messages = [
            SystemMessage(content="You are a helpful assistant that summarizes YouTube video transcripts.and you have to give answer in point ise manner "),
            HumanMessage(content=prompt)
        ]
        return chat.invoke(messages).content
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None

st.set_page_config(page_title="YouTube Video Content Summarizer", page_icon="🎥", layout="wide")
st.title("🎥 YouTube Video Content Summarizer")

if "history" not in st.session_state:
    st.session_state.history = []

url = st.text_input("Paste YouTube URL:", placeholder="https://youtube.com/watch?v=...")


if st.button(" Generate Summary"):
    if url:
        with st.spinner("🔄 Getting video content..."):
            info, transcript = get_video_info(url)
            if info and transcript:
                prompt = f"""
                Please summarize the following YouTube video transcript:
                Title: {info['title']}
                Author: {info['author']}
                Transcript: {transcript}
                """
                summary = get_summary(prompt)
                if summary:
                    st.success("✅ Summary generated successfully!")
                    st.markdown(f"### 📝 Content Summary\n{summary}")
                    st.markdown(f"**Title:** {info['title']}\n**Author:** {info['author']}\n**URL:** [Open in YouTube]({url})")
                    tab1, tab2 = st.tabs(["Summary", "Full Transcript"])
                    with tab1: st.markdown(summary)
                    with tab2: st.text(transcript)
                    st.session_state.history.append({'title': info['title'], 'url': url, 'summary': summary, 'author': info['author'], 'transcript': transcript})
    else:
        st.warning("⚠️ Please enter a YouTube URL!")



if st.session_state.history:

    st.markdown("### 📚 Previous Summaries")
    for i, item in enumerate(reversed(st.session_state.history)):
        st.markdown(f"#### Summary {i+1}: {item['title']} (by {item['author']})")

        st.markdown(f"🔗 [Watch on YouTube]({item['url']})")


        sum_tab, trans_tab = st.tabs(["Summary", "Transcript"])
        with sum_tab: st.markdown(item['summary'])
        with trans_tab: st.text(item['transcript'])
        st.markdown("---")
