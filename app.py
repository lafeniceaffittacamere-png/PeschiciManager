import streamlit as st

st.title("Controllo Motore Victory Radar")

try:
    # Proviamo a connetterci usando solo la URL dei secrets
    conn = st.connection("postgresql", type="sql")
    df = conn.query("SELECT 1", ttl=0)
    st.balloons()
    st.success("CE L'ABBIAMO FATTA! Il motore è acceso.")
    st.info("Ora posso ricaricare tutto il tuo calendario.")
except Exception as e:
    st.error("Il database non risponde ancora.")
    st.write("Errore riscontrato:", e)
    st.warning("Luigi, se non va nemmeno così, non preoccuparti. Cambiamo metodo e usiamo un file Excel su GitHub come database, che è a prova di errore!")