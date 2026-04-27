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

.title {
    font-size: 30px;
    font-weight: bold;
}

.subtitle {
    color: #aaa;
    margin-bottom: 20px;
}

[data-testid="stDataFrame"] {
    font-size: 20px !important;
}
[data-testid="stDataFrame"] div {
    font-size: 18px !important;
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

    st.markdown('<div class="title">💊 نظام عروض مؤتمر الصيادلة</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">اختر العرض لعرض التفاصيل</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        offer_type = st.selectbox("نوع العرض", sorted(df["offer_type"].unique()))

    filtered = df[df["offer_type"] == offer_type]

    with col2:
        offer_group = st.selectbox("مجموعة العرض", sorted(filtered["offer_group"].unique()))

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

    # 🧼 تنظيف
    result = result.fillna("")
    result = result.loc[:, ~result.columns.str.contains("unnamed", case=False)]

    # =========================
    # 🔥 تحويل النسب
    # =========================
    for col in result.columns:
        if "حسم" in col or "discount" in col or "نسبة" in col:
            result[col] = result[col].apply(
                lambda x: f"{x:.0%}" if isinstance(x, (int, float)) and 0 < x <= 1 else x
            )

    # =========================
    # 💰 تنسيق الأرقام
    # =========================
    for col in result.columns:
        if "قيمة" in col or "سعر" in col or "price" in col or "value" in col:
            result[col] = result[col].apply(
                lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x
            )

    st.markdown(f"### 💊 {selected_type} / {selected_group}")

    if st.button("⬅️ رجوع"):
        st.session_state.page = "filters"
        st.rerun()

    st.divider()

    # =========================
    # 📊 عرض الجدول
    # =========================
    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True,
        height=520
    )

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
