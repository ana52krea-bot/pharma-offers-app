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
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
}
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
}
.hero {
    background: linear-gradient(135deg, #2563eb, #0f766e);
    border-radius: 25px;
    padding: 25px;
    margin-bottom: 20px;
    color: white;
}
.hero-title {
    font-size: 34px;
    font-weight: bold;
}
.section-title {
    color: white;
    font-size: 22px;
    margin: 20px 0;
}
.offer-box {
    background: white;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
.offer-table {
    width: 100%;
    border-collapse: collapse;
}
.offer-table th {
    background: #f1f5f9;
    padding: 10px;
    color: #0f172a;
}
.offer-table td {
    padding: 10px;
    border-bottom: 1px solid #e2e8f0;
    color: #0f172a;
}
.badge {
    background: #dbeafe;
    color: #1d4ed8;
    padding: 5px 10px;
    border-radius: 999px;
    display: inline-block;
    margin-bottom: 10px;
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

    df["offer_type"] = df["offer_type"].astype(str)
    df["offer_group"] = df["offer_group"].astype(str)

    return df


def clean(v):
    if pd.isna(v) or str(v).lower() in ["none", "nan"]:
        return ""
    return str(v)


def get_val(row, cols):
    for c in cols:
        if c in row:
            val = clean(row[c])
            if val != "":
                return val
    return ""


df = load_data()

if "page" not in st.session_state:
    st.session_state.page = "filters"

# =========================
# 🔄 تحديث
# =========================
if st.button("🔄 تحديث"):
    st.cache_data.clear()
    st.rerun()

# =========================
# 🟢 الفلاتر
# =========================
if st.session_state.page == "filters":

    st.markdown("""
    <div class="hero">
        <div class="hero-title">💊 نظام عروض مؤتمر الصيادلة</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        offer_type = st.selectbox("نوع العرض", df["offer_type"].unique())

    filtered = df[df["offer_type"] == offer_type]

    with col2:
        offer_group = st.selectbox("مجموعة العرض", filtered["offer_group"].unique())

    if st.button("عرض التفاصيل"):
        st.session_state.selected_type = offer_type
        st.session_state.selected_group = offer_group
        st.session_state.page = "details"
        st.rerun()

# =========================
# 🔵 التفاصيل
# =========================
else:

    selected_type = st.session_state.selected_type
    selected_group = st.session_state.selected_group

    result = df[
        (df["offer_type"] == selected_type) &
        (df["offer_group"] == selected_group)
    ].fillna("")

    if st.button("⬅️ رجوع"):
        st.session_state.page = "filters"
        st.rerun()

    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">{selected_type} / {selected_group}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">📦 تفاصيل العرض</div>', unsafe_allow_html=True)

    rows = ""

    for _, r in result.iterrows():

        product = get_val(r, ["product", "اسم_المستحضر"])
        qty = get_val(r, ["عدد_القطع", "qty"])
        gift = get_val(r, ["الهدية", "bonus_qty"])
        discount = get_val(r, ["الحسم", "discount"])
        value = get_val(r, ["قيمة_العرض", "السعر"])

        rows += f"<tr><td>{product}</td><td>{qty}</td><td>{gift}</td><td>{discount}</td><td>{value}</td></tr>"

    # 🔥 بدون مسافات = حل المشكلة
    html = f"""<div class="offer-box">
<div class="badge">عرض مؤتمر</div>
<h3>💊 {selected_type} / {selected_group}</h3>

<table class="offer-table">
<thead>
<tr>
<th>المستحضر</th>
<th>الكمية</th>
<th>الهدية</th>
<th>الحسم</th>
<th>القيمة</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</div>"""

    st.markdown(html, unsafe_allow_html=True)

    st.subheader("تثبيت العرض")

    with st.form("form"):
        name = st.text_input("الاسم")
        address = st.text_input("العنوان")
        phone = st.text_input("الهاتف")
        notes = st.text_area("ملاحظات")

        if st.form_submit_button("تثبيت"):
            payload = {
                "doctor_name": name,
                "pharmacy_name": address,
                "phone": phone,
                "offer_type": selected_type,
                "offer_group": selected_group,
                "notes": notes
            }

            try:
                res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
                if res.status_code == 200:
                    st.success("تم الحفظ ✅")
                else:
                    st.error("خطأ بالحفظ")
            except:
                st.error("فشل الاتصال")
