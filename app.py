import streamlit as st
import pandas as pd
from sqlalchemy import text

st.set_page_config(page_title="Victory Radar Debug", layout="wide")

st.title("🚀 Victory Radar - Allineamento Supabase")

# --- DEBUG SECRETS ---
if "connections" not in st.secrets:
    st.error("❌ Errore critico: Non trovo la sezione [connections] nei Secrets!")
elif "postgresql" not in st.secrets.connections:
    st.error("❌ Errore critico: Nei Secrets manca la sezione [connections.postgresql]!")
else:
    st.success("✅ Secrets trovati correttamente!")

# --- TENTATIVO DI CONNESSIONE ---
try:
    # Cerchiamo la connessione definita nei Secrets
    conn = st.connection('postgresql', type='sql', ttl=0)
    
    # Query di test rapida
    test_query = conn.query("SELECT current_date", ttl=0)
    st.balloons()
    st.success("🔥 CONNESSIONE STABILITA! Il database Supabase risponde correttamente.")
    st.write("Data attuale sul server:", test_query)

except Exception as e:
    st.error("❌ Impossibile stabilire la connessione.")
    st.info("Dettaglio errore tecnico:")
    st.code(str(e))

st.markdown("---")
st.write("Appena vedi i palloncini, scrivi 'Siamo dentro!' e ripristiniamo tutto il calendario.")