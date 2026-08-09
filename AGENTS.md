# AGENTS.md — ASYA Sözleşme Oluşturucu

AIESEC İstanbul Asya OGV'nin sözleşme PDF'lerini otomatik dolduran Streamlit uygulaması.
Bu dosya, PDF doldurma altyapısının nasıl çalıştığını ve yeni belge türlerinin nasıl
ekleneceğini kalıcı olarak hatırlamak için yazıldı.

## Genel Bakış

- **app.py** — Streamlit arayüzü. Kullanıcı başta belge türünü seçer (radio), form bunun
  `fields()` tanımına göre **dinamik** render edilir. Doğrulama, screenshot yükleme ve
  indirme de generic'tir.
- **documents/** — belge türleri. Her PDF bir `DocumentType` alt sınıfıdır ve
  `documents/__init__.py` içindeki `DOCUMENT_TYPES` registry'sine kayıtlıdır.
- **fill_pdf.py** — tüm belge türlerinin kullandığı düşük seviye PDF motoru
  (font bulma, redaction, baseline, screenshot işleme).
- **taslak_sözleşme.pdf** — EP Sözleşmesi şablonu (10 sayfa). Şekil, yer tutucu
  metinlerin PDF içinde **birebir aynı string** olarak durduğu örnek dolu bir PDF'tir.
- **Taslak_Acceptance_Note.pdf** — Acceptance Note (visa letter) şablonu (1 sayfa, İngilizce).
  `Taslak_Acceptance_Note with GUIDE.pdf` aynı şablonun, her değiştirilebilir değerin yanında
  1-10 arası numaralı işaretleyicileri olan kopyasıdır (referans için; runtime'da kullanılmaz).
  Numaralar: 1 üst sağ antet adresi, 2 ülke ("Germany", 4 kez), 3 katılımcı adı ("Ayşenur İnce",
  6 kez), 4/5 program başlangıç/bitiş tarihleri, 6 host Local Committee ("AACHEN", 2 kez),
  7-10 doğum tarihi / pasaport no / düzenlenme / geçerlilik tarihi.
- **setup_fonts.sh** — Linux (Streamlit Cloud) üzerinde uygulama başlarken Times New
  Roman benzeri fontları kurar. `app.py` bunu `platform.system() == "Linux"` ise çalıştırır.
- **assets/black&yellow.png** — üstteki logo.

## PDF Doldurma Tekniği (çekirdek fikir)

Şablon PDF'te değerlerin gitmesini istediğimiz yerlerde **örnek/yer tutucu metinler**
durur (ör. `39931582910`, `[01/08/2026]- [29/08/2026]`, `(3770) EGP`). Doldurma:

1. **`page.search_for(old_text)`** → yer tutucunun bbox'unu bul. `_pick_rect()` birden
   fazla eşleşmeyi Y-toleranslı gruplar; aynı satırdaysa birleştirir, farklı satırda
   kalanlardan en alttakini seçer (git d736b92: "destructive combined redaction" fix'i).
2. **Baseline**: `get_text("dict")` ile yer tutucu span'inin `origin[1]`'i (gerçek
   metin baseline'ı) alınır. `rect.y1 - 0.22*fontsize` yaklaşımına göre dikey hizalama
   için çok daha doğru (git 5614248).
3. **Redaction**: Bulunan rect'in etrafına **minimal** genişletilmiş rect (ör.
   `fitz.Rect(x0, y0-2, x1+60, y1+6)`) ile `add_redact_annot(fill=white)` eklenir; sonra
   `apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)` ile metin silinir. Genişletme
   komşu içeriği bozmamak için minimal olmalı (git 82750c8).
4. **Yeniden yazım**: Aynı baselineda, repo'ya gömülü `TimesNewRoman.ttf` /
   `TimesNewRomanBold.ttf` (Linux'ta Liberation Serif fallback) `page.insert_text` ile
   12pt, siyah yazılır. Fontlar `TNR`/`TNRB` adıyla `insert_font` ile gömülür.

### Paragraf yeniden yazımları (satır kırpma ve bold gereken yerler)

- **1. sayfa giriş paragrafı**: Tüm paragraf redact edilir (Rect(43.2, 133, 557, 220))
  ve `insert_textbox` ile otomatik satır kırpma yapılarak yeniden yazılır. Redaction ilk
  önce, yazım sonra: `_fill_page1_paragraph` → `doc[0].apply_redactions()` →
  `_fill_page1_text`.
- **5. bölüm (2. sayfa)**: `SECTION5_START_MARKER = "Sözleşmede bahsi"` ile
  `SECTION5_END_MARKER = "kabul eder."` arası yer bulunur, redact edilir ve
  `insert_htmlbox` ile HTML string yazılır — böylece `<b>` etiketiyle **native bold**
  desteklenir (git 47220df). HTML içine kullanıcı verisi girerken `& < >` kaçışlanır.

### Ekran görüntüleri (3. sayfa = 10-12. görsel sayfalar)

- `SCREENSHOT_PAGES = [7, 8, 9]` (sıfır-indexli sayfalar 8-10) şablondaki örnek ekran
  görüntülerini içerir.
- `clear_screenshots()`: her görüntü xref'inin stream'i 1x1 beyaz JPEG'e çevrilir
  (`update_stream` + `xref_set_key` Width/Height/Length) ve görüntü bbox'ları redact
  edilir. Böylece eski görüntülerden eser kalmaz.
- `insert_screenshots()`: yeni görseller slot rect'lerine **contain** (letterbox,
  ortalanmış, kenarlardan taşmadan) yerleştirilir: `SCREENSHOT_LAYOUT`'taki slot
  rect'lerine `page.insert_image`.

### Acceptance Note farkları (multi-instance ve zone)

- Aynı yer tutucu PDF'te **birden çok satırda** geçer (ad 6 kez, ülke 4 kez, LC 2 kez) →
  `redact_and_collect` yerine **`redact_all_instances`** kullanılır: her geçtiği yer ayrı
  redact rect'i + ayrı baseline alır (tek-rect `_pick_rect` mantığı yalnızca en alttakini seçerdi).
- Tarihler iki yerde geçer: birleşik `"17.07.2026- 28.08.2026 "` span'ı (vize dönemi satırı,
  tek parça değiştirilir) ve bağımsız `17.07.2026`/`28.08.2026` span'ları (alt satırda).
  Bağımsız olanlar **`zone` filtresi** (Rect(0,390,595,440)) ile ayrıştırılır — yoksa birleşik
  span'ın içindeki tarihler de eşleşir ve çift redact olur.
- Font boyutu değere göre değişir: değerler 10pt bold, adres satırı 10pt normal, antet adresi
  8.5pt bold → pending item'a `size` alanı eklenir, `insert_pending` onu kullanır.
- `insert_pending` sayfa 0'ı font embed'den hariç tutar; tek sayfalık şablonlarda font'lari
  `fill()` içinde elle `insert_fonts(doc[0], ...)` ile gömmek gerekir.
- PyMuPDF eklenen metindeki boşlukları `\xa0`, tireyi `\xad` (soft hyphen) olarak encode eder —
  ekstraksiyonda böyle görünür ama görsel çıktı düzgündür. String karşılaştırırken normalize et.

## Mimari: Belge Türü Kayıt Sistemi

```
app.py                 → DOCUMENT_TYPES registry'sini kullanır, UI tamamen generic
documents/
  __init__.py          → DOCUMENT_TYPES = {d.ID: d for d in (...)} 
  base.py              → Field dataclass + DocumentType arayüzü
  ep_sozlesme.py       → EP Sözleşmesi (10 sayfa, full pipeline)
  acceptance_note.py   → Acceptance Note (STUB — şablon bekleniyor)
fill_pdf.py            → ortak motor (font, rect, baseline, redaction, screenshot)
```

`DocumentType` arayüzü:
- `ID / NAME / DESCRIPTION` — registry key'i ve UI etiketi
- `TEMPLATE_PATH` + `template_available()` — şablon kontrolü; yoksa UI uyarı verir
- `fields() -> List[Field]` — form; `Field(key, label, kind="text"|"number", required,
  placeholder, help, max_chars, half)`; `half=True` olan alanlar bir sonraki half alanla
  yan yana 2 sütunda render edilir
- `assemble_data(form)` — ham form değerlerini `fill()`'in beklediği anahtarlara çevirir
  (ör. `tarih_araligi = f"[{baslangic}]- [{bitis}]"` birleştirmeleri)
- `fill(data, screenshots) -> bytes` — PDF üretimi
- `supports_screenshots() / screenshot_layout() / screenshot_slot_count()` — görsel
  sayfaları olan belgelerde
- `output_filename(data)` — indirilen dosyanın adı

## Yeni Belge Türü Ekleme Adımları

1. Şablon PDF'i repo köküne bırak (ör. `Taslak_Acceptance_Note.pdf`).
2. `documents/` içinde yeni modül aç; `TEMPLATE_PATH`'i doğrula, `NAME`/`DESCRIPTION`'ı
   tanımla.
3. `fields()`'da form alanlarını tanımla (şablondaki yer tutucu metinlerle eşleşen).
4. `assemble_data(form)` ile birleşik alanları kur (tarih aralığı gibi).
5. `fill()` içinde şablonu incele ve önce **hangi yer tutucuların aynen aranabileceğini**
   (`search_for`) bul:
   - Tek satır / tek geçişli yer tutucular → `redact_and_collect` + `insert_pending` (bak:
     `EPSozlesmeDocument.fill`'deki REPLACEMENTS döngüsü). `EXPANDED_RECTS`'te her anahtar
     için minimal genişletme tanımla. Kalın yazılacaksa `use_bold=True`.
   - Aynı değer birden çok yerde geçiyorsa → `redact_all_instances` (bak:
     `AcceptanceNoteDocument.fill`). Alt string çakışması varsa `zone` filtresi kullan.
   - Paragraf içi değerler (tüm paragraf yeniden yazılacaksa) → marker-start/end +
     `insert_textbox` (düz) veya `insert_htmlbox` (bold gerekiyorsa).
6. PDF'i `doc.tobytes()` ile döndür. **app.py'ye dokunma** — registry otomatik
   yakalar. Şablon dosyasını `.gitignore`'daki `!` istisna satırına ekle (Streamlit
   Cloud repo'dan deploy eder).

## Doğrulama Çalışmaları

- Refactor sonrası EP çıktısı **piksel bazında birebir** olduğu doğrulandı (10 sayfa
  render + sayfa metinleri + dosya boyutu). Fark yalnızca PDF metadata zaman damgaları.
- Regresyon testi (isteğe bağlı): aynı input'la PDF üretilip
  `hashlib.sha256(pdf_bytes)` karşılaştırılabilir — dikkat: iki üretim arasında
  `creationDate`/`modDate` farklı olacağından hash aynı **olmaz**; karşılaştırma
  sayfa metni/render ile yapılmalıdır (yukarıdaki piksel karşılaştırma yaklaşımı).

## Bilinen Tuzaklar (git geçmişinden öğrenildi)

- Aynı yer tutucu string PDF'te birden çok yerde geçiyorsa tüm rect'leri tek redaction'da
  birleştirmek başka içeriği de silebilir → `_pick_rect` yaklaşımı (d736b92).
- Yazıyı `rect.y1`'e değil **span origin baseline'ına** yerleştir (5614248).
- Redaction rect'ini fazla büyütme; komşu satırlar/içerik silinir (82750c8).
- Font dosyası bulunamazsa crash olur → `font_available()` + `helv` fallback (8be1f70).
- Linux'ta Türkçe karakterler için Times New Roman kurulumu şart (setup_fonts.sh).
- `insert_htmlbox` kullanıcı verisi alıyorsa `& < >` escape et (özel karakterli ülke/
  tarih girdileri PDF'i bozabilir).
- Screenshot sayfalarında eski görüntüyü sadece redact etmek yetmez — stream'i beyaz
  JPEG ile değiştirmek gerekiyor (`clear_screenshots`).

## Çalıştırma

```bash
pip install -r requirements.txt   # streamlit, PyMuPDF, Pillow
streamlit run app.py
```