import streamlit as st
import pandas as pd
from sqlalchemy import text

st.set_page_config(page_title="Victory Radar - Final Debug", layout="wide")

st.title(" Victory Radar Peschici")

# Funzione per tentare la connessione ogni volta che serve
def get_conn():
    try:
        return st.connection('mysql', type='sql', ttl=0)
    except:
        return None

conn = get_conn()

if conn:
    st.success("✅ Ponte stabilito. In attesa di risposta dal database...")
    
    # --- TEST LETTURA ---
    if st.button("🚀 TENTA LETTURA DATI"):
        try:
            # Query ultra-semplice per testare il firewall
            df = conn.query("SELECT 1 as test", ttl=0)
            st.write("🔥 Il database risponde! Ecco il test:", df)
            
            st.markdown("---")
            st.subheader("Caricamento prenotazioni...")
            df_reale = conn.query("SELECT * FROM prenotazioni LIMIT 10", ttl=0)
            st.dataframe(df_reale)
        except Exception as e:
            st.error(f"Il Firewall blocca ancora la connessione. Errore: {e}")
            st.info("Vai nel pannello Aruba e abilita l'accesso esterno (IP %) per il database Sql1816157_3.")

    # --- TEST SCRITTURA ---
    with st.expander("📝 Prova Scrittura"):
        with st.form("write"):
            nome = st.text_input("Nome")
            if st.form_submit_button("Invia"):
                try:
                    with conn.session as s:
                        s.execute(text("INSERT INTO prenotazioni (Data, Struttura, Nome) VALUES (CURDATE(), 'Test', :n)"), {"n": nome})
                        s.commit()
                    st.success("Scritto!")
                except Exception as e:
                    st.error(f"Bloccato in scrittura: {e}")
else:
    st.error("Configurazione Secrets errata o mancante.")