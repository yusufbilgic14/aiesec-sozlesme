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
  `documents/embassies.py` belge türü DEĞİLDİR — AN'nin ülke→temsilcilik veritabanıdır
  (registry'de yok).
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
- **Fontlar**: `TimesNewRoman.ttf`/`TimesNewRomanBold.ttf` (EP, `insert_text` için),
  `Carlito-Regular.ttf`/`Carlito-Bold.ttf` (Calibri metrik-uyumlu, OFL; AN'nin dinamik
  metni — `insert_htmlbox` @font-face ile; `liga` özellikleri PUA arama/kopyalama bozmasın
  diye fontTools ile söküldü), `LiberationSans-Regular.ttf`/`LiberationSans-Bold.ttf`
  (Arial metrik-uyumlu; AN antet satırı şablondaki Arial-BoldMT'yi birebir verir).
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

### Acceptance Note farkları (region-based htmlbox yeniden yazımı)

AN, EP'nin sayfa-1/5. bölüm formülünü **tüm değişken bölgelerine** uygular: yer tutucu
arıyor değil, değişken içeren her cümle bölgesini komple white-out edip cümleyi
form verisinden baştan kurar. Böylece boşluklar her uzunluktaki girdiye uyar (eski
karakter-karakter swap yaklaşımı bunu sağlayamıyordu — sabit şablon boşlukları ve
uzun girdide taşma: commit 4b61906'dan vazgeçildi).

- `REGIONS` listesi: 7 bölge, her biri `fitz.Rect` (şablon satır bbox'ından türetilmiş).
  Hepsi önce tek `apply_redactions` ile silinir, sonra `page.insert_htmlbox` ile
  `_build_regions_html(data)` HTML'i yazılır (`<b>` = native bold, commit 47220df yöntemi).
- Bölge içeriği tamamen dinamiktir: değerler değil, **cümleler** veriden kurulur
  (`para3`/`para4`/`para5`/`title`/`visa_officer` tamamen yeniden yazılır; `details`
  6 satırlık blok, `letterhead` sağa hizalı antet adresi).
- **Antet adresi = temsilcilik adresi** (şube adresi değil!): kullanıcı ülkeyi (`ulke`,
  kind="select", İngilizce ülke adları — mektup gövdesinde aynen kullanıldığı için),
  ülkede birden fazla temsilcilik varsa şehri (`sehir`, depends_on="ulke") seçer.
  `documents/embassies.py` → `MISSIONS` veritabanı: ülke → misyon listesi (`label` UI
  etiketi, `title` hitap satırındaki resmi ad, `address` antete giden adres).
  `assemble_data` misyonu `sirket_adresi` + `mission_title` anahtarlarına çözer;
  `visa_officer` satırı "The Visa Officer, <b>{mission_title}</b>" olur (şablonun sabit
  "Consulate General of the Federal Republic of Germany" yazısı yerine her temsilciliğin
  resmi adı). Adlar temsilciliklerin gerçek mektuplarında kullandığı biçimle birebir
  tutulmalı: Polonya "The Consulate General of the Republic of Poland in Istanbul",
  Portekiz'in İstanbul varlığı FAHRİ konsolosluktur ("Honorary Consulate of Portugal in
  Istanbul", portaldascomunidades.mne.gov.pt), Mısır/Hindistan İstanbul adlarında
  "in Istanbul" yoktur. Adresler ~65 karakteri geçmemeli (8.5pt antet satırı rect'ine
  scale_low tetiklenmeden sığsın). Adresler resmi kaynaklardan doğrulandı (Ağu 2026) —
  değişiklik yaparken kaynağı teyit et.
- Hizalama şablonu **birebir** kopyalanmalı: gövde satırları sola (x=54.0), `letterhead`
  sağa (sağ kenar 572.7) ve `visa_officer` da sağa (sağ kenar 577.7, rect x1=578.9,
  `align="right"`) — şablonun anlık bbox'ını ölçmeden "sola hizalı" varsayma (git c94253c).
- Statik bölgeler (giriş paragrafları, "Dear Sir / Madam,", "The following are his
  details:", "Best regards,", imzalar) şablonda orijinal Calibri fontuyla bırakılır.
- `insert_htmlbox` varsayılan olarak kendi gömülü **CharisSIL** serifini kullanır. AN,
  `fitz.Archive(repo_root)` + `@font-face` CSS'i geçerek **Carlito** (Calibri metrik-uyumlu)
  kullandırır: `font-family:carlito` + `font-weight:bold` → Carlito-Bold. Böylece satır
  kırpma ve glif genişlikleri şablondaki Calibri'yle birebir aynı olur. Antet satırı
  (8.5pt, sağa hizalı) ayrıca **Liberation Sans** family'si kullanır — şablondaki
  Arial-BoldMT metrikleri için. Calibri (statik) + Carlito (dinamik) karışımı bilinçlidir.
- **Baseline kalibrasyonu (ampirik)**: ilk satır baseline = `rect.y0 + 10.75` (10pt Carlito)
  veya `+ 8.65` (8.5pt); `line-height` 1.35'ten büyükse üstüne yarım ekstra leading eklenir
  (details, lh=2.4 → ilk satır = `rect.y0 + 16.0`, pitch 24.0 = şablonun 24pt satır aralığı).
  Gövde sol hizası da önemlidir: htmlbox metni rect.x0'tan **+1pt** içeriden başlatır;
  şablon metni x=54'ten başladığı için rect'ler `x0=53` kullanır (ayrıca `htmlbox` her satırı
  x=54.0'a oturtur). Sağa hizalı satırlar için de aynı inset geçerli: text sağ kenarı
  rect.x1 − 1.2pt'e oturur → hedef kenar 577.7 ise rect.x1 = 578.9. Bölge rect'leri bu
  değerlerle şablon satırlarına Δ ≤ 0.1pt oturur.
- Rect'ler komşu statik içeriği silmemek için dar tutulmalıdır; ör. `para5` (601.25..638)
  "Best regards," (üst ~642) ile 4pt pay bırakır; `details` (451.7..597) "The following
  are his details:" (443) satırına dokunmaz. Uzun girdide htmlbox `scale_low` ile
  otomatik küçültür (taşma olmaz — EP ile aynı davranış).
- `insert_pending` sayfa 0'ı font embed'den hariç tutar; tek sayfalık şablonlarda font'lari
  `fill()` içinde elle `insert_fonts(doc[0], ...)` ile gömmek gerekir.
- PyMuPDF eklenen metindeki boşlukları `\xa0`, tireyi `\xad` (soft hyphen) olarak encode eder —
  ekstraksiyonda böyle görünür ama görsel çıktı düzgündür. String karşılaştırırken normalize et.
- Not: `fill_pdf.py`'deki `redact_all_instances`/`zone` mekanizması AN v1 (4b61906) için
  yazıldı, artık AN tarafından kullanılmıyor; ileride bölge-bazlı olmayan belgeler için
  motor yardımcıları olarak duruyor.

## Mimari: Belge Türü Kayıt Sistemi

```
app.py                 → DOCUMENT_TYPES registry'sini kullanır, UI tamamen generic
documents/
  __init__.py          → DOCUMENT_TYPES = {d.ID: d for d in (...)} 
  base.py              → Field dataclass + DocumentType arayüzü
  ep_sozlesme.py       → EP Sözleşmesi (10 sayfa, full pipeline)
  acceptance_note.py   → Acceptance Note (tek sayfa, region-based htmlbox)
  embassies.py         → ülke → misyon veritabanı (registry'de YOK)
fill_pdf.py            → ortak motor (font, rect, baseline, redaction, screenshot)
```

`DocumentType` arayüzü:
- `ID / NAME / DESCRIPTION` — registry key'i ve UI etiketi
- `TEMPLATE_PATH` + `template_available()` — şablon kontrolü; yoksa UI uyarı verir
- `fields() -> List[Field]` — form; `Field(key, label, kind="text"|"number"|"select",
  required, placeholder, help, max_chars, half, options, depends_on)`; `half=True` olan
  alanlar bir sonraki half alanla yan yana 2 sütunda render edilir; `kind="select"` →
  `st.selectbox` (statik `options` ya da `depends_on` ile kademeli: şehir gibi); tek
  seçenek kalan bağımlı selectbox UI'da render edilmez (değeri otomatik doldurulur)
- `field_options(key, parent_value)` — bağımlı selectlerin seçenek listesi; varsayılan
  `Field.options`'ı döner, kademeli alanlarda override edilir (bak: AN `sehir`)
- `assemble_data(form)` — ham form değerlerini `fill()`'in beklediği anahtarlara çevirir
  (ör. `tarih_araligi = f"[{baslangic}]- [{bitis}]"` birleştirmeleri, AN'de misyon
  çözümlemesi)
- `fill(data, screenshots) -> bytes` — PDF üretimi
- `supports_screenshots() / screenshot_layout() / screenshot_slot_count()` — görsel
  sayfaları olan belgelerde
- `output_filename(data)` — indirilen dosyanın adı

## Yeni Belge Türü Ekleme Adımları

1. Şablon PDF'i repo köküne bırak (ör. `Taslak_Acceptance_Note.pdf`).
2. `documents/` içinde yeni modül aç; `TEMPLATE_PATH`'i doğrula, `NAME`/`DESCRIPTION`'ı
   tanımla.
3. `fields()`'da form alanlarını tanımla (şablondaki yer tutucu metinlerle eşleşen).
   Açılır liste gerekiyorsa `kind="select"` + `options=`; ülke→şehir gibi kademeli
   seçimde ikinci alana `depends_on` ver ve `field_options(key, parent_value)`'yu
   override et (bak: AN `ulke`/`sehir` + `documents/embassies.py`).
4. `assemble_data(form)` ile birleşik alanları kur (tarih aralığı gibi).
5. `fill()` içinde şablonu incele ve önce **hangi yer tutucuların aynen aranabileceğini**
   (`search_for`) bul:
   - Tek satır / tek geçişli yer tutucular → `redact_and_collect` + `insert_pending` (bak:
     `EPSozlesmeDocument.fill`'deki REPLACEMENTS döngüsü). `EXPANDED_RECTS`'te her anahtar
     için minimal genişletme tanımla. Kalın yazılacaksa `use_bold=True`.
   - Aynı değer birden çok yerde geçiyorsa ve cümleler baştan kurulacaksa → bölge-bazlı
     yaklaşım (bak: `AcceptanceNoteDocument.fill`): değişken içeren bölgeleri `REGIONS`
     rect'leriyle komple white-out edip `insert_htmlbox` ile cümleyi veriden baştan kur.
     Bu yöntem her uzunluktaki girdiye uyar.
   - Paragraf içi değerler (tüm paragraf yeniden yazılacaksa) → marker-start/end +
     `insert_textbox` (düz) veya `insert_htmlbox` (bold gerekiyorsa).
   - `insert_htmlbox` kullanıyorsan **varsayılan CharisSIL serifini kullanma**:
     şablonun metrik eşdeğeri fontu `fitz.Archive(repo_root)` + `@font-face` CSS'i ile
     bağla ve font dosyalarını repo köküne koy (Calibri→`Carlito-*.ttf`,
     Arial→`LiberationSans-*.ttf`; EP'nin TNR'si gibi gömülü değil, archive'ten).
     Bölge rect'lerini ilk satır formülüyle (`y0 + 10.75` vb.) kalibre et — yukarıdaki
     "Doğrulama Reçetesi" ile aynı-değer hizasını kanıtlamadan bitirme.
6. PDF'i `doc.tobytes()` ile döndür. **app.py'ye dokunma** — registry otomatik
   yakalar. Şablon dosyasını `.gitignore`'daki `!` istisna satırına ekle (Streamlit
   Cloud repo'dan deploy eder).

## Doğrulama Reçetesi (yeni belge türleri için)

Bölge-bazlı (htmlbox) bir belgeyi şablonla "aynı değerlerle" doldurup şunları sırayla
doğrula — AN'nin şu anki durumu tüm maddeleri geçiyor:

1. **Baseline haritası**: Şablonun her dinamik satırının `origin[1]`'ini (get_text
   `"dict"`) ölç; doldurulmuş çıktıda aynı satırlar Δ ≤ 0.1pt'te olmalı. İlk satır
   formülü: `rect.y0 + 10.75` (10pt Carlito), `+ 8.65` (8.5pt), lh>1.35 ise üstüne
   yarım ekstra leading (details lh=2.4 → `+ 16.0`).
2. **Font boyutu tam**: Tüm eklenen span'ler `size` birebir (10.0/8.5). 9.9/9.94 gibi
   değerler = `scale_low` tetiklenmiş → bölge rect'ini büyüt (komşu statik içeriğe
   dokunmadan; para5/`Best regards` gibi sınırlarda ≥ 3-4pt pay bırak).
3. **x hizası**: gövde satırları x0=54.0 birebir; sağa hizalı satırların sağ kenarı
   şablonunkiyle birebir (inset ~1.2pt). Şablonun bbox'ını ölçmeden hizalama varsayma.
4. **Ekstraksiyon/PUA**: Çıktı metninde U+0xE000+ (PUA) karakter olmamalı; "Officer",
   "Letter" gibi kelimeler PDF içinde **aranabilir** olmalı. PUA çıkarsa fonttan
   `liga`/`clig`/`rlig` sök (fontTools, repo'da yapıldı) veya ligature'sız font seç.
5. **Uzun girdi senaryosu**: Mevcut girdilerin ~1.5-2 katı uzunluğunda isim/ülke/LC/
   adres dene; eklenen span'lerin `fitz.Rect.intersects()` statik span taraması = 0
   olmalı (boş intersection'lara dikkat: `&` yerine `intersects` kullan).
6. **Çift boşluk taraması**: `get_text()` çıktısında `  ` (çift boşluk) olmamalı — ama
   span bazlı echo script'leri span'ları `'  '` ile birleştirerek yanlış pozitif
   üretir; `get_text()` düz metniyle kontrol et.
7. **EP regresyonu**: `documents/`'ta EP dosyalarına dokunulmadıysa atlanabilir;
   dokunulduysa sayfa metin hash'leri karşılaştır (metadata hash değil).

## Doğrulama Çalışmaları

- Refactor sonrası EP çıktısı **piksel bazında birebir** olduğu doğrulandı (10 sayfa
  render + sayfa metinleri + dosya boyutu). Fark yalnızca PDF metadata zaman damgaları.
- AN aynı-değer doğrulaması: şablondaki satır baseline'larıyla Δ ≤ 0.1pt, x0=54.0 birebir,
  font boyutları 10.0/8.5 (ölçeklenme yok); antet bbox'ı template ile ~0.2pt içinde.
  Uzun girdide çakışma = 0 (htmlbox scale_low taşmayı zaten engeller).
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
- `insert_htmlbox` içerik rect'inden yüksek olursa **`scale_low` ile fontu küçültür** —
  bölge rect'lerine marj bırak; "sizes are different" şikayetlerinin sebebi buydu.
- htmlbox + Carlito varsayılan `liga` GSUB özelliği yüzünden "tt/ti/st/ff" çiftleri PUA
  karakterlere dönüşür (PDF içinde arama/kopyalama bozulur). Çözüm: repo'daki Carlito
  dosyalarından fontTools ile `liga`/`clig`/`rlig` özellikleri söküldü (şablon Calibri
  çıktısında da ligature yoktu, böylece birebir hizalı).
- Screenshot sayfalarında eski görüntüyü sadece redact etmek yetmez — stream'i beyaz
  JPEG ile değiştirmek gerekiyor (`clear_screenshots`).

## Çalıştırma

```bash
pip install -r requirements.txt   # streamlit, PyMuPDF, Pillow
streamlit run app.py
```