import streamlit as st
import os
import platform
import subprocess
from fill_pdf import fill_contract

if platform.system() == "Linux":
    try:
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup_fonts.sh")
        if os.path.exists(script):
            subprocess.run(["bash", script], capture_output=True, timeout=120)
    except Exception:
        pass

st.set_page_config(page_title="ASYA Sözleşme Oluşturucu", page_icon="📄", layout="centered")

st.markdown(
    """
    <style>
    .stImage { margin-top: -20px; }
    div[data-testid="stImage"] { margin-bottom: -20px; }
    </style>
    """,
    unsafe_allow_html=True,
)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.image("assets/black&yellow.png", width=300)

st.title("📄 ASYA OGV Sözleşme Oluşturucu")
st.markdown("Formu doldurarak EP Sözleşmesi PDF'ini otomatik oluşturun. Asya için sevgiyle tasarlandı.")

with st.expander("📋 Kişisel Bilgiler", expanded=True):
    tc_kimlik = st.text_input("TC Kimlik No *", max_chars=11)
    ad = st.text_input("Ad (First Name) *")
    soyad = st.text_input("Soyad (Last Name) *")
    adres = st.text_input("Adres *")
    eposta = st.text_input("E-posta *")
    dogum_tarihi = st.text_input("Doğum Tarihi *", placeholder="DD.MM.YYYY")

with st.expander("🌍 Program Bilgileri", expanded=True):
    ulke = st.text_input("Program Ülkesi *")
    col1, col2 = st.columns([3, 2])
    with col1:
        baslangic_tarihi = st.text_input("Başlangıç Tarihi *", placeholder="DD/MM/YYYY")
    with col2:
        bitis_tarihi = st.text_input("Bitiş Tarihi *", placeholder="DD/MM/YYYY")
    col3, col4 = st.columns(2)
    with col3:
        proje_ucreti_tutar = st.number_input("Karşı Şubenin Proje Ücreti (Tutar) *", min_value=0)
    with col4:
        proje_ucreti_para = st.text_input("Karşı Şubenin Proje Ücreti (Para Birimi) *", help="ör: EGP, USD, EUR")
    col5, col6 = st.columns(2)
    with col5:
        danismanlik_ucreti = st.number_input("Danışmanlık Ücreti *", min_value=0)
    with col6:
        danismanlik_ucreti_yazi = st.text_input("Danışmanlık Ücreti (Yazıyla) *", help="ör: altıbindokuyüzotuz")
    sozlesme_tarihi = st.text_input("Sözleşme Tarihi *", placeholder="DD/MM/YYYY")

with st.expander("📸 Ekran Görüntüleri", expanded=False):
    st.markdown("Sözleşmenin son 3 sayfasındaki ekran görüntülerini yükleyin. En fazla 6 görsel (her sayfada 2 adet). Yüklemezseniz sayfalar boş olacaktır.")
    uploaded_files = st.file_uploader(
        "Ekran görüntülerini yükle",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Görseller sırasıyla yerleştirilir: Sayfa 8 (üst/alt), Sayfa 9 (üst/alt), Sayfa 10 (üst/alt)",
    )
    if uploaded_files:
        st.info(f"{len(uploaded_files)} görsel yüklendi ({6 - len(uploaded_files)} boş slot kaldı)")

st.markdown("---")

if st.button("📝 Sözleşme Oluştur", type="primary", use_container_width=True):
    required = {
        "TC Kimlik No": tc_kimlik,
        "Ad": ad,
        "Soyad": soyad,
        "Adres": adres,
        "E-posta": eposta,
        "Doğum Tarihi": dogum_tarihi,
        "Program Ülkesi": ulke,
        "Başlangıç Tarihi": baslangic_tarihi,
        "Bitiş Tarihi": bitis_tarihi,
        "Karşı Şubenin Proje Ücreti (Tutar)": proje_ucreti_tutar,
        "Karşı Şubenin Proje Ücreti (Para Birimi)": proje_ucreti_para,
        "Danışmanlık Ücreti": danismanlik_ucreti,
        "Danışmanlık Ücreti (Yazıyla)": danismanlik_ucreti_yazi,
        "Sözleşme Tarihi": sozlesme_tarihi,
    }
    missing = []
    for k, v in required.items():
        if isinstance(v, str) and not v.strip():
            missing.append(k)
        elif isinstance(v, (int, float)) and v == 0:
            pass  # 0 is valid for number inputs
    if missing:
        st.error(f"Lütfen şu alanları doldurun: {', '.join(missing)}")
    else:
        try:
            data = {
                "tc_kimlik": tc_kimlik.strip(),
                "ad": ad.strip(),
                "soyad": soyad.strip(),
                "adres": adres.strip(),
                "eposta": eposta.strip(),
                "dogum_tarihi": dogum_tarihi.strip(),
                "ulke": ulke.strip(),
                "baslangic_tarihi": baslangic_tarihi.strip(),
                "bitis_tarihi": bitis_tarihi.strip(),
                "tarih_araligi": f"[{baslangic_tarihi.strip()}]- [{bitis_tarihi.strip()}]",
                "proje_ucreti": f"({proje_ucreti_tutar}) {proje_ucreti_para.strip()}",
                "danismanlik_ucreti": str(danismanlik_ucreti),
                "danismanlik_ucreti_yazi": danismanlik_ucreti_yazi.strip(),
                "danismanlik_ucreti_braket": str(danismanlik_ucreti),
                "sozlesme_tarihi": sozlesme_tarihi.strip(),
            }

            screenshots = []
            for f in uploaded_files[:6]:
                screenshots.append(f.read())

            pdf_bytes = fill_contract(data, screenshots=screenshots if screenshots else None)
            st.session_state["pdf_bytes"] = pdf_bytes
            st.session_state["pdf_name"] = f"{ad.strip()}_{soyad.strip()}_sözleşme.pdf"
            st.success("✅ Sözleşme başarıyla oluşturuldu!")
        except Exception as e:
            st.error(f"Oluşturma hatası: {e}")

if "pdf_bytes" in st.session_state:
    st.download_button(
        label="📥 PDF İndir",
        data=st.session_state["pdf_bytes"],
        file_name=st.session_state["pdf_name"],
        mime="application/pdf",
        use_container_width=True,
    )