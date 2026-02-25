import streamlit as st
import pandas as pd
import psycopg2

# ---------------------------------------------------
# 1. Setup the Page
# ---------------------------------------------------
st.set_page_config(page_title="RIDE 1 COMMAND CENTER", layout="wide")

# ---------------------------------------------------
# 2. DB Helper Function
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
    st.metric("TOTAL INVENTORY VALUE", "$4.2M", "-$12,400 (Leak Detected)")
with col3:
    st.metric("ACCESSORY BLEED", "14 Items", "-$2,140")
with col4:
    st.metric("LAZY TECH ALERTS", "8", "Requires Review")

st.markdown("---")

# ---------------------------------------------------
# 5. LEAK DETECTOR (Forensic Analytics)
# ---------------------------------------------------
st.subheader("LEAK DETECTOR: SUSPICIOUS VARIANCE")
st.caption("Detecting negative variances, missing employee logs, or high-severity movements.")

leak_query = """
SELECT 
    id,
    part_number,
    description,
    quantity,
    employee_id,
    movement_type,
    location_bin,
    variance_amount,
    severity_level,
    timestamp
FROM receiving_log
WHERE 
    (variance_amount IS NOT NULL AND variance_amount < 0)
    OR (severity_level IN ('MEDIUM', 'HIGH'))
    OR (employee_id IS NULL)
    OR (employee_id = '')
ORDER BY timestamp DESC
LIMIT 50;
"""

leaks = get_data(leak_query)

if "Error" in leaks.columns:
    st.error("Leak detector query failed:")
    st.code(leaks["Error"].iloc[0])
elif leaks.empty:
    st.success("No suspicious movements detected. System is clean.")
else:
    st.warning(f"{len(leaks)} suspicious movement(s) detected. Review below.")

    display_cols = [
        "id", "part_number", "description", "employee_id",
        "movement_type", "variance_amount", "severity_level", "timestamp"
    ]
    display_cols = [c for c in display_cols if c in leaks.columns]
    st.dataframe(leaks[display_cols], use_container_width=True, hide_index=True)

    st.markdown("### Drill-Down: Click a Row to Investigate")

    for _, row in leaks.iterrows():
        ts = str(row.get("timestamp", "Unknown Time"))
        part = str(row.get("part_number", "Unknown Part"))
        emp = str(row.get("employee_id", "NO EMPLOYEE"))
        var = str(row.get("variance_amount", "N/A"))
        sev = str(row.get("severity_level", "UNKNOWN"))

        label = f"{ts}  |  Part: {part}  |  Employee: {emp}  |  Variance: {var}  |  Severity: {sev}"

        with st.expander(label):
            st.write("#### Full Event Record")
            st.dataframe(row.to_frame().T, use_container_width=True)

            part_number = row.get("part_number")
            if part_number:
                history_query = f"""
                SELECT 
                    timestamp,
                    employee_id,
                    movement_type,
                    quantity,
                    variance_amount,
                    location_bin,
                    severity_level
                FROM receiving_log
                WHERE part_number = '{part_number}'
                ORDER BY timestamp DESC
                LIMIT 30;
                """
                history = get_data(history_query)

                st.write("#### Movement History for This Part")
                if "Error" in history.columns:
                    st.error("Could not load history:")
                    st.code(history["Error"].iloc[0])
                elif history.empty:
                    st.info("No additional movement history found for this part.")
                else:
                    st.dataframe(history, use_container_width=True, hide_index=True)

                    if "quantity" in history.columns and len(history) > 1:
                        st.write("#### Quantity Trend")
                        chart = history.sort_values("timestamp")
                        st.line_chart(
                            chart.set_index("timestamp")["quantity"],
                            height=200
                        )

st.markdown("---")

# ---------------------------------------------------
# 6. ACCESSORY RADAR
# ---------------------------------------------------
st.subheader("ACCESSORY RADAR: HIGH-VELOCITY ITEMS")
c1, c2 = st.columns(2)

with c1:
    st.write("Top Selling Accessories (Demo)")
    chart_data = pd.DataFrame(
        {"Item": ["Shoei X-15", "Fox V3", "GoPro Hero 12"], "Sales": [12, 8, 15]}
    )
    st.bar_chart(chart_data.set_index("Item"))

with c2:
    st.write("Low Stock Alerts")
    st.warning("Shoei RF-1400 (Matte Black - Large) is low.")
    st.warning("Warn VRX 45 Winch is low.")

st.markdown("---")

# ---------------------------------------------------
# 7. AUDIT TRAIL
# ---------------------------------------------------
st.subheader("AUDIT TRAIL: RECENT MOVEMENTS")

audit_query = """
SELECT 
    part_number,
    description,
    quantity,
    employee_id,
    movement_type,
    variance_amount,
    severity_level,
    timestamp
FROM receiving_log
ORDER BY timestamp DESC
LIMIT 50;
"""

audit_data = get_data(audit_query)

if "Error" in audit_data.columns:
    st.error("Audit query failed:")
    st.code(audit_data["Error"].iloc[0])
else:
    st.dataframe(audit_data, use_container_width=True, hide_index=True)

    if "employee_id" in audit_data.columns and not audit_data.empty:
        st.write("### Employee Activity Summary")

        df = audit_data.copy()
        df["employee_id"] = df["employee_id"].fillna("UNKNOWN")

        summary = (
            df.groupby("employee_id")
            .agg(
                total_movements=("part_number", "count"),
                total_negative_variance=(
                    "variance_amount",
                    lambda x: x[x < 0].sum() if x.notna().any() else 0
                )
            )
            .reset_index()
        )

        st.dataframe(summary, use_container_width=True, hide_index=True)
