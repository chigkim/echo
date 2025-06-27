import os
import gc
import uuid
import logging

import streamlit as st
from tornado.web import Application, RequestHandler
from tornado.routing import Rule, PathMatches

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# 1. Register Tornado handlers once
# ----------------------------------------------------------------------------

# Create a 1MB chunk of random data to be reused.
# This is much faster than generating it on every request.
_RANDOM_CHUNK = os.urandom(1 * 1024 * 1024)


@st.cache_resource()
def _setup_speed_handlers():
    """Expose /speedtest/download and /speedtest/upload endpoints."""

    class DownloadHandler(RequestHandler):
        async def get(self, size_str: str):
            size = int(size_str)
            self.set_header("Content-Type", "application/octet-stream")
            payload = (_RANDOM_CHUNK * (size // len(_RANDOM_CHUNK) + 1))[:size]
            self.write(payload)
            log.info("Served download payload: %s bytes", size)

    class UploadHandler(RequestHandler):
        async def post(self):
            log.info("Received upload payload: %s bytes", len(self.request.body))
            self.write(str(len(self.request.body)))

    app = next(o for o in gc.get_referrers(Application) if isinstance(o, Application))
    app.wildcard_router.rules.insert(0, Rule(PathMatches(r"/speedtest/download/([0-9]+)"), DownloadHandler))
    app.wildcard_router.rules.insert(0, Rule(PathMatches(r"/speedtest/upload"), UploadHandler))

_setup_speed_handlers()

# ----------------------------------------------------------------------------
# 2. Streamlit state
# ----------------------------------------------------------------------------

if "test_id" not in st.session_state:
    st.session_state.test_id = None
    st.session_state.payload = 10 * 1024**2  # default 10 MB

# ----------------------------------------------------------------------------
# 3. UI
# ----------------------------------------------------------------------------

st.title("📶 Client ↔ Server Speed Test (Debug Mode)")

size_mb = st.slider("Payload size (MB)", 1, 100, 10)

if st.button("Run test"):
    st.session_state.test_id = str(uuid.uuid4())
    st.session_state.payload = size_mb * 1024 * 1024
    log.info("Speed-test initiated — %.2f MB", size_mb)

# ----------------------------------------------------------------------------
# 4. Execute JavaScript when test_id set
# ----------------------------------------------------------------------------

if st.session_state.test_id:
    size_bytes = st.session_state.payload

    js_code = f"""(async () => {{
        const SIZE = {size_bytes};
        const start = performance.now();
        console.log('▶️ Speed-test started —', SIZE/1024/1024, 'MB');

        try {{
            // —— DOWNLOAD ——
            const dlStart = performance.now();
            const dlBuf   = await fetch(`/speedtest/download/${{SIZE}}`).then(r => r.arrayBuffer());
            const dlEnd   = performance.now();
            const dlMbps  = (dlBuf.byteLength * 8) / ((dlEnd - dlStart) / 1000) / 1e6;
            console.log('⬇️ Download', dlBuf.byteLength, 'bytes @', dlMbps.toFixed(2), 'Mbps');

            // —— UPLOAD ——
            const ulStart = performance.now();
            await fetch('/speedtest/upload', {{ method: 'POST', body: dlBuf }});
            const ulEnd   = performance.now();
            const ulMbps  = (dlBuf.byteLength * 8) / ((ulEnd - ulStart) / 1000) / 1e6;
            console.log('⬆️ Upload', dlBuf.byteLength, 'bytes @', ulMbps.toFixed(2), 'Mbps');

            const totalTime = (performance.now() - start) / 1000;
            console.log('🏁 Speed-test complete in', totalTime.toFixed(2), 's');

            return {{ download: dlMbps.toFixed(2), upload: ulMbps.toFixed(2), totalTime: totalTime.toFixed(2) }};
        }} catch (err) {{
            console.error('❌ JS error', err);
            return {{ error: err.toString() }};
        }}
    }})()"""

    from streamlit_javascript import st_javascript

    result = st_javascript(js_code, key=st.session_state.test_id)
    log.info("Component returned: %s", result)

    if not result or result == 0:
        st.stop()

    if isinstance(result, dict) and not result.get("error"):
        st.metric("Total time", f"{result['totalTime']} s")
        col1, col2 = st.columns(2)
        col1.metric("Download", f"{result['download']} Mbps")
        col2.metric("Upload", f"{result['upload']} Mbps")
        log.info(
            "Speed-test complete: ↓ %s Mbps, ↑ %s Mbps, total time %s s",
            result['download'],
            result['upload'],
            result['totalTime'],
        )
    else:
        st.error(f"JavaScript execution error: {result}")

    st.session_state.test_id = None

# ----------------------------------------------------------------------------
# Usage
# ----------------------------------------------------------------------------
#   $ pip install streamlit streamlit-javascript
#   $ streamlit run speed_test_app.py
# ----------------------------------------------------------------------------
