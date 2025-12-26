import streamlit as st
import gspread
from PIL import Image
import datetime
import google.generativeai as genai
import json

# --- KONFIGURACIJA ---
st.set_page_config(page_title="Pametni Skavtski Računi", page_icon="💸")

KATEGORIJE = [
    "1 - Material", "2 - Živila", "3 - Gradivo/Literatura", "4 - Oprema/Orodje",
    "5 - Potni stroški", "6 - Prevoz", "7 - Najem", "9 - Nastanitev",
    "10 - Kotizacija", "19 - Banka", "20 - Drugo"
]
OSEBE = ["Marko", "Jerneja", "Lucija", "Polona", "Lovro", "Monika", "Jure", "Vid", "Katarina", "Hana", "Loti", "Blagajna"]

# ---------------------------------------------------------
# 🔑 TUKAJ PRILEPI SVOJ GOOGLE GEMINI API KLJUČ (AIza...)
# ---------------------------------------------------------
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # Za lokalno testiranje (če nimaš nastavljenih secrets)
    GOOGLE_API_KEY = "TU_NI_KLJUČA"

# Nastavitev AI modela
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except:
    pass # Če ključ manjka, bomo opozorili kasneje znotraj funkcije

# --- FUNKCIJA ZA BRANJE RAČUNA (AI) ---
def analyze_receipt_with_ai(image):
    # Preverimo API ključ
    if "AIza" not in GOOGLE_API_KEY:
        st.error("Manjka Google API ključ! Preveri secrets ali kodo.")
        return None

    try:
        # Uporabimo model flash, ki je hiter in učinkovit
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """
        Analiziraj ta račun. Iščem te podatke:
        1. Ime trgovine/izdajatelja (npr. CONAD, SPAR, ...)
        2. Končni znesek (kot decimalna številka)
        3. Datum računa (format YYYY-MM-DD)
        4. Številka računa (če obstaja)

        Vrni mi SAMO čisti JSON v takšni obliki, brez dodatnega besedila ali markdown oznak:
        {
            "trgovina": "Ime",
            "znesek": 0.00,
            "datum": "YYYY-MM-DD",
            "st_racuna": "123"
        }
        """
        
        with st.spinner('🤖 AI bere račun...'):
            # Pošljemo sliko in navodila
            response = model.generate_content([prompt, image])
            
            # Očistimo odgovor, če AI doda "```json"
            text = response.text.replace('```json', '').replace('```', '').strip()
            
            return json.loads(text)
            
    except Exception as e:
        st.warning(f"AI ni moral prebrati računa (napaka: {e})")
        return None

# --- POVEZAVA Z GOOGLE SHEET ---
def connect_and_setup():
    # 1. Povezava na service account
    try:
        gc = gspread.service_account(filename='service_account.json')
    except FileNotFoundError:
        st.error("Manjka datoteka 'service_account.json'!")
        st.stop()

    # 2. Pridobivanje linka do tabele
    try:
        LINK = st.secrets["SHEET_LINK"]
    except:
        # Če ni v secrets, uporabimo tvoj hardcoded link
        LINK = "[https://docs.google.com/spreadsheets/d/1j58PhPgJXjxwKqnuMPJ4xdlWZttViwo0dBXf_Vt_AaI/edit?gid=0#gid=0](https://docs.google.com/spreadsheets/d/1j58PhPgJXjxwKqnuMPJ4xdlWZttViwo0dBXf_Vt_AaI/edit?gid=0#gid=0)" 
    
    # 3. Odpiranje in priprava tabele
    try:
        sh = gc.open_by_url(LINK)
        ws = sh.get_worksheet(0)
        
        # Če je tabela prazna, dodamo naslovno vrstico
        if not ws.row_values(1):
            ws.append_row(["Datum", "Izdajatelj", "Kategorija", "Znesek", "Kdo je plačal", "Opis", "Št. računa"])
        
        return ws
        
    except Exception as e:
        st.error(f"Napaka pri povezavi s tabelo: {e}")
        st.stop()

# --- APLIKACIJA ---
st.title("💸 Pametni Skavtski Računi")

img_file = st.camera_input("Slikaj račun")

# Privzete vrednosti
default_date = datetime.date.today()
default_izd = ""
default_zn = 0.0
default_st = ""

if img_file:
    image = Image.open(img_file)
    st.image(image, caption="Račun", width=300)
    
    # Klic AI funkcije