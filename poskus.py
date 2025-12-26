import streamlit as st
import gspread

st.title("🕵️ Detektiv za Datoteke")

try:
    # 1. Povezava
    gc = gspread.service_account(filename='service_account.json')
    
    # 2. Vprašamo robota, katere tabele vidi
    st.info("Preverjam, katere datoteke vidi robot ...")
    datoteke = gc.list_spreadsheet_files()
    
    if not datoteke:
        st.error("Robot ne vidi NOBENE datoteke! 😱")
        st.markdown("""
        **Možni razlogi:**
        1. Datoteka ni deljena s pravim emailom (`lucy-813...`).
        2. Datoteka je v Excel formatu (.xlsx) in ne Google Sheet formatu.
        """)
    else:
        st.success(f"Ura! Robot vidi {len(datoteke)} datotek:")
        st.markdown("---")
        for f in datoteke:
            st.markdown(f"### 📄 Ime: **{f['name']}**")
            st.code(f"{f['id']}")
            st.write("👆 Kopiraj ta ID za uporabo v programu!")
            st.markdown("---")

except Exception as e:
    st.error(f"Napaka pri povezavi: {e}")