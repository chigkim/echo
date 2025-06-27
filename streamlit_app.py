import streamlit as st

def main():
    echo = st.Page("echo.py", title="Echo")
    speed = st.Page("speed.py", title="Speed")
    pg = st.navigation([speed, echo])
    pg.run()

if __name__ == "__main__":
    main()
