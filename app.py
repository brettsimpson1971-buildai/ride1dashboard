import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# ---------- CONFIG ----------
st.set_page_config(page_title="ZAPTASK A.I. | RIDE 1 VENTURE", layout="wide")

# ---------- PERSISTENT LOGIN ----------
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    def password_entered():
        if st.session_state["password"] == "ZAPTASK-RIDE1":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔐 ZAPTASK A.I. SECURE GATEWAY")
        st.text_input("Enter Admin Password:", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Invalid Password.")
        st.info("Unauthorized access is strictly prohibited.")
        return False
    return True

if check_password():
    # ---------- DB CONNECTION ----------
    def get_conn():
        return psycopg2.connect(st.secrets["postgres"]["url"])

    # ---------- UNIFIED NAVIGATION ----------
    st.sidebar.image("https://raw.githubusercontent.com/brettsimpson1971/ride1-dashboard/main/logo.png", width=200)
    st.sidebar.title("ZAPTASK A.I. SYSTEM")
    
    page = st.sidebar.radio("Navigate:", ["📊 Command Center", "📦 Data Operations", "⚙️ System Settings"])
    
    if st.sidebar.button("🔒 LOGOUT"):
        st.session_state["password_correct"] = False
        st.rerun()

    # ==========================================
    # PAGE 1: COMMAND CENTER (THE DASHBOARD)
    # ==========================================
    if page == "📊 Command Center":
        st.title("Forensic Audit & Loss Prevention")
        try:
            conn = get_conn()
            inv_stats = pd.read_sql("SELECT COUNT(*) as total_skus, SUM(quantity_on_hand) as total_parts, SUM(quantity_on_hand * 25) as est_value FROM inventory", conn)
            leaks_df = pd.read_sql("SELECT * FROM receiving_log WHERE resolution_status IS NULL OR resolution_status = 'Unresolved' ORDER BY timestamp DESC", conn)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("TOTAL PARTS", f"{int(inv_stats['total_parts'][0] or 0):,}", f"{int(inv_stats['total_skus'][0] or 0):,} SKUs")
            m2.metric("EST. VALUE", f"${(inv_stats['est_value'][0] or 0):,.2f}")
            m3.metric("ACCESSORIES", f"{int((inv_stats['total_parts'][0] or 0) * 0.4):,}")
            m4.metric("ACTIVE LEAKS", len(leaks_df), delta_color="inverse")

            st.subheader("🚨 LEAK DETECTOR")
            if not leaks_df.empty:
                st.dataframe(leaks_df, use_container_width=True)
                for index, row in leaks_df.iterrows():
                    with st.expander(f"CASE #{row['id']} | {row['part_number']}"):
                        st.write(f"**Employee:** {row['employee_id']} | **Variance:** {row['variance_amount']}")
                        verdict = st.selectbox("Verdict:", ["Unresolved", "Theft", "Error", "Damaged"], key=f"v_{row['id']}")
                        if st.button("SUBMIT", key=f"b_{row['id']}"):
                            cur = conn.cursor()
                            cur.execute("UPDATE receiving_log SET resolution_status = %s, resolved_at = NOW() WHERE id = %s", (verdict, row['id']))
                            conn.commit()
                            st.rerun()
            else:
                st.success("✅ No active leaks detected.")
            conn.close()
        except Exception as e:
            st.error(f"Dashboard Error: {e}")

    # ==========================================
    # PAGE 2: DATA OPERATIONS (THE UPLOADER)
    # ==========================================
    elif page == "📦 Data Operations":
        st.title("Data Operations & Uploads")
        op = st.selectbox("Select Upload Type:", ["Daily Activity Log (Sales/Receiving)", "Master Inventory Update"])
        
        uploaded_file = st.file_uploader("Choose CSV File", type="csv")
        if uploaded_file:
            if st.button("🚀 START IMPORT"):
                try:
                    conn = get_conn()
                    cur = conn.cursor()
                    if op == "Master Inventory Update":
                        cur.execute("TRUNCATE TABLE inventory;")
                    
                    reader = pd.read_csv(uploaded_file, chunksize=50000)
                    for chunk in reader:
                        if op == "Master Inventory Update":
                            execute_values(cur, "INSERT INTO inventory (part_number, quantity_on_hand, location_bin) VALUES %s ON CONFLICT (part_number) DO UPDATE SET quantity_on_hand = EXCLUDED.quantity_on_hand", chunk[['part_number', 'quantity_on_hand', 'location_bin']].values.tolist())
                        else:
                            execute_values(cur, "INSERT INTO receiving_log (part_number, description, quantity, employee_id, movement_type, location_bin, variance_amount, severity_level, timestamp) VALUES %s", chunk[['part_number', 'description', 'quantity', 'employee_id', 'movement_type', 'location_bin', 'variance_amount', 'severity_level', 'timestamp']].values.tolist())
                        conn.commit()
                    st.success("Import Complete!")
                    conn.close()
                except Exception as e:
                    st.error(f"Upload Error: {e}")

    # ==========================================
    # PAGE 3: SYSTEM SETTINGS (NUKE)
    # ==========================================
    elif page == "⚙️ System Settings":
        st.title("System Administration")
        if st.button("☢️ WIPE ALL ACTIVITY LOGS"):
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("TRUNCATE TABLE receiving_log;")
            conn.commit()
            st.warning("Activity logs cleared.")
            conn.close()
