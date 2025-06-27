(async () => {
        const SIZE = __SIZE_PLACEHOLDER__;
        const start = performance.now();
        const debugLogs = [];
        debugLogs.push(`▶️ Speed-test started — ${SIZE/1024/1024} MB`);

        try {
            debugLogs.push('JS: Starting download simulation...');
            // —— DOWNLOAD (simulated: client-side data generation) ——
            const dlStart = performance.now();
            const dlBuf = new Uint8Array(SIZE);
            // Simulate data generation (e.g., fill with random values)
            for (let i = 0; i < SIZE; i++) {
                dlBuf[i] = Math.floor(Math.random() * 256);
            }
            const dlEnd = performance.now();
            const dlTimeS = (dlEnd - dlStart) / 1000;
            const dlMbps = (SIZE * 8) / dlTimeS / 1e6;
            debugLogs.push(`⬇️ Download (simulated) ${SIZE} bytes in ${dlTimeS.toFixed(2)} s → ${dlMbps.toFixed(2)} Mbps`);

            // —— UPLOAD (client to Streamlit server via st_javascript) ——
            // The actual upload time will be measured by Streamlit's internal communication
            // We are temporarily NOT passing the large payload back to Python to debug the '0' return.
            debugLogs.push('JS: Preparing return value (without payload)...');
            const totalTime = (performance.now() - start) / 1000;
            debugLogs.push(`🏁 Speed-test complete in ${totalTime.toFixed(2)} s`);

            return {
                download: dlMbps.toFixed(2),
                upload: null, // Upload speed will be calculated on Python side
                totalTime: totalTime.toFixed(2),
                dlTime: dlTimeS.toFixed(2),
                ulTime: null, // Upload time will be calculated on Python side
                debugLogs: debugLogs
            };
        } catch (err) {
            debugLogs.push(`❌ JS error: ${err.toString()}`);
            return { error: err.toString(), debugLogs: debugLogs };
        }
    })();