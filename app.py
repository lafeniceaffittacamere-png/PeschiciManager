import streamlit as st
import pandas as pd
from sqlalchemy import text

st.set_page_config(page_title="Victory Radar - Gestione Database", layout="wide")

# Inizializziamo conn a None per evitare l'errore "not defined"
conn = None

# TENTATIVO DI CONNESSIONE
try:
    # Questa funzione cercherà 'username' nei tuoi Secrets
    conn = st.connection('mysql', type='sql')
    st.success("✅ Connessione al database Aruba riuscita!")
except Exception as e:
    st.error(f"❌ Errore di configurazione connessione: {e}")
    st.info("Verifica di aver scritto 'username' (non 'user') nei Secrets di Streamlit.")

st.title(" Victory Radar Peschici")

# Se la connessione esiste, procediamo con le operazioni
if conn is not None:
    
    # --- PARTE LETTURA ---
    st.subheader("Dati nel Database")
    try:
        df = conn.query("SELECT * FROM prenotazioni ORDER BY Data DESC", ttl=0)
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("La tabella è vuota. Inserisci un test qui sotto.")
    except Exception as e:
        st.error(f"Errore nella lettura della tabella: {e}")

    # --- PARTE SCRITTURA ---
    st.markdown("---")
    with st.expander("➕ Inserisci un test rapido"):
        with st.form("test_form"):
            t_nome = st.text_input("Nome Ospite")
            if st.form_submit_button("Invia al Database"):
                try:
                    with conn.session as s:
                        s.execute(
                            text("INSERT INTO prenotazioni (Data, Struttura, Nome) VALUES (CURDATE(), 'Test Unità', :nome)"),
                            {"nome": t_nome}
                        )
                        s.commit()
                    st.success("Dato inviato! Ricarica la pagina.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore in scrittura: {e}")

else:
    st.warning("Il sistema non è connesso al database. Controlla i Secrets su Streamlit Cloud.")