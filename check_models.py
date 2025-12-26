import google.generativeai as genai

# TUKAJ SPODAJ PRILEPI SVOJ KLJUČ (AIza...)
GOOGLE_API_KEY = "AIzaSyBCMWMloB6FjYGNAbfoVP-ouNnuNbWEBkY"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    
    print("------------------------------------------------")
    print("🔍 IŠČEM MODELE, KI SO TI NA VOLJO ...")
    print("------------------------------------------------")
    
    found = False
    for m in genai.list_models():
        # Iščemo samo tiste modele, ki znajo generirati vsebino (ne samo embeddignov)
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ NAJDEN: {m.name}")
            found = True
            
    if not found:
        print("❌ Noben model ni bil najden. Preveri API ključ!")
        
    print("------------------------------------------------")

except Exception as e:
    print(f"❌ Napaka: {e}")