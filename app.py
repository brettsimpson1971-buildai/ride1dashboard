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

# 3. SIDEBAR - Stabilized Branding & Search
with st.sidebar:
    # Fixed width logo to prevent jumping
    st.image("https://cdn.abacus.ai/images/8f44384a-1116-4c71-b3e6-67356cf217cd.png", width=200)
    st.markdown("<​br>", unsafe_allow_html=True) # Spacer
    
    st.markdown("### DASHBOARD VIEW")
    view_mode = st.radio("Select View:", ["OPEN LEAKS (Active)", "RESOLVED CASES (Archive)"])
    
    st.markdown("---")
    st.markdown("### FORENSIC SEARCH")
    # Using a container to keep search fields stable
    search_container = st.container()
    with search_container:
        search_part = st.text_input("Search Part #:", placeholder="e.g. 99999-001")
        search_emp = st.text_input("Search Employee:", placeholder="e.g. TECH_42")

# 4. HEADER
st.title("🏁 RIDE 1: INVENTORY COMMAND CENTER")
st.markdown("---")

# 5. GOD VIEW (Mock KPIs for Stress Test)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("TOTAL PARTS ON HAND", "1,042,381", "+12% vs Last Week")
with col2:
    st.metric("TOTAL INVENTORY VALUE", "$4.2M", "-$12,400 (Leak Detected)")
with col3:
    st.metric("ACCESSORY BLEED", "14 Items", "-$2,140")
with col4:
    st.metric("LAZY TECH ALERTS", "8", "Requires Review")

st.markdown("---")

# 6. LEAK DETECTOR
st.subheader("🚨 LEAK DETECTOR: SUSPICIOUS VARIANCE")

# Build Query based on View Mode
if view_mode == "OPEN LEAKS (Active)":
    sql = "SELECT * FROM receiving_log WHERE ((variance_amount IS NOT NULL AND variance_amount < 0) OR (severity_level IN ('MEDIUM', 'HIGH')) OR (employee_id IS NULL) OR (employee_id = '')) AND (resolution_status = 'OPEN' OR resolution_status IS NULL) ORDER BY timestamp DESC LIMIT 100;"
else:
    sql = "SELECT * FROM receiving_log WHERE resolution_status NOT IN ('OPEN') AND resolution_status IS NOT NULL ORDER BY resolved_at DESC LIMIT 100;"

leaks = get_data(sql)

# Apply Sidebar Filters
if not leaks.empty and "Error" not in leaks.columns:
    if search_part:
        leaks = leaks[leaks['part_number'].astype(str).str.contains(search_part, case=False, na=False)]
    if search_emp:
        leaks = leaks[leaks['employee_id'].astype(str).str.contains(search_emp, case=False, na=False)]

if "Error" in leaks.columns:
    st.error("Database connection issue. Check your secrets.")
elif leaks.empty:
    st.success("No suspicious movements found. System is clean.")
else:
    # Color Coding Logic
    def color_severity(val):
        color = 'white'
        if val == 'HIGH': color = '#ff4b4b' # Red
        elif val == 'MEDIUM': color = '#ffa500' # Orange
        elif val == 'LOW': color = '#2e7d32' # Green
        return f'background-color: {color}; color: white; font-weight: bold'

    # Apply styling to the dataframe
    styled_leaks = leaks.style.applymap(color_severity, subset=['severity_level'])
    st.dataframe(styled_leaks, use_container_width=True, hide_index=True)
    
    st.markdown("### 🔍 DRILL-DOWN & VERDICTS")
    VERDICTS = ["-- Select Verdict --", "Legitimate Adjustment", "Human Error / Training Issue", "Suspicious / Under Watch", "Confirmed Theft", "Resolved with Note"]

    for _, row in leaks.iterrows():
        label = f"ID: {row['id']} | Part: {row['part_number']} | Var: {row['variance_amount']} | Emp: {row['employee_id']}"
        with st.expander(label):
            st.write("#### Event Details")
            st.write(row.to_frame().T)
            
            if view_mode == "OPEN LEAKS (Active)":
                st.markdown("---")
                st.write("#### VERDICT CENTER")
                v_choice = st.selectbox("Verdict:", VERDICTS, key=f"v_{row['id']}")
                v_note = st.text_input("Note:", key=f"n_{row['id']}")
                v_user = st.text_input("Your Name:", key=f"u_{row['id']}")
                
                if st.button("Submit Verdict", key=f"b_{row['id']}"):
                    if v_choice != "-- Select Verdict --" and v_user:
                        update_sql = "UPDATE receiving_log SET resolution_status = %s, resolution_note = %s, resolved_by = %s, resolved_at = %s WHERE id = %s;"
                        if run_command(update_sql, (v_choice, v_note, v_user, datetime.now(), int(row['id']))):
                            st.success("Case Closed. Refresh to update.")
                            st.balloons()
                    else:
                        st.warning("Verdict and Name are required.")
            else:
                st.info(f"Resolved by {row['resolved_by']} as {row['resolution_status']}")

st.markdown("---")

# 7. AUDIT TRAIL
st.subheader("🕵️ AUDIT TRAIL: ALL MOVEMENTS")
audit_data = get_data("SELECT * FROM receiving_log ORDER BY timestamp DESC LIMIT 50;")
if "Error" not in audit_data.columns:
    st.dataframe(audit_data, use_container_width=True, hide_index=True)
