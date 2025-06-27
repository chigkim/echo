import os
import gc
import uuid
import logging

import streamlit as st

__version__ = "0.0.5" # Incrementing version for this significant change

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

    js_code = f"""(async () => {{
        const SIZE = {size_bytes};
        const start = performance.now();
        console.log('▶️ Speed-test started —', SIZE/1024/1024, 'MB');

        try {{
            // —— DOWNLOAD (simulated: client-side data generation) ——
            const dlStart = performance.now();
            const dlBuf = new Uint8Array(SIZE);
            // Simulate data generation (e.g., fill with random values)
            for (let i = 0; i < SIZE; i++) {{
                dlBuf[i] = Math.floor(Math.random() * 256);
            }}
            const dlEnd = performance.now();
            const dlTimeS = (dlEnd - dlStart) / 1000;
            const dlMbps = (SIZE * 8) / dlTimeS / 1e6;
            console.log('⬇️ Download (simulated)', SIZE, 'bytes in', dlTimeS.toFixed(2), 's →', dlMbps.toFixed(2), 'Mbps');

            // —— UPLOAD (client to Streamlit server via st_javascript) ——
            // The actual upload time will be measured by Streamlit's internal communication
            // We pass the generated data back to Python

            const totalTime = (performance.now() - start) / 1000;
            console.log('🏁 Speed-test complete in', totalTime.toFixed(2), 's');

            return {{
                download: dlMbps.toFixed(2),
                upload: null, // Upload speed will be calculated on Python side
                totalTime: totalTime.toFixed(2),
                dlTime: dlTimeS.toFixed(2),
                ulTime: null, // Upload time will be calculated on Python side
                payload: Array.from(dlBuf) // Pass the data back to Python
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
        # Calculate upload speed on Python side
        payload_size_bytes = len(result.get('payload', []))
        # Assuming totalTime includes both download simulation and upload transfer
        # For a more accurate ulTime, we would need a separate timer in JS for the actual transfer
        # For now, we'll use the totalTime and subtract dlTime for a rough estimate
        ul_time_s = float(result['totalTime']) - float(result['dlTime'])
        ul_mbps = (payload_size_bytes * 8) / ul_time_s / 1e6 if ul_time_s > 0 else 0

        st.metric("Total time", f"{result['totalTime']} s")
        col1, col2 = st.columns(2)
        col1.metric("Download (simulated)", f"{result['download']} Mbps", delta=f"{result['dlTime']} s")
        col2.metric("Upload (Streamlit transfer)", f"{ul_mbps:.2f} Mbps", delta=f"{ul_time_s:.2f} s")
        log.info(
            "Speed-test complete (v%s): ↓ %s Mbps (%s s), ↑ %s Mbps (%s s), total time %s s, Payload Size: %s bytes",
            __version__,
            result['download'],
            result['dlTime'],
            f"{ul_mbps:.2f}",
            f"{ul_time_s:.2f}",
            result['totalTime'],
            payload_size_bytes,
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
