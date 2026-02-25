import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# ---------------------------------------------------
# 1. Setup the Page
# ---------------------------------------------------
st.set_page_config(page_title="RIDE 1 COMMAND CENTER", layout="wide")

# ---------------------------------------------------
# 2. DB Helper Functions
# ---------------------------------------------------
def get_data(query):
    try:
        conn = psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            port=st.secrets["DB_PORT"]
        )
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})


def run_command(query, params=None):
    try:
        conn = psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            port=st.secrets["DB_PORT"]
        )
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False


# ---------------------------------------------------
# 3. HEADER
# ---------------------------------------------------
st.title("RIDE 1: INVENTORY COMMAND CENTER")
st.markdown("---")

# ---------------------------------------------------
# 4. GOD VIEW (Top-level KPIs)
# ---------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("TOTAL PARTS ON HAND", "1,042,381", "+12% vs Last Week")
with col2:
    st.metric("TOTAL INVENTORY VALUE", "\$4.2M", "-\$12,400 (Leak Detected)")
with col3:
    st.metric("ACCESSORY BLEED", "14 Items", "-\$2,140")
with col4:
    st.metric("LAZY TECH ALERTS", "8", "Requires Review")

st.markdown("---")

# ---------------------------------------------------
# 5. LEAK DETECTOR (Forensic Analytics + Resolution)
# ---------------------------------------------------
st.subheader("LEAK DETECTOR: SUSPICIOUS VARIANCE")
st.caption("Detecting negative variances, missing employee logs, or high-severity movements.")

# Toggle between Open and Resolved
view_mode = st.radio(
    "View Mode:",
    ["OPEN LEAKS (Active)", "RESOLVED CASES (Archive)"],
    horizontal=True
)

if view_mode == "OPEN LEAKS (Active)":
    leak_query = """
    SELECT 
        id,
        part_number,
        description,
        quantity,
        employee_id,
        movement_type,
        location_bin,
