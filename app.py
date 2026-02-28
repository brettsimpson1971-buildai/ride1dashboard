import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# ---------- CONFIG ----------
st.set_page_config(page_title="ZAPTASK A.I. | COMMAND CENTER", layout="wide")

# ---------- LOGIN LOGIC ----------
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "ZAPTASK-RIDE1":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        # First run or incorrect password, show input for password.
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
        # Password correct.
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

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 FORENSIC SEARCH")
    search_part = st.sidebar.text_input("Search Part #:")

    # --- MAIN DASHBOARD ---
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
                employee_id, movement_type, location_bin, variance_amount, severity_level,
                resolution_status, resolution_note
            FROM receiving_log 
            WHERE resolution_status IS NULL OR resolution_status = 'Unresolved'
            ORDER BY timestamp DESC
        """, conn)

        total_parts = int(inv_stats['total_parts'][0]) if inv_stats['total_parts'][0] else 0
        total_skus = int(inv_stats['total_skus'][0]) if inv_stats['total_skus'][0] else 0
        est_value = float(inv_stats['est_value'][0]) if inv_stats['est_value'][0] else 0.0

        # Header
        col_logo, col_title = st.columns([1, 5])
        with col_logo:
            st.image("https://raw.githubusercontent.com/brettsimpson1971/ride1-dashboard/main/logo.png", width=100)
        with col_title:
            st.title("Forensic Audit & Loss Prevention")

        st.divider()

        # Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TOTAL PARTS ON HAND", f"{total_parts:,}", f"↑ {total_skus:,} SKUs Active")
        m2.metric("EST. INVENTORY VALUE", f"${est_value:,.2f}", "Avg $25/unit")
        m3.metric("ACCESSORY COUNT", f"{int(total_parts * 0.4):,}", "Items in Showroom")
        m4.metric("ACTIVE LEAKS", len(leaks_df), "Requires Verdict", delta_color="inverse")

        st.divider()

        # --- FORENSIC SEARCH ---
        if search_part:
            st.subheader(f"🔍 Search Results for: {search_part}")
            search_df = pd.read_sql("SELECT * FROM receiving_log WHERE part_number ILIKE %s ORDER BY timestamp DESC", conn, params=(f"%{search_part}%",))
            if not search_df.empty:
                st.dataframe(search_df, use_container_width=True)
            else:
                st.warning(f"No records found for: {search_part}")
            st.divider()

        # --- LEAK DETECTOR ---
        st.subheader("🚨 LEAK DETECTOR: SUSPICIOUS VARIANCE")
        if not leaks_df.empty:
            st.dataframe(leaks_df, use_container_width=True)
            
            st.subheader("🔍 DRILL-DOWN & VERDICTS")
            for index, row in leaks_df.iterrows():
                severity = row['severity_level'] if row['severity_level'] else "UNKNOWN"
                with st.expander(f"CASE #{row['id']} | {severity} | {row['part_number']} - {row['description']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Timestamp:** {row['timestamp']}")
                        st.write(f"**Employee ID:** {row['employee_id']}")
                        st.write(f"**Movement:** {row['movement_type']}")
                    with c2:
                        st.write(f"**Location:** {row['location_bin']}")
                        st.write(f"**Variance:** {row['variance_amount']}")
                        st.write(f"**Status:** {row['resolution_status']}")
                    
                    st.markdown("---")
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
                        """, (verdict, note, int(row['id'])))
                        conn.commit()
                        st.success("Verdict Logged.")
                        st.rerun()
        else:
            st.success("✅ No active leaks detected.")

        conn.close()
    except Exception as e:
        st.error(f"System Error: {e}")
