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

st.markdown("""
<style>
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
}
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #111827 100%);
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1250px;
}
.hero {
    background: linear-gradient(135deg, #2563eb, #0f766e);
    border-radius: 28px;
    padding: 28px;
    margin-bottom: 22px;
    color: white;
    box-shadow: 0 18px 45px rgba(0,0,0,0.28);
}
.hero-title {
    font-size: 38px;
    font-weight: 900;
    margin-bottom: 8px;
}
.hero-subtitle {
    font-size: 18px;
    opacity: 0.92;
}
.filter-card {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.16);
    border-radius: 24px;
    padding: 22px;
    margin-bottom: 22px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.18);
}
.section-title {
    color: #f8fafc;
    font-size: 25px;
    font-weight: 800;
    margin: 12px 0 18px;
}
.offer-box {
    background: #ffffff;
    border-radius: 24px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.18);
    min-height: 220px;
    border-top: 6px solid #2563eb;
}
.offer-product {
    color: #0f172a;
    font-size: 23px;
    font-weight: 900;
    margin-bottom: 16px;
}
.offer-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 9px 0;
    border-bottom: 1px solid #e5e7eb;
    color: #334155;
    font-size: 16px;
}
.offer-row:last-child {
    border-bottom: none;
}
.offer-label {
    color: #64748b;
    font-weight: 700;
}
.offer-value {
    color: #0f172a;
    font-weight: 900;
}
.badge {
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    border-radius: 999px;
    padding: 6px 12px;
    font-weight: 800;
    margin-bottom: 12px;
}
.form-box {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.16);
    border-radius: 24px;
    padding: 22px;
    margin-top: 20px;
}
div[data-testid="stForm"] {
    background: rgba(255,255,255,0.07);
    padding: 20px;
    border-radius: 22px;
}
h1, h2, h3, .stMarkdown, label {
    color: #f8fafc !important;
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


def clean_value(value):
    if pd.isna(value) or value is None:
        return ""
    value = str(value)
    if value.lower() in ["none", "nan", "nat"]:
        return ""
    return value


def get_first_value(row, columns):
    for col in columns:
        if col in row.index:
            value = clean_value(row.get(col, ""))
            if value != "":
                return value
    return ""


df = load_data()

if "page" not in st.session_state:
    st.session_state.page = "filters"

if st.button("🔄 تحديث بيانات العروض"):
    st.cache_data.clear()
    st.rerun()


# =========================
# شاشة اختيار العرض
# =========================
if st.session_state.page == "filters":
    st.markdown("""
    <div class="hero">
        <div class="hero-title">💊 نظام عروض مؤتمر الصيادلة</div>
        <div class="hero-subtitle">اختر نوع العرض ثم مجموعة العرض لعرض التفاصيل وتثبيت الطلب مباشرة</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="filter-card">', unsafe_allow_html=True)

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

    if st.button("🚀 عرض تفاصيل العرض", use_container_width=True):
        st.session_state.selected_type = offer_type
        st.session_state.selected_group = offer_group
        st.session_state.page = "details"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


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

    result = result.fillna("")
    result = result.loc[:, ~result.columns.str.contains("unnamed", case=False)]

    top1, top2 = st.columns([1, 4])

    with top1:
        if st.button("⬅️ رجوع للخيارات", use_container_width=True):
            st.session_state.page = "filters"
            st.rerun()

    with top2:
        st.markdown(f"""
        <div class="hero">
            <div class="hero-title">{selected_type} / {selected_group}</div>
            <div class="hero-subtitle">تفاصيل المنتجات المرتبطة بهذا العرض</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">📦 المنتجات ضمن العرض</div>', unsafe_allow_html=True)

    cols = st.columns(2)

    for i, (_, row) in enumerate(result.iterrows()):
        col = cols[i % 2]

        product = get_first_value(row, [
            "product",
            "اسم_المستحضر",
            "المستحضر",
            "الصنف",
            "العرض_او_الحسم"
        ])

        qty = get_first_value(row, [
            "qty",
            "عدد_القطع",
            "كمية_العرض",
            "كمية_العرض_",
            "الكمية"
        ])

        gift = get_first_value(row, [
            "bonus_qty",
            "البونص",
            "الهدية",
            "gift"
        ])

        discount = get_first_value(row, [
            "discount",
            "الحسم",
            "نسبة_الحسم",
            "العرض_او_الحسم"
        ])

        value = get_first_value(row, [
            "قيمة_العرض",
            "value",
            "السعر",
            "القيمة"
        ])

        with col:
            st.markdown(f"""
            <div class="offer-box">
                <div class="badge">عرض مؤتمر</div>
                <div class="offer-product">💊 {product}</div>

                <div class="offer-row">
                    <span class="offer-label">📦 الكمية</span>
                    <span class="offer-value">{qty}</span>
                </div>

                <div class="offer-row">
                    <span class="offer-label">🎁 الهدية</span>
                    <span class="offer-value">{gift}</span>
                </div>

                <div class="offer-row">
                    <span class="offer-label">💰 الحسم</span>
                    <span class="offer-value">{discount}</span>
                </div>

                <div class="offer-row">
                    <span class="offer-label">💵 قيمة العرض</span>
                    <span class="offer-value">{value}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.subheader("✅ تثبيت العرض")

    with st.form("confirm_offer_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            doctor_name = st.text_input("اسم الصيدلي / الدكتور")
        with c2:
            pharmacy_name = st.text_input("العنوان")
        with c3:
            phone = st.text_input("رقم الهاتف")

        notes = st.text_area("تثبيت العرض:", height=90)

        submitted = st.form_submit_button("✅ تثبيت العرض", use_container_width=True)

        if submitted:
            if not doctor_name and not pharmacy_name:
                st.warning("يرجى إدخال اسم الصيدلي/الدكتور أو العنوان.")
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

    st.markdown('</div>', unsafe_allow_html=True)
