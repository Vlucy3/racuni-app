import streamlit as st
import gspread
from PIL import Image
import datetime
import google.generativeai as genai
import json

# --- KONFIGURACIJA STRANI ---
st.set_page_config(page_title="Beleženje računov", page_icon="💸")

# --- KONSTANTE (SEZNAMI) ---
VRSTE_ODHODKOV = [
    "1 - Material", "2 - Živila", "3 - Gradivo/Literatura", "4 - Oprema/Orodje",
    "5 - Potni stroški", "6 - Prevoz", "7 - Najem", "9 - Nastanitev",
    "10 - Kotizacija", "19 - Banka", "20 - Drugo"
]

POSTAVKE = [
    "Članarina", "Prenos iz prejšnega leta", "Usposabljanje", "Razpisi", "Občina",
    "SKVO - srečanja", "SKVO - večerja", "Potni stroški", "DSV in SZ",
    "Taborne šole", "BB", "VV", "IV", "PP", "Sklad za opremo", "Potrošni material",
    "FB in WWW", "Župnija - stroški", "Skavt za en dan", "NOV PROJEKT",
    "LMB - območni sprejem", "LMB - steg", "Zimovanje", "Zaključni piknik", "Drugo"
]

OSEBE = ["Marko", "Jerneja", "Lucija", "Polona", "Lovro", "Monika", "Jure", "Vid", "Katarina", "Hana", "Loti", "Blagajna"]

# --- API KLJUČI (SECRETS) ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = "MANJKA_KLJUC"

# Nastavitev AI modela
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except:
    pass

# --- FUNKCIJA 1: ANALIZA DOKUMENTA (AI) ---
def analyze_receipt_with_ai(input_data, mime_type):
    if "AIza" not in GOOGLE_API_KEY:
        st.warning("⚠️ Manjka Google API ključ. Ročno vnesi podatke.")
        return None

    try:
        # Uporabljamo model 2.5-flash, ki je hiter in podpira PDF
        model = genai.GenerativeModel('gemini-2.5-flash') 
        
        # Priprava seznama vrst odhodkov za prompt
        vrste_str = ", ".join(VRSTE_ODHODKOV)

        prompt = f"""
        Analiziraj ta račun. 
        1. Preberi datum, znesek, trgovino in številko računa.
        2. Poglej POSTAVKE na računu (kaj je bilo kupljeno).
        3. Glede na kupljeno blago izberi NAJBOLJ USTREZNO 'Vrsto odhodka' iz tega seznama:
        [{vrste_str}]
        
        Vrni SAMO JSON podatke brez markdown oznak:
        {{
            "trgovina": "Ime trgovine",
            "znesek": 0.00,
            "datum": "YYYY-MM-DD",
            "st_racuna": "12345",
            "vrsta_odhodka": "Točno ime iz seznama vrst odhodkov"
        }}
        Če podatka ne najdeš, pusti prazno ali 0.
        """
        
        with st.spinner('🤖 AI bere in kategorizira...'):
            content_parts = [prompt]
            
            if mime_type == "application/pdf":
                content_parts.append({
                    "mime_type": "application/pdf",
                    "data": input_data
                })
            else:
                content_parts.append(input_data)

            response = model.generate_content(content_parts)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
            
    except Exception as e:
        st.warning(f"AI ni mogel prebrati dokumenta. Vnesi ročno. (Napaka: {e})")
        return None

# --- FUNKCIJA 2: POVEZAVA Z GOOGLE SHEET ---
def connect_and_setup():
    try:
        gc = gspread.service_account(filename='service_account.json')
        try:
            LINK = st.secrets["SHEET_LINK"]
        except:
            st.error("Manjka link do tabele v secrets.toml!")
            st.stop()
        sh = gc.open_by_url(LINK)
        ws = sh.get_worksheet(0)
        return ws
    except Exception as e:
        st.error(f"Napaka pri povezavi s tabelo: {e}")
        return None

# --- GLAVNI UI DEL APLIKACIJE ---
st.title("💸 Beleženje računov")

