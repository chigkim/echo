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


def process(audio):
    with sr.AudioFile(audio) as data:
        source = r.record(data)
        text = r.recognize_google(source, language="en")
        speech_audio = gTTS(text=text, lang="en", tld="us", slow=False)
        fp = BytesIO()
        speech_audio.write_to_fp(fp)
        fp.seek(0)
        play(fp.read())
    return text


st.set_page_config(
    page_title="Echo",
    page_icon=":material/speaker:",
)
st.title("Echo")
load_css("style.css")
r = sr.Recognizer()
if audio := mic_recorder(
    start_prompt="🎙 Record",
    stop_prompt="📤 Stop",
    just_once=False,
    use_container_width=True,
    format="wav",
    key="recorder",
):
    audio_bio = BytesIO(audio["bytes"])
    audio_bio.name = "audio.wav"
    text = process(audio_bio)
    st.button(text)
