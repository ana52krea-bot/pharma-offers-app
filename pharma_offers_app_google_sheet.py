import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="عروض المؤتمر",
    page_icon="💊",
    layout="wide"
)

DATA_FILE = "عروض المؤتمر 2026.xlsx"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz7dTqGUw95xDV2rVX6FbbcZM7H_LaJ-T83b1iYWYqrJ-Kq36gcFj3zD-kd-28jhsga/exec"

# =========================
# 🎨 CSS
# =========================
st.markdown("""
<style>
html, body {
    direction: rtl;
    text-align: right;
}

.custom-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    border: 2px solid #9ca3af;
}

.custom-table th {
    background: #2563eb;
    color: white;
    font-size: 22px;
    font-weight: 900;
    padding: 14px;
    text-align: center;
}

.custom-table td {
    font-size: 20px;
    font-weight: 900;
    padding: 14px;
    text-align: center;
    border: 1px solid #cbd5e1;
    color: #111827;
}

.custom-table tr:nth-child(even) td {
    background: #ffffff;
}

.custom-table tr:nth-child(odd) td {
    background: #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 📊 تحميل البيانات
# =========================
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)

    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    df = df.dropna(how="all")

    # 🔥 مهم جداً لتجنب الأخطاء
    df["offer_type"] = df["offer_type"].astype(str).fillna("").str.strip()
    df["offer_group"] = df["offer_group"].astype(str).fillna("").str.strip()

    return df


def clean(x):
    if pd.isna(x) or str(x).lower() in ["none", "nan", ""]:
        return ""
    return x


def format_value(x, col):
    x = clean(x)

    if x == "":
        return ""

    if isinstance(x, (int, float)):

        # نسبة
        if "حسم" in col or "discount" in col or "نسبة" in col:
            if 0 < x <= 1:
                return f"{x:.0%}"
            return f"{x}%"

        # رقم كبير
        if abs(x) >= 1000:
            return f"{x:,.0f}"

        return str(int(x))

    return str(x)


df = load_data()

if "page" not in st.session_state:
    st.session_state.page = "filters"

# تحديث
if st.button("🔄 تحديث البيانات"):
    st.cache_data.clear()
    st.rerun()

# =========================
# شاشة الفلاتر
# =========================
if st.session_state.page == "filters":

    st.title("💊 نظام عروض مؤتمر الصيادلة")

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

# =========================
# شاشة التفاصيل
# =========================
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
    # 🔥 جدول HTML
    # =========================
    headers = result.columns.tolist()
    rows_html = ""

    for _, row in result.iterrows():
        row_html = "<tr>"
        for col in headers:
            val = format_value(row[col], col)
            row_html += f"<td>{val}</td>"
        row_html += "</tr>"
        rows_html += row_html

    table_html = f"""
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

        submit = st.form_submit_button("تثبيت")

        if submit:
            if doctor == "" and address == "":
                st.warning("أدخل اسم أو عنوان")
            else:
                payload = {
                    "doctor_name": doctor,
                    "pharmacy_name": address,
                    "phone": phone,
                    "offer_type": selected_type,
                    "offer_group": selected_group,
                    "notes": notes
                }

                try:
                    r = requests.post(GOOGLE_SCRIPT_URL, json=payload)
                    if r.status_code == 200:
                        st.success("تم الحفظ ✅")
                    else:
                        st.error("خطأ بالحفظ")
                except:
                    st.error("فشل الاتصال")
