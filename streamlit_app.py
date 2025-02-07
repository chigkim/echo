import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import base64
from io import BytesIO
from streamlit_mic_recorder import mic_recorder


@st.cache_data
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def play(audio_data):
    b64 = base64.b64encode(audio_data).decode("utf-8")
    md = f"""
    <audio autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)


def transcribe(audio):
    r = sr.Recognizer()
    with sr.AudioFile(audio) as data:
        source = r.record(data)
        text = r.recognize_google(source, language="en")
        speech_audio = gTTS(text=text, lang="en", tld="us", slow=False)
        fp = BytesIO()
        speech_audio.write_to_fp(fp)
        fp.seek(0)
        play(fp.read())
    return text


def handle_audio():
    with st.sidebar:
        if audio := mic_recorder(
            start_prompt="🎙 Record",
            stop_prompt="📤 Stop",
            just_once=True,
            use_container_width=True,
            format="wav",
            key="recorder",
        ):
            audio_bio = BytesIO(audio["bytes"])
            audio_bio.name = "audio.wav"
            return transcribe(audio_bio)


def show_messages():
    for message in st.session_state.messages:
        with st.chat_message(name="Bot"):
            st.markdown(message)


def toggle_text_chat():
    st.session_state.text_chat_enabled = not st.session_state.text_chat_enabled


st.set_page_config(
    page_title="Echo",
    page_icon=":material/speaker:",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Echo")
load_css("style.css")
if "text_chat_enabled" not in st.session_state:
    st.session_state.text_chat_enabled = False
    st.session_state.messages = []


st.sidebar.toggle(
    ":material/keyboard: Enable Text Chat",
    value=st.session_state.text_chat_enabled,
    on_change=toggle_text_chat,
)

if st.session_state.text_chat_enabled:
    show_messages()

if message := handle_audio():
    st.session_state.messages.append(message)
    if st.session_state.text_chat_enabled:
        with st.chat_message(name="Bot"):
            st.markdown(message)
