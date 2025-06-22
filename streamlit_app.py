import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import base64
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript

@st.cache_data
def load_css(file_name):
    with open(file_name) as f:
        st.html(f"<style>{f.read()}</style>")


def play(audio_data):
    b64 = base64.b64encode(audio_data).decode("utf-8")
    html_str = f"""
    <audio id="auto_player" autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    <button onclick="document.getElementById('auto_player').play()">Play</button>
    """
    print(len(html_str))
    components.html(html_str)


def get_player(audio_data):
    b64 = base64.b64encode(audio_data).decode("utf-8")
    html_str = f"""
    <audio id="player">
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    <button onclick="document.getElementById('player').play()">Play</button>
    """
    return html_str


def transcribe(audio):
    r = sr.Recognizer()
    with sr.AudioFile(audio) as data:
        source = r.record(data)
        text = r.recognize_google(source, language="en")
        return text


def tts(text):
    speech_audio = gTTS(text=text, lang="en", tld="us", slow=False)
    fp = BytesIO()
    speech_audio.write_to_fp(fp)
    fp.seek(0)
    return fp


def handle_audio():
    speech_audio = None
    transcription = None
    with st.sidebar:
        if audio := mic_recorder(
            start_prompt="🎙 Record",
            stop_prompt="📤 Stop",
            just_once=True,
            use_container_width=True,
            format="wav",
            key="recorder",
        ):
            components.html(get_player(audio["bytes"]))
            audio_bio = BytesIO(audio["bytes"])
            audio_bio.name = "audio.wav"
            transcription = transcribe(audio_bio)
            print(transcription)
            speech_audio = tts(transcription).read()
    if speech_audio:
        play(speech_audio)
    if transcription:
        return transcription


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
#st.markdown(st.context.request_ip)
#st.markdown(dir(st.context.headers))
headers = st.context.headers.to_dict()
for k, v in headers.items():
    st.markdown(f"{k}: {v}")
st.markdown(st.context.ip_address)
client_ip = st_javascript("await fetch('https://api.ipify.org').then(r=>r.text())")
st.markdown(client_ip)
#load_css("style.css")
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
