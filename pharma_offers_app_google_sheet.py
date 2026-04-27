import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(
    page_title="عروض المؤتمر",
    page_icon="💊",
    layout="wide"
)

DATA_FILE = "عروض المؤتمر 2026.xlsx"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz7dTqGUw95xDV2rVX6FbbcZM7H_LaJ-T83b1iYWYqrJ-Kq36gcFj3zD-kd-28jhsga/exec"

st.markdown("""
<style>
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
}
.block-container {
    padding-top: 2rem;
}
.offer-box {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
}
.title {
    font-size: 34px;
    font-weight: 800;
    color: #0f172a;
}
.subtitle {
    font-size: 17px;
    color: #475569;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    df = df.dropna(how="all")

    required = ["offer_type", "offer_group"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"الأعمدة الناقصة من ملف الإكسل: {missing}")
        st.stop()

    df["offer_type"] = df["offer_type"].astype(str).str.strip()
    df["offer_group"] = df["offer_group"].astype(str).str.strip()
    return df

df = load_data()

if "page" not in st.session_state:
    st.session_state.page = "filters"

# =========================
# شاشة اختيار العرض
# =========================
if st.session_state.page == "filters":
    st.markdown('<div class="title">💊 نظام عروض مؤتمر الصيادلة</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">اختر نوع العرض ثم مجموعة العرض لعرض التفاصيل</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        offer_type = st.selectbox(
            "اختر نوع العرض",
            sorted(df["offer_type"].dropna().unique())
        )

    filtered_type = df[df["offer_type"] == offer_type]

    with col2:
        offer_group = st.selectbox(
            "اختر مجموعة العرض",
            sorted(filtered_type["offer_group"].dropna().unique())
        )

    if st.button("عرض التفاصيل", use_container_width=True):
        st.session_state.selected_type = offer_type
        st.session_state.selected_group = offer_group
        st.session_state.page = "details"
        st.rerun()

# =========================
# شاشة تفاصيل العرض
# =========================
elif st.session_state.page == "details":
    selected_type = st.session_state.selected_type
    selected_group = st.session_state.selected_group

    result = df[
        (df["offer_type"] == selected_type) &
        (df["offer_group"] == selected_group)
    ].copy()

    top1, top2 = st.columns([1, 4])

    with top1:
        if st.button("⬅️ رجوع للخيارات", use_container_width=True):
            st.session_state.page = "filters"
            st.rerun()

    with top2:
        st.markdown(f'<div class="title">تفاصيل العرض: {selected_type} / {selected_group}</div>', unsafe_allow_html=True)

    st.divider()

    show_cols = [c for c in result.columns if c not in ["id"]]

    st.dataframe(
        result[show_cols],
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    st.subheader("تثبيت العرض")

    with st.form("confirm_offer_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            doctor_name = st.text_input("اسم الصيدلي / الدكتور")
        with c2:
            pharmacy_name = st.text_input("اسم الصيدلية")
        with c3:
            phone = st.text_input("رقم الهاتف")

        notes = st.text_area("ملاحظات", height=80)

        submitted = st.form_submit_button("✅ تثبيت العرض", use_container_width=True)

        if submitted:
            if not doctor_name and not pharmacy_name:
                st.warning("يرجى إدخال اسم الصيدلي/الدكتور أو اسم الصيدلية.")
            else:
                payload = {
                    "doctor_name": doctor_name,
                    "pharmacy_name": pharmacy_name,
                    "phone": phone,
                    "offer_type": selected_type,
                    "offer_group": selected_group,
                    "notes": notes
                }

                try:
                    response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=15)

                    if response.status_code == 200:
                        st.success("تم تثبيت العرض وحفظه في Google Sheet بنجاح ✅")
                    else:
                        st.error(f"صار خطأ بالحفظ. Status code: {response.status_code}")

                except Exception as e:
                    st.error(f"تعذر الاتصال بـ Google Sheet: {e}")
