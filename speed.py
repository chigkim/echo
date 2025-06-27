import os
import gc
import uuid
import logging

import streamlit as st

__version__ = "0.0.9" # Incrementing version for this significant change

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO # Reverting to INFO as DEBUG was for server-side issues
)
log = logging.getLogger(__name__)


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

    with open("static/js/speed_test.js", "r") as f:
        js_code = f.read()
    js_code = js_code.replace("__SIZE_PLACEHOLDER__", str(size_bytes))

    result = st_javascript(js_code, key=st.session_state.test_id)
    log.info("Component returned: %s", result)

    if not result or result == 0:
        st.stop()

    if isinstance(result, dict) and not result.get("error"):
        st.metric("Total time", f"{result['totalTime']} s")
        col1, col2 = st.columns(2)
        col1.metric("Download (simulated)", f"{result['download']} Mbps", delta=f"{result['dlTime']} s")
        col2.metric("Upload (Streamlit transfer)", "N/A", delta="N/A")
        log.info(
            "Speed-test complete (v%s): ↓ %s Mbps (%s s), total time %s s",
            __version__,
            result['download'],
            result['dlTime'],
            result['totalTime'],
        )
        if "debugLogs" in result:
            for log_msg in result["debugLogs"]:
                log.info("JS Debug: %s", log_msg)
    else:
        st.error(f"JavaScript execution error: {result}")
        if "debugLogs" in result:
            for log_msg in result["debugLogs"]:
                log.error("JS Debug: %s", log_msg)

    st.session_state.test_id = None

# ----------------------------------------------------------------------------
# Usage
# ----------------------------------------------------------------------------
#   $ pip install streamlit streamlit-javascript
#   $ streamlit run speed_test_app.py
# ----------------------------------------------------------------------------
