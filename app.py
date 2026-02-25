import streamlit as st
import pandas as pd
import psycopg2

# 1. Setup the Page
st.set_page_config(page_title="RIDE 1 COMMAND CENTER", layout="wide")

# 2. DB Helper
def get_data(query):
    try:
        conn = psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            port=st.secrets["DB_PORT"],
        )
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})


# 3. HEADER
st.title("🏁 RIDE 1: INVENTORY COMMAND CENTER")
st.markdown("---")

# 4. GOD VIEW (Top KPIs) – still mostly mock KPIs for now
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("TOTAL PARTS ON HAND", "1,042,381", "+12% vs Last Week")
with col2:
    st.metric("TOTAL INVENTORY VALUE", "\$4.2M", "-\$12,400 (Leak Detected)")
with col3:
    st.metric("ACCESSORY BLEED", "14 Items", "-\$2,140", delta_color="inverse")
with col4:
    st.metric("LAZY TECH ALERTS", "8", "Requires Review", delta_color="off")

st.markdown("---")

# ============================================
# 5. LEAK DETECTOR - FORENSIC VIEW
# ============================================
st.subheader("🚨 L
