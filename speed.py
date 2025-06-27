import os
import gc
import uuid
import logging

import streamlit as st

__version__ = "0.0.3"
from tornado.web import Application, RequestHandler
from tornado.routing import Rule, PathMatches

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.DEBUG
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
            log.info("DownloadHandler received request for %s bytes", size)
            chunk_size = len(_RANDOM_CHUNK)
            bytes_to_write = 0
            for i in range(size // chunk_size):
                self.write(_RANDOM_CHUNK)
                await self.flush()
                bytes_to_write += chunk_size
                log.debug("DownloadHandler wrote chunk %s, total bytes: %s", i + 1, bytes_to_write)
            remaining_bytes = size % chunk_size
            if remaining_bytes > 0:
                self.write(_RANDOM_CHUNK[:remaining_bytes])
                await self.flush()
                bytes_to_write += remaining_bytes
                log.debug("DownloadHandler wrote remaining bytes: %s, total bytes: %s", remaining_bytes, bytes_to_write)
            self.finish()
            log.info("DownloadHandler finished writing %s bytes", bytes_to_write)

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
    log.info("Speed-test initiated (v%s) — %.2f MB", __version__, size_mb)

# ----------------------------------------------------------------------------
# 4. Execute JavaScript when test_id set
# ----------------------------------------------------------------------------

from streamlit_javascript import st_javascript

if st.session_state.test_id:
    size_bytes = st.session_state.payload

    js_code = f"""(async () => {{
        const SIZE = {size_bytes};
        const start = performance.now();
        console.log('▶️ Speed-test started —', SIZE/1024/1024, 'MB');

        try {{
            // —— DOWNLOAD ——
            const dlStart = performance.now();
            const dlResponse = await fetch(`/speedtest/download/${{SIZE}}`);
            console.log('⬇️ Download Response Status:', dlResponse.status, dlResponse.statusText);
            console.log('⬇️ Download Content-Length Header:', dlResponse.headers.get('Content-Length'));
            const dlBuf = await dlResponse.arrayBuffer();
            console.log('⬇️ Download Received Bytes (dlBuf.byteLength):', dlBuf.byteLength);
            const dlEnd = performance.now();
            const dlTimeS = (dlEnd - dlStart) / 1000;
            const dlMbps = (dlBuf.byteLength * 8) / dlTimeS / 1e6;
            console.log('⬇️ Download', dlBuf.byteLength, 'bytes in', dlTimeS.toFixed(2), 's →', dlMbps.toFixed(2), 'Mbps');

            // —— UPLOAD ——
            const ulStart = performance.now();
            await fetch('/speedtest/upload', {{ method: 'POST', body: dlBuf }});
            const ulEnd = performance.now();
            const ulTimeS = (ulEnd - ulStart) / 1000;
            const ulMbps = (dlBuf.byteLength * 8) / ulTimeS / 1e6;
            console.log('⬆️ Upload', dlBuf.byteLength, 'bytes in', ulTimeS.toFixed(2), 's →', ulMbps.toFixed(2), 'Mbps');

            const totalTime = (performance.now() - start) / 1000;
            console.log('🏁 Speed-test complete in', totalTime.toFixed(2), 's');

            return {{
                download: dlMbps.toFixed(2),
                upload: ulMbps.toFixed(2),
                totalTime: totalTime.toFixed(2),
                dlTime: dlTimeS.toFixed(2),
                ulTime: ulTimeS.toFixed(2),
                dlStatus: dlResponse.status,
                dlStatusText: dlResponse.statusText,
                dlContentLength: dlResponse.headers.get('Content-Length'),
                dlReceivedBytes: dlBuf.byteLength
            }};
        }} catch (err) {{
            console.error('❌ JS error', err);
            return {{ error: err.toString() }};
        }}
    }})()"""

    result = st_javascript(js_code, key=st.session_state.test_id)
    log.info("Component returned: %s", result)

    if not result or result == 0:
        st.stop()

    if isinstance(result, dict) and not result.get("error"):
        st.metric("Total time", f"{result['totalTime']} s")
        col1, col2 = st.columns(2)
        col1.metric("Download", f"{result['download']} Mbps", delta=f"{result['dlTime']} s")
        col2.metric("Upload", f"{result['upload']} Mbps", delta=f"{result['ulTime']} s")
        log.info(
            "Speed-test complete (v%s): ↓ %s Mbps (%s s), ↑ %s Mbps (%s s), total time %s s, DL Status: %s %s, DL Content-Length: %s, DL Received Bytes: %s",
            __version__,
            result['download'],
            result['dlTime'],
            result['upload'],
            result['ulTime'],
            result['totalTime'],
            result['dlStatus'],
            result['dlStatusText'],
            result['dlContentLength'],
            result['dlReceivedBytes'],
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
