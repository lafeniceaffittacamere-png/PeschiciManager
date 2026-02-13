import streamlit as st
import pandas as pd

st.set_page_config(page_title="Victory Radar - Connessione Finale")

st.title("🔗 Test Connessione Supabase")

try:
    # Stabiliamo la connessione
    conn = st.connection('postgresql', type='sql', ttl=0)
    
    # Query di test
    df = conn.query("SELECT 'Siamo online!' as status", ttl=0)
    
    st.success("✅ CE L'ABBIAMO FATTA!")
    st.balloons()
    st.write(df)
    
except Exception as e:
    st.error("❌ Errore di connessione")
    st.info("Controlla di aver usato l'HOST del POOLER (porta 6543) e non quello diretto.")
    st.code(str(e))