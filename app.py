import platform
import os
import subprocess

import streamlit as st

from documents import DOCUMENT_TYPES

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
    .stImage { margin-top: -40px; }
    div[data-testid="stImage"] { margin-bottom: -40px; }
    </style>
    """,
    unsafe_allow_html=True,
)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.image("assets/black&yellow.png", width=300)

st.title("📄 ASYA OGV Sözleşme Oluşturucu")
st.markdown("Formu doldurarak EP Sözleşmesi PDF'ini otomatik oluşturun. Asya için sevgiyle tasarlandı.")

doc_id = st.radio(
    "Oluşturmak istediğiniz belge türünü seçin:",
    options=list(DOCUMENT_TYPES.keys()),
    format_func=lambda k: DOCUMENT_TYPES[k].NAME,
    horizontal=True,
)
doc_type = DOCUMENT_TYPES[doc_id]
st.caption(doc_type.DESCRIPTION)

if not doc_type.template_available():
    st.warning(doc_type.TEMPLATE_MISSING_HINT or "Şablon dosyası bulunamadı.")
else:
    fields = doc_type.fields()
    form_values = {}

    def render_field(f):
        if f.kind == "number":
            return st.number_input(
                f.label,
                min_value=0,
                help=f.help or None,
                key=f"{doc_id}_{f.key}",
            )
        if f.kind == "select":
            parent_value = None
            if f.depends_on:
                parent_value = st.session_state.get(f"{doc_id}_{f.depends_on}")
            options = doc_type.field_options(f.key, parent_value) if f.depends_on else doc_type.field_options(f.key)
            if f.depends_on and len(options) == 1:
                # single mission for this country: no dropdown needed
                return options[0]
            return st.selectbox(
                f.label,
                options=options,
                help=f.help or None,
                key=f"{doc_id}_{f.key}",
            )
        return st.text_input(
            f.label,
            placeholder=f.placeholder or None,
            max_chars=f.max_chars or None,
            help=f.help or None,
            key=f"{doc_id}_{f.key}",
        )

    i = 0
    while i < len(fields):
        current = fields[i]
        nxt = fields[i + 1] if i + 1 < len(fields) else None
        if current.half and nxt is not None and nxt.half:
            col_a, col_b = st.columns(2)
            with col_a:
                form_values[current.key] = render_field(current)
            with col_b:
                form_values[nxt.key] = render_field(nxt)
            i += 2
        else:
            form_values[current.key] = render_field(current)
            i += 1

    uploaded_files = []
    if doc_type.supports_screenshots():
        slot_count = doc_type.screenshot_slot_count()
        with st.expander("📸 Ekran Görüntüleri", expanded=False):
            st.markdown(doc_type.SCREENSHOTS_HELP or "")
            uploaded_files = st.file_uploader(
                "Ekran görüntülerini yükle",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
            ) or []
            if uploaded_files:
                st.info(f"{len(uploaded_files)} görsel yüklendi ({slot_count - len(uploaded_files)} boş slot kaldı)")
    screenshots = [f.read() for f in uploaded_files[:slot_count]] if doc_type.supports_screenshots() else []

    st.markdown("---")

    if st.button("📝 PDF Oluştur", type="primary", use_container_width=True):
        missing = []
        for f in fields:
            if not f.required:
                continue
            v = form_values[f.key]
            if isinstance(v, str) and not v.strip():
                missing.append(f.label)
        if missing:
            st.error(f"Lütfen şu alanları doldurun: {', '.join(missing)}")
        else:
            try:
                pdf_bytes = doc_type.run(form_values, screenshots=screenshots or None)
                data = doc_type.assemble_data(form_values)
                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["pdf_name"] = doc_type.output_filename(data)
                st.success("✅ PDF başarıyla oluşturuldu!")
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

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 14px;'>"
    "Geliştirmeler ve feedbackler için bana istediğiniz zaman ulaşabilirsiniz. -yusuf"
    "</p>",
    unsafe_allow_html=True,
)