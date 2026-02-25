import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# 1. Setup the Page
st.set_page_config(page_title="RIDE 1 COMMAND CENTER", layout="wide")

# 2. DB Helper Functions
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

# 3. SIDEBAR
with st.sidebar:
    st.markdown("### 🔍 FORENSIC SEARCH")
    search_part = st.text_input("Search Part #:", placeholder="e.g. 99999-001")
    search_emp = st.text_input("Search Employee:", placeholder="e.g. TECH_42")
    st.markdown("---")
    st.markdown("### DASHBOARD VIEW")
    view_mode = st.radio("Select View:", ["OPEN LEAKS (Active)", "RESOLVED CASES (Archive)"])
    st.markdown("---")
    st.image("https://cdn.abacus.ai/images/8f44384a-1116-4c71-b3e6-67356cf217cd.png", use_container_width=True)
    st.caption("Ride 1 Motorsports Inventory Control")

# 4. HEADER
st.title("🏁 RIDE 1: INVENTORY COMMAND CENTER")
st.markdown("---")

# 5. LIVE KPI ENGINE
try:
    inv_stats = get_data("SELECT COUNT(*) AS total_skus, COALESCE(SUM(quantity_on_hand),0) AS total_qty FROM inventory;")
    total_skus = int(inv_stats["total_skus"].iloc[0] or 0)
    total_parts = int(inv_stats["total_qty"].iloc[0] or 0)

    acc_stats = get_data("SELECT COUNT(*) AS acc_count FROM inventory WHERE part_number LIKE 'ACC%';")
    total_accessories = int(acc_stats["acc_count"].iloc[0] or 0)

    leak_stats = get_data("SELECT COUNT(*) AS leak_count FROM receiving_log WHERE (resolution_status = 'OPEN' OR resolution_status IS NULL);")
    open_leaks = int(leak_stats["leak_count"].iloc[0] or 0)
except:
    total_skus, total_parts, total_accessories, open_leaks = 0, 0, 0, 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("TOTAL PARTS ON HAND", f"{total_parts:,}", f"{total_skus:,} SKUs Active")
with col2:
    st.metric("LIVE INVENTORY VALUE", "CALCULATING...", f"Tracking {total_skus:,} Items")
with col3:
    st.metric("ACCESSORY COUNT", f"{total_accessories:,}", "Items in Showroom")
with col4:
    st.metric("ACTIVE LEAKS", open_leaks, "Requires Verdict" if open_leaks > 0 else "System Clean")

st.markdown("---")

# 6. LEAK DETECTOR
st.subheader("🚨 LEAK DETECTOR: SUSPICIOUS VARIANCE")
sql = "SELECT * FROM receiving_log WHERE ((variance_amount < 0) OR (severity_level IN ('MEDIUM', 'HIGH')) OR (employee_id IS NULL) OR (employee_id = '')) "
if view_mode == "OPEN LEAKS (Active)":
    sql += "AND (resolution_status = 'OPEN' OR resolution_status IS NULL) "
else:
    sql += "AND (resolution_status NOT IN ('OPEN') AND resolution_status IS NOT NULL) "
sql += "ORDER BY timestamp DESC LIMIT 100;"

leaks = get_data(sql)

if not leaks.empty and "Error" not in leaks.columns:
    if search_part: leaks = leaks[leaks["part_number"].astype(str).str.contains(search_part, case=False)]
    if search_emp: leaks = leaks[leaks["employee_id"].astype(str).str.contains(search_emp, case=False)]

    def color_severity(val):
        color = "#ff4b4b" if val == "HIGH" else "#ffa500" if val == "MEDIUM" else "#2e7d32"
        return f"background-color: {color}; color: white; font-weight: bold"

    st.dataframe(leaks.style.applymap(color_severity, subset=["severity_level"]), use_container_width=True, hide_index=True)

    st.markdown("### 🔍 DRILL-DOWN & VERDICTS")
    VERDICTS = ["-- Select Verdict --", "Legitimate Adjustment", "Human Error / Training", "Suspicious / Under Watch", "Confirmed Theft", "Resolved with Note"]
    for _, row in leaks.iterrows():
        with st.expander(f"ID: {row['id']} | Part: {row['part_number']} | Var: {row['variance_amount']}"):
            st.write(row.to_frame().T)
            if view_mode == "OPEN LEAKS (Active)":
                v_col1, v_col2, v_col3 = st.columns(3)
                v_choice = v_col1.selectbox("Verdict:", VERDICTS, key=f"v_{row['id']}")
                v_note = v_col2.text_input("Note:", key=f"n_{row['id']}")
                v_user = v_col3.text_input("Your Name:", key=f"u_{row['id']}")
                if st.button("Submit Verdict", key=f"b_{row['id']}"):
                    if v_choice != "-- Select Verdict --" and v_user:
                        run_command("UPDATE receiving_log SET resolution_status=%s, resolution_note=%s, resolved_by=%s, resolved_at=%s WHERE id=%s", (v_choice, v_note, v_user, datetime.now(), int(row['id'])))
                        st.success("Resolved!")
                        st.rerun()
            else:
                st.info(f"Resolved by {row['resolved_by']} as {row['resolution_status']}")

st.markdown("---")
st.subheader("🕵️ AUDIT TRAIL: ALL MOVEMENTS")
audit_data = get_data("SELECT * FROM receiving_log ORDER BY timestamp DESC LIMIT 50;")
if "Error" not in audit_data.columns:
    st.dataframe(audit_data, use_container_width=True, hide_index=True)
