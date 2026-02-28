import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime

# ---------- CONFIG & SECRETS ----------
st.set_page_config(page_title="ZAPTASK A.I. | COMMAND CENTER", layout="wide")

# Simple Login Logic
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "ZAPTASK-RIDE1":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.title("🔐 ZAPTASK A.I. SECURE GATEWAY")
        st.text_input(
            "Enter Admin Password to Access Ride 1 Command Center:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Invalid Password. Access Denied.")
        st.info("Unauthorized access is strictly prohibited and monitored.")
        return False
    else:
        return True

if check_password():
    # ---------- EVERYTHING BELOW ONLY RUNS IF LOGGED IN ----------

    def get_conn():
        return psycopg2.connect(st.secrets["postgres"]["url"])

    # Sidebar & Logout
    st.sidebar.image("https://raw.githubusercontent.com/brettsimpson1971/ride1-dashboard/main/logo.png", width=200)
    st.sidebar.title("COMMAND CENTER")
    if st.sidebar.button("🔒 LOGOUT"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- DATA LOADING ---
    try:
        conn = get_conn()
        
        # Metrics
        inv_stats = pd.read_sql("""
            SELECT 
                COUNT(*) as total_skus,
                SUM(quantity_on_hand) as total_parts,
                SUM(quantity_on_hand * 25) as est_value
            FROM inventory
        """, conn)
        
        # Leak Detection Query
        leaks_df = pd.read_sql("""
            SELECT 
                id, part_number, description, quantity, timestamp, 
                employee_id, movement_type, location_bin, variance_amount, severity_level
            FROM receiving_log 
            WHERE resolution_status IS NULL OR resolution_status = 'Unresolved'
            ORDER BY timestamp DESC
        """, conn)

        # --- UI HEADER ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("TOTAL PARTS ON HAND", f"{int(inv_stats['total_parts'][0]):,}", f"↑ {int(inv_stats['total_skus'][0]):,} SKUs Active")
        col2.metric("EST. INVENTORY VALUE", f"${inv_stats['est_value'][0]:,.2f}", "Avg $25/unit")
        col3.metric("ACCESSORY COUNT", f"{int(inv_stats['total_parts'][0] * 0.4):,}", "Items in Showroom")
        col4.metric("ACTIVE LEAKS", len(leaks_df), "Requires Verdict", delta_color="inverse")

        st.divider()

        # --- LEAK DETECTOR ---
        st.subheader("🚨 LEAK DETECTOR: SUSPICIOUS VARIANCE")
        if not leaks_df.empty:
            st.dataframe(leaks_df, use_container_width=True)
            
            st.subheader("🔍 DRILL-DOWN & VERDICTS")
            for index, row in leaks_df.iterrows():
                with st.expander(f"CASE #{row['id']}: {row['part_number']} - {row['description']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Timestamp:** {row['timestamp']}")
                        st.write(f"**Employee ID:** {row['employee_id']}")
                        st.write(f"**Movement:** {row['movement_type']}")
                    with c2:
                        st.write(f"**Location:** {row['location_bin']}")
                        st.write(f"**Variance:** {row['variance_amount']}")
                        st.write(f"**Severity:** {row['severity_level']}")
                    
                    # Verdict System
                    verdict = st.selectbox("Set Forensic Verdict:", 
                        ["Unresolved", "Confirmed Theft", "Paperwork Error", "Misplaced Item", "Damaged/Scrapped"],
                        key=f"v_{row['id']}")
                    
                    note = st.text_area("Forensic Notes:", key=f"n_{row['id']}")
                    
                    if st.button("SUBMIT VERDICT", key=f"b_{row['id']}"):
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE receiving_log 
                            SET resolution_status = %s, resolution_note = %s, resolved_at = NOW()
                            WHERE id = %s
                        """, (verdict, note, row['id']))
                        conn.commit()
                        st.success("Verdict Logged. Refreshing...")
                        st.rerun()
        else:
            st.success("✅ No active leaks detected in the current cycle.")

        conn.close()
    except Exception as e:
        st.error(f"System Error: {e}")
