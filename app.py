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

st.set_page_config(page_title="AIESEC Sözleşme Oluşturucu", page_icon="📄", layout="centered")

st.title("📄 AIESEC Sözleşme Oluşturucu")
st.markdown("Formu doldurarak Değişim Katılımcısı Sözleşmesi PDF'ini otomatik oluşturun.")

st.header("Kişisel Bilgiler")
col1, col2 = st.columns(2)

with col1:
    tc_kimlik = st.text_input("TC Kimlik No *", max_chars=11)
    ad = st.text_input("Ad *")
    adres = st.text_input("Adres *")

with col2:
    eposta = st.text_input("E-posta *")
    soyad = st.text_input("Soyad *")
    dogum_tarihi = st.text_input("Doğum Tarihi (DD.MM.YYYY) *")

st.header("Program Bilgileri")
col3, col4 = st.columns(2)

with col3:
    ulke = st.text_input("Program Ülkesi *")
    baslangic_tarihi = st.text_input("Başlangıç Tarihi (DD/MM/YYYY) *")

with col4:
    para_birimi = st.text_input("Para Birimi *", help="Ödeme para birimi (ör: EGP, USD, EUR)")
    tutar = st.number_input("Tutar *", min_value=0)
    bitis_tarihi = st.text_input("Bitiş Tarihi (DD/MM/YYYY) *")

sozlesme_tarihi = st.text_input("Sözleşme Tarihi (DD/MM/YYYY) *")

st.header("Ekran Görüntüleri")
st.markdown("Sözleşmenin son 3 sayfasındaki ekran görüntülerini yükleyin. En fazla 6 görsel (her sayfada 2 adet). Yüklemezseniz sayfalar boş olacaktır.")
uploaded_files = st.file_uploader(
    "Ekran görüntülerini yükle",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    help="Görseller yükleme sırasına göre yerleştirilir (sayfa 8 üst/alt, sayfa 9 üst/alt, sayfa 10 üst/alt).",
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
        "Para Birimi": para_birimi,
        "Sözleşme Tarihi": sozlesme_tarihi,
    }
    missing = [k for k, v in required.items() if not v.strip()]
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
                "odeme_bilgisi": f"({tutar}) {para_birimi.strip()}",
                "sozlesme_tarihi": sozlesme_tarihi.strip(),
            }

            screenshots = []
            for f in uploaded_files[:6]:
                screenshots.append(f.read())

            pdf_bytes = fill_contract(data, screenshots=screenshots if screenshots else None)
            st.session_state["pdf_bytes"] = pdf_bytes
            st.session_state["pdf_name"] = f"sozlesme_{ad.strip()}_{soyad.strip()}.pdf"
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