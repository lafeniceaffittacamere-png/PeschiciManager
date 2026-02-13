import streamlit as st
import pandas as pd

st.set_page_config(page_title="Test Connessione MySQL", layout="wide")

# 1. TENTATIVO DI CONNESSIONE
try:
    conn = st.connection('mysql', type='sql')
    st.success("✅ Connessione al server 31.11.39.174 riuscita!")
except Exception as e:
    st.error(f"❌ Errore di connessione: {e}")

# 2. LETTURA DATI (senza tabelle complicate)
st.subheader("Dati nel Database")
try:
    # ttl=0 per non avere cache
    df = conn.query("SELECT * FROM prenotazioni", ttl=0)
    
    if df.empty:
        st.info("Il database è connesso ma la tabella 'prenotazioni' è vuota.")
    else:
        st.dataframe(df) # Usa la tabella standard di Streamlit (indistruttibile)
except Exception as e:
    st.error(f"Impossibile leggere la tabella: {e}")

# 3. TEST SCRITTURA RAPIDO
st.subheader("Test Scrittura")
if st.button("Inserisci Prenotazione di Prova"):
    try:
        from sqlalchemy import text
        with conn.session as s:
            s.execute(text("INSERT INTO prenotazioni (Data, Struttura, Nome) VALUES ('2026-02-15', 'Hotel Peschici', 'TEST_LUIGI')"))
            s.commit()
        st.success("Scrittura riuscita! Ricarica la pagina.")
        st.rerun()
    except Exception as e:
        st.error(f"Errore scrittura: {e}")