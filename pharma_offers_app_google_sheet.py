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
# 🔐 المستخدمين
# =========================
USERS = {
    "Manar": "123",
    "Ruba": "0123",
    "Alaa": "1234"
}

# =========================
# CSS
# =========================
st.markdown("""
<style>
html, body { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

# =========================
# Login
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")

    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("دخول"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.employee = username
            st.rerun()
        else:
            st.error("بيانات غير صحيحة")

    st.stop()

# =========================
# تحميل البيانات
# =========================
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    df = df.dropna(how="all")

    df["offer_type"] = df["offer_type"].astype(str)
    df["offer_group"] = df["offer_group"].astype(str)

    return df

df = load_data()

if "page" not in st.session_state:
    st.session_state.page = "filters"

# =========================
# شاشة الفلاتر
# =========================
if st.session_state.page == "filters":

    st.title(f"💊 أهلاً {st.session_state.employee}")

    col1, col2 = st.columns(2)

    with col1:
        offer_type = st.selectbox("نوع العرض", sorted(df["offer_type"].unique()))

    filtered = df[df["offer_type"] == offer_type]

    with col2:
        offer_group = st.selectbox("مجموعة العرض", sorted(filtered["offer_group"].unique()))

    if st.button("عرض التفاصيل"):
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
    ].fillna("")

    st.subheader(f"{selected_type} / {selected_group}")

    if st.button("⬅️ رجوع"):
        st.session_state.page = "filters"
        st.rerun()

    st.dataframe(result, use_container_width=True)

    st.subheader("تثبيت العرض")

    with st.form("form"):

        doctor = st.text_input("اسم الدكتور / الصيدلي")
        address = st.text_input("العنوان")
        phone = st.text_input("رقم الهاتف")
        notes = st.text_area("ملاحظات")

        submit = st.form_submit_button("تثبيت")

        if submit:
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
                r = requests.post(GOOGLE_SCRIPT_URL, json=payload)
                if r.status_code == 200:
                    st.success("تم الحفظ ✅")
                else:
                    st.error("خطأ بالحفظ")
            except:
                st.error("فشل الاتصال")
