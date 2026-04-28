import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="عروض المؤتمر",
    page_icon="💊",
    layout="wide"
)

DATA_FILE = "عروض المؤتمر 2026.xlsx"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzNnX--BElICEiGzpUV0mXC-9B1EM5NItWfvoGjV9AMVlZ1oeir39IlhAd_yvaLyCBR/exec"

USERS = {
    "Manar": "123",
    "Ruba": "0123",
    "Alaa": "1234"
}

st.markdown("""
<style>
html, body {
    direction: rtl;
    text-align: right;
}

.summary-box {
    background: #ffffff;
    color: #111827;
    border-radius: 16px;
    padding: 12px;
    border: 2px solid #2563eb;
    text-align: center;
    font-weight: 900;
    margin-bottom: 14px;
}

.summary-title {
    font-size: 15px;
    color: #2563eb;
    margin-bottom: 6px;
}

.summary-value {
    font-size: 24px;
    color: #111827;
}

.table-wrapper {
    max-height: none;
    overflow: visible;
    border: 2px solid #9ca3af;
    margin-top: 18px;
}

.custom-table {
    width: 100%;
    border-collapse: collapse;
}

.custom-table thead th {
    position: sticky;
    top: 0;
    z-index: 2;
    background: #2563eb;
    color: white;
    font-size: 18px;
    font-weight: 900;
    padding: 8px;
    text-align: center;
    border: 1px solid #9ca3af;
}

.custom-table td {
    font-size: 17px;
    font-weight: 700;
    padding: 7px;
    text-align: center;
    border: 1px solid #cbd5e1;
    color: #111827;
    line-height: 1.25;
}

.custom-table tr:nth-child(even) td {
    background: #ffffff;
}

.custom-table tr:nth-child(odd) td {
    background: #e5e7eb;
}

.custom-table tr:hover td {
    background: #dbeafe;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    df = df.dropna(how="all")

    df["offer_type"] = df["offer_type"].astype(str).fillna("").str.strip()
    df["offer_group"] = df["offer_group"].astype(str).fillna("").str.strip()

    return df


def clean(x):
    if pd.isna(x) or str(x).lower() in ["none", "nan", "nat", ""]:
        return ""
    return x


def format_value(x, col_name=""):
    x = clean(x)

    if x == "":
        return ""

    percent_cols = ["حسم", "discount", "نسبة", "العرض"]

    if isinstance(x, (int, float)):
        if any(word in col_name for word in percent_cols):
            if 0 < x <= 1:
                return f"{x:.0%}"
            return f"{x}%"

        if float(x).is_integer():
            if abs(x) >= 1000:
                return f"{x:,.0f}"
            return f"{x:.0f}"

        return f"{x:,.2f}"

    return str(x)


def is_summary_row(row):
    text_cols = ["العرض_و_الحسم", "product", "المستحضر", "الصنف"]
    has_product_text = False

    for col in text_cols:
        if col in row.index:
            value = clean(row[col])
            if value != "" and not isinstance(value, (int, float)):
                has_product_text = True

    return not has_product_text


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "employee" not in st.session_state:
    st.session_state.employee = ""

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")

    username = st.selectbox("USER", list(USERS.keys()))
    password = st.text_input("password", type="password")

    if st.button("دخول", use_container_width=True):
        if USERS.get(username) == password:
            st.session_state.logged_in = True
            st.session_state.employee = username
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")

    st.stop()


df = load_data()

if "page" not in st.session_state:
    st.session_state.page = "filters"

if st.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()

st.write(f"👤 USER : **{st.session_state.employee}**")

if st.button("تسجيل خروج"):
    st.session_state.logged_in = False
    st.session_state.employee = ""
    st.session_state.page = "filters"
    st.rerun()


if st.session_state.page == "filters":

    st.title("💊 2026 عروض مؤتمر الصيادلة")

    col1, col2 = st.columns(2)

    with col1:
        offer_type = st.selectbox(
            "نوع العرض",
            sorted([x for x in df["offer_type"].unique() if x != ""])
        )

    filtered = df[df["offer_type"] == offer_type]

    with col2:
        offer_group = st.selectbox(
            "مجموعة العرض",
            sorted([x for x in filtered["offer_group"].unique() if x != ""])
        )

    if st.button("عرض التفاصيل", use_container_width=True):
        st.session_state.selected_type = offer_type
        st.session_state.selected_group = offer_group
        st.session_state.page = "details"
        st.rerun()


else:

    selected_type = st.session_state.selected_type
    selected_group = st.session_state.selected_group

    result = df[
        (df["offer_type"] == selected_type) &
        (df["offer_group"] == selected_group)
    ].copy()

    result = result.fillna("")
    result = result.loc[:, ~result.columns.str.contains("unnamed", case=False)]

    st.subheader(f"💊 {selected_type} / {selected_group}")

    if st.button("⬅️ رجوع"):
        st.session_state.page = "filters"
        st.rerun()

    st.divider()

    # =========================
    # ملخص القيم المالية
    # =========================
    summary_row = result.iloc[0]

    summary_items = []

    for col in result.columns:
        if col in ["offer_type", "offer_group"]:
            continue

        value = clean(summary_row[col])

        if value != "":
            summary_items.append((col, format_value(value, col)))

    if summary_items:
        st.markdown("### 💰 ملخص العرض")

        cols = st.columns(min(len(summary_items), 4))

        for i, (label, value) in enumerate(summary_items):
            with cols[i % len(cols)]:
                st.markdown(f"""
                <div class="summary-box">
                    <div class="summary-title">{label}</div>
                    <div class="summary-value">{value}</div>
                </div>
                """, unsafe_allow_html=True)

    # =========================
    # جدول التفاصيل
    # =========================
    table_result = result.copy()

    if len(table_result) > 1 and is_summary_row(table_result.iloc[0]):
        table_result = table_result.iloc[1:].copy()

    # إخفاء الأعمدة غير المطلوبة من الجدول
    table_result = table_result.drop(
        columns=[
            "offer_type",
            "offer_group",
            "عدد_النقاط"
        ],
        errors="ignore"
    )

    # إخفاء أي عمود يحتوي كلمة نقاط احتياطياً
    table_result = table_result.drop(
        columns=[col for col in table_result.columns if "نقاط" in col or "points" in col.lower()],
        errors="ignore"
    )

    headers = table_result.columns.tolist()
    rows_html = ""

    for _, row in table_result.iterrows():
        row_html = "<tr>"
        for col in headers:
            value = format_value(row[col], col)
            row_html += f"<td>{value}</td>"
        row_html += "</tr>"
        rows_html += row_html

    table_html = f"""
<div class="table-wrapper">
<table class="custom-table">
<thead>
<tr>
{''.join([f"<th>{col}</th>" for col in headers])}
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>
"""

    st.markdown(table_html, unsafe_allow_html=True)

    st.divider()
    st.subheader("تثبيت العرض")

    with st.form("form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            doctor = st.text_input("اسم الدكتور / الصيدلي")

        with c2:
            address = st.text_input("العنوان")

        with c3:
            phone = st.text_input("رقم الهاتف")

        notes = st.text_area("ملاحظات")

        submit = st.form_submit_button("تثبيت", use_container_width=True)

        if submit:
            if doctor == "" and address == "":
                st.warning("أدخل اسم أو عنوان")
            else:
                payload = {
                    "employee_name": st.session_state.employee,
                    "doctor_name": doctor,
                    "pharmacy_name": address,
                    "phone": phone,
                    "offer_type": selected_type,
                    "offer_group": selected_group,
                    "notes": notes
                }

                try:
                    r = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=15)
                    if r.status_code == 200:
                        st.success(f"تم الحفظ باسم الموظف {st.session_state.employee} ✅")
                    else:
                        st.error("خطأ بالحفظ")
                except Exception as e:
                    st.error(f"فشل الاتصال: {e}")
