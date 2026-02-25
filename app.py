import streamlit as st
import pandas as pd
import psycopg2
import os

# 1. Setup the Page (Dark Mode / Wide)
st.set_page_config(page_title="RIDE 1 COMMAND CENTER", layout="wide")

# 2. Connect to the Zaptask Engine
def get_data(query):
    try:
    try:
    conn = psycopg2.connect(
        host=st.secrets['DB_HOST'],
        database=st.secrets['DB_NAME'],
        user=st.secrets['DB_USER'],
        password=st.secrets['DB_PASSWORD'],
        port=st.secrets['DB_PORT']
    )
    df = pd.read_sql(query, conn)
    conn.close()
    return df
    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})

# 3. THE DASHBOARD HEADER
st.title("🏁 RIDE 1: INVENTORY COMMAND CENTER")
st.markdown("---")

# 4. THE "GOD VIEW" (Top Row Metrics)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("TOTAL PARTS ON HAND", "1,042,381", "+12% vs Last Week")
with col2:
    st.metric("TOTAL INVENTORY VALUE", "$4.2M", "-$12,400 (Leak Detected)")
with col3:
    st.metric("ACCESSORY BLEED", "14 Items", "-$2,140", delta_color="inverse")
with col4:
    st.metric("LAZY TECH ALERTS", "8", "Requires Review", delta_color="off")

st.markdown("---")

# 5. THE "LEAK DETECTOR" (Red Flag Panel)
st.subheader("🚨 LEAK DETECTOR: SUSPICIOUS VARIANCE")
st.error("WARNING: The following high-value accessories have unaccounted movement.")
leak_query = "SELECT part_number, description, category, initial_qty FROM parts_master LIMIT 5;"
leaks = get_data(leak_query)
st.table(leaks)

st.markdown("---")

# 6. ACCESSORY RADAR (Helmets, Gear, Winches)
st.subheader("📦 ACCESSORY RADAR: HIGH-VELOCITY ITEMS")
acc_col1, acc_col2 = st.columns(2)

with acc_col1:
    st.write("### Top Selling Accessories")
    chart_data = pd.DataFrame({'Item': ['Shoei X-15', 'Fox V3', 'GoPro Hero 12'], 'Sales': [12, 8, 15]})
    st.bar_chart(chart_data.set_index('Item'))

with acc_col2:
    st.write("### Low Stock / Reorder Alerts")
    st.warning("Reorder Required: Shoei RF-1400 (Matte Black - Large)")
    st.warning("Reorder Required: Warn VRX 45 Winch")

st.markdown("---")

# 7. THE "LAZY EMPLOYEE" AUDIT TRAIL
st.subheader("🕵️ AUDIT TRAIL: RECENT MOVEMENTS")
audit_query = "SELECT * FROM receiving_log ORDER BY timestamp DESC LIMIT 5;"
audit_data = get_data(audit_query)
st.dataframe(audit_data, use_container_width=True)
