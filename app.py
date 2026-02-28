import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# ---------- CONFIG ----------
st.set_page_config(page_title="ZAPTASK A.I. | COMMAND CENTER", layout="wide")

# ---------- LOGIN ----------
def check_password():
    def password_entered():
        if st.session_state["password"] == "ZAPTASK-RIDE1":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.titl
