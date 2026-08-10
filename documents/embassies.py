"""Embassy / Consulate General addresses in Türkiye for the Acceptance Note.

The letterhead (top right of the visa letter) carries the address of the
diplomatic mission the participant will apply to, not the LC/branch address.
The UI offers a country dropdown and — when the country has more than one
mission in Türkiye — a second dropdown for the city/mission. The chosen
mission's ``address`` lands in the letterhead region, and its official
``title`` replaces the "Consulate General of the Federal Republic of ..."
salutation line.

Addresses were verified against official sources (Aug 2026), e.g.:
- Germany: tuerkei.diplo.de (German Foreign Office)
- India: indembassyankara.gov.in / cgiistanbul.gov.in
- Poland: gov.pl (Rozporządzenie RODO sayfası)
- Romania: ankara.mae.ro / mae.ro
- Vietnam: vnembassy-ankara.mofa.gov.vn
- Egypt: egyptembassy.org + current Turkish visa-agency records (Bebek)
- Italy: consistanbul.esteri.it / federcamere.it
- Indonesia: kemlu.go.id/ankara (moved to Sukarno Cd. end of 2021),
  id.wikipedia KJRI Istanbul (Dikilitaş, Beşiktaş)
- Sri Lanka: srilanka.org.tr (official)
- Portugal: ancara.embaixadaportugal.mne.gov.pt (embassy),
  portaldascomunidades.mne.gov.pt (İstanbul is an HONORARY consulate)

The ``title`` strings must match how each mission names itself in real visa
letters: Poland keeps "The ... in Istanbul", Egypt/India omit "in Istanbul",
Portugal's İstanbul office is an honorary consulate.

Keep addresses <= ~65 chars so the 8.5pt right-aligned letterhead line fits
its rect without insert_htmlbox scale_low kicking in.
"""

# country (English, as used inside the letter body) ->
#   list of missions: label (UI dropdown), title (salutation), address (letterhead)
MISSIONS = {
    "Tunisia": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of the Republic of Tunisia",
            "address": "Ferit Recai Ertuğrul Cd. No: 19, Diplomatik Site, Oran / Ankara",
        },
    ],
    "Sri Lanka": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of the Democratic Socialist Republic of Sri Lanka",
            "address": "Kırlangıç Sok. No: 41, Gaziosmanpaşa, Çankaya / Ankara",
        },
    ],
    "Italy": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of Italy",
            "address": "Atatürk Bulvarı No: 118, Kavaklıdere, Çankaya / Ankara",
        },
        {
            "label": "İstanbul — Başkonsolosluk",
            "title": "Consulate General of Italy in Istanbul",
            "address": "Tomtom Kaptan Sok. No: 5, Beyoğlu / İstanbul",
        },
    ],
    "Egypt": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of the Arab Republic of Egypt",
            "address": "Atatürk Bulvarı No: 126, Kavaklıdere, Çankaya / Ankara",
        },
        {
            "label": "İstanbul — Başkonsolosluk",
            "title": "Consulate General of the Arab Republic of Egypt",
            "address": "Cevdetpaşa Cad. No: 12, Bebek, Beşiktaş / İstanbul",
        },
    ],
    "Germany": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of the Federal Republic of Germany",
            "address": "Atatürk Bulvarı No: 114, Kavaklıdere / Ankara",
        },
        {
            "label": "İstanbul — Başkonsolosluk",
            "title": "Consulate General of the Federal Republic of Germany",
            "address": "İnönü Caddesi No: 10, 34437 Gümüşsuyu / İstanbul",
        },
    ],
    "Portugal": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of Portugal",
            "address": "Kırlangıç Sok. No: 39, Gaziosmanpaşa, Çankaya / Ankara",
        },
        {
            "label": "İstanbul — Fahri Konsolosluk",
            "title": "Honorary Consulate of Portugal in Istanbul",
            "address": "Meclisi Mebusan Cd. No: 77, Kat 5, Fındıklı, Kabataş / İstanbul",
        },
    ],
    "India": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of India",
            "address": "77, Cinnah Caddesi, Çankaya / Ankara",
        },
        {
            "label": "İstanbul — Başkonsolosluk",
            "title": "Consulate General of India",
            "address": "Cumhuriyet Cad. No: 42, Elmadag, Şişli / İstanbul",
        },
    ],
    "Vietnam": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of the Socialist Republic of Vietnam",
            "address": "414 Sokak, No: 14, Birlik Mahallesi, Çankaya / Ankara",
        },
    ],
    "Algeria": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of the People's Democratic Republic of Algeria",
            "address": "Şehit Ersan Cad. No: 42, Çankaya / Ankara",
        },
    ],
    "Romania": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of Romania",
            "address": "Güvenevler Mah., Farabi Sokak No: 27, Çankaya / Ankara",
        },
        {
            "label": "İstanbul — Başkonsolosluk",
            "title": "Consulate General of Romania in Istanbul",
            "address": "Yanarsu Sok. No: 42, Narin Sitesi, Etiler, Beşiktaş / İstanbul",
        },
    ],
    "Indonesia": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of the Republic of Indonesia",
            "address": "Sukarno Caddesi No: 24, Hilal Mahallesi, Çankaya / Ankara",
        },
        {
            "label": "İstanbul — Başkonsolosluk",
            "title": "Consulate General of the Republic of Indonesia in Istanbul",
            "address": "Dikilitaş Mah., Aşık Kerem Sok. No: 26, Beşiktaş / İstanbul",
        },
    ],
    "Poland": [
        {
            "label": "Ankara — Büyükelçilik",
            "title": "Embassy of the Republic of Poland",
            "address": "Atatürk Bulvarı No: 241, Kavaklıdere, Çankaya / Ankara",
        },
        {
            "label": "İstanbul — Başkonsolosluk",
            "title": "The Consulate General of the Republic of Poland in Istanbul",
            "address": "Eski Büyükdere Cad. No: 7, GİZ 2000 Plaza, Maslak / İstanbul",
        },
    ],
}

COUNTRY_OPTIONS = tuple(MISSIONS.keys())


def missions_for(country: str):
    return MISSIONS.get(country) or []


def mission_for(country: str, label: str):
    for m in missions_for(country):
        if m["label"] == label:
            return m
    return None