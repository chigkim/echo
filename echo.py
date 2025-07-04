import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import base64
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
import json
import re
from io import StringIO

@st.cache_data(show_spinner=False)
def _load_css(file_name: str) -> str:
    with open(file_name, encoding="utf-8") as f:
        return f.read()


def local_css(file_name: str):
    css = _load_css(file_name)
    st.html(f"<style>{css}</style>")



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


def get_client_info():
    info = {"browser": "Unknown", "os": "Unknown"}
    try:
        client_info = st_javascript(
            "await fetch('https://aisimbot.chikim.com/client-info').then(r=>r.text())"
        )
        if not client_info:
            st.stop()
        if client_info:
            client_info = json.loads(client_info)
            return client_info
    except Exception as e:
        log.exception(e)
    return info



st.set_page_config(
    page_title="Echo",
    page_icon=":material/speaker:",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Echo")
local_css("style.css")
#st.markdown(st.context.request_ip)
#st.markdown(dir(st.context.headers))
#st.markdown(st.context.ip_address)
headers = st.context.headers.to_dict()
for k, v in headers.items():
    st.markdown(f"{k}: {v}")


client_info = get_client_info()
for k, v in client_info.items():
    st.markdown(f"{k}: {v}")
browser = client_info["browser"]
safari = False
if "Safari" in browser:
    version = re.search(r"\d+\.\d+", browser)[0]
    version = float(version)
    if version >= 18.4:
        st_javascript("alert('Safari is not supported. Please use Chrome browser instead.');return 0")

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

st.markdown("To help improve both the educational value and ease of use for future students, please reflect on your overall experience and provide feedback on the following:")
with st.form("Feedback"):
    st.subheader("Interaction with Jordan: How realistic did the patient encounter feel?")
    q1 = st.text_area("*", key="q1")
    st.subheader("Guidance from Dr. Casey: How effective was the debrief in prompting reflection and providing feedback?")
    q2 = st.text_area("*", key="q2")
    st.subheader("Website Navigation: Was the interface intuitive, and did you encounter any technical difficulties?")
    q3 = st.text_area("*", key="q3")
    st.subheader("Suggestions for Improvement: Is there anything you would change or recommend for future iterations?")
    q4 = st.text_area("*", key="q4")
    submitted = st.form_submit_button("Submit")

if submitted:
    if not all(q.strip() for q in (q1, q2, q3, q4)):
        st.error("Please answer all the questions.")
        st.stop()

    buf = StringIO()
    buf.write(f"1. {q1}\n")
    buf.write(f"2. {q2}\n")
    buf.write(f"3. {q3}\n")
    buf.write(f"4: {q4}\n")
    file_bytes = buf.getvalue().encode("utf-8")
    st.download_button(
        label="Download responses",
        data=file_bytes,                # Streamlit keeps this in memory
        file_name="responses.txt",
        mime="text/plain",
    )