# --- CSS STILIRANJE (PASTELNO RDEČA OPOZORILA) ---
# To bo obarvalo polja v levem stolpcu obrazca
st.markdown("""
<style>
/* Ciljamo prvi stolpec v obrazcu in selectboxe v njem */
div[data-testid="stForm"] [data-testid="column"]:nth-of-type(1) [data-testid="stSelectbox"] > div > div {
    background-color: #ffe6e6;  /* Pastelno rdeča */
    border: 2px solid #ff4b4b;  /* Temnejša rdeča obroba */
    border-radius: 5px;
}
/* Obarvamo naslove teh polj v rdečo */
div[data-testid="stForm"] [data-testid="column"]:nth-of-type(1) [data-testid="stSelectbox"] label p {
    color: #ff4b4b;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- IZBIRA NAČINA VNOSA ---
vnos_opcija = st.radio(
    "Kako želiš vnesti račun?",
    ("📷 Slikaj s kamero", "📂 Naloži datoteko (PDF/Slika)"),
    horizontal=True
)

input_file = None
mime_type = None
ai_data = None

# Logika za pridobivanje datoteke (Kamera ali Upload)
if vnos_opcija == "📷 Slikaj s kamero":
    img_file = st.camera_input("Slikaj račun")
    if img_file:
        input_file = Image.open(img_file)
        mime_type = "image/jpeg"
        st.image(input_file, caption="Posnetek računa", width=300)

else: 
    uploaded_file = st.file_uploader("Izberi račun", type=['pdf', 'jpg', 'jpeg', 'png'])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            input_file = uploaded_file.getvalue()
            mime_type = "application/pdf"
            st.info("📄 PDF datoteka naložena.")
        else:
            input_file = Image.open(uploaded_file)
            mime_type = uploaded_file.type
            st.image(input_file, caption="Naložena slika", width=300)

# Privzete vrednosti
default_date = datetime.date.today()
default_izd = ""
default_zn = 0.0
default_st = ""
default_opis = ""
default_vrsta_index = 0 

# --- OBDELAVA Z AI ---
if input_file and mime_type:
    ai_data = analyze_receipt_with_ai(input_file, mime_type)
    
    if ai_data:
        st.success("Podatki prebrani! 👇 Preveri rdeča polja!")
        if ai_data.get('trgovina'): default_izd = ai_data['trgovina']
        if ai_data.get('st_racuna'): default_st = ai_data['st_racuna']
        if ai_data.get('znesek'): default_zn = float(ai_data['znesek'])
        if ai_data.get('datum'): 
            try: 
                default_date = datetime.datetime.strptime(ai_data['datum'], "%Y-%m-%d").date()
            except: 
                pass
        
        # LOGIKA ZA VRSTO ODHODKA
        if ai_data.get('vrsta_odhodka'):
            predlagana = ai_data['vrsta_odhodka']
            if predlagana in VRSTE_ODHODKOV:
                default_vrsta_index = VRSTE_ODHODKOV.index(predlagana)
                st.info(f"💡 AI predlaga vrsto: **{predlagana}**")

st.markdown("---")
st.subheader("📝 Preveri in shrani")

# --- GLAVNI OBRAZEC ---
with st.form("vnos"):
    col1, col2 = st.columns(2)
    
    # LEVI STOLPEC (Rdeča polja zaradi CSS)
    with col1:
        d = st.date_input("Datum", default_date)
        izd = st.text_input("Trgovina/Izdajatelj", value=default_izd)
        
        st.markdown("**:red[⬇️ OBVEZNO PREVERI:]**")
        # Ta dva izbirnika bosta rdeča
        vrsta = st.selectbox("❗ Vrsta odhodka", VRSTE_ODHODKOV, index=default_vrsta_index)
        postavka = st.selectbox("❗ Postavka (Projekt/Dogodek)", POSTAVKE)
        
    # DESNI STOLPEC (Normalen)
    with col2:
        zn = st.number_input("Znesek (€)", value=default_zn, step=0.01)
        kdo = st.selectbox("Kdo je plačal?", OSEBE)
        st_rac = st.text_input("Številka računa", value=default_st)
        
    opis = st.text_input("Opis (kaj smo kupili)", value=default_opis)
    
    submit = st.form_submit_button("✅ SHRANI V TABELO")
    
    if submit:
        ws = connect_and_setup()
        if ws:
            try:
                # Priprava vrstice za Google Sheet
                # Zaporedje: Datum | Trgovina | Vrsta | Postavka | Znesek | Kdo | Opis | Št. računa
                row = [str(d), izd, vrsta, postavka, zn, kdo, opis, st_rac]
                
                ws.append_row(row)
                st.balloons()
                st.success(f"Uspešno shranjeno!\n{izd} | {zn}€ | {vrsta} | {postavka}")
            except Exception as e:
                st.error(f"Napaka pri zapisu: {e}")