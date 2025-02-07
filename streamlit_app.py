# pip install streamlit SpeechRecognition gTTS
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import base64
from io import BytesIO

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
        text = r.recognize_google(source, language='en')
        speech_audio = gTTS(text=text, lang="en", tld='us', slow=False)
        fp = BytesIO()
        speech_audio.write_to_fp(fp)
        fp.seek(0)
        play(fp.read())

st.set_page_config(
    page_title="Echo",
    page_icon=":material/speaker:",
)
st.title("Echo")
r = sr.Recognizer() 
if "audio_input_key_counter" not in st.session_state:
    st.session_state.audio_input_key_counter = 0

audio_input_key = f"audio_input_key_{st.session_state.audio_input_key_counter}"
if audio := st.audio_input(label=" ", label_visibility="collapsed", key=audio_input_key):
    process(audio)
    del st.session_state[audio_input_key]
    st.session_state.audio_input_key_counter += 1
