import streamlit as st
import pandas as pd
from sqlalchemy import text

# 1. Configurazione
st.set_page_config(page_title="Victory Radar Debug", layout="wide")

# 2. Connessione Blindata
# Se i Secrets sono giusti, questo non darà errori
try:
    conn = st.connection('mysql', type='sql')
except Exception as e:
    st.error(f"Errore di configurazione connessione: {e}")

# 3. Funzioni Database
def carica_dati():
    try:
        # Leggiamo i dati in modo diretto e semplice
        query = "SELECT * FROM prenotazioni ORDER BY Data DESC"
        df = conn.query(query, ttl=0)
        return df
    except Exception as e:
        st.error(f"Errore nella lettura della tabella: {e}")
        return pd.DataFrame()

# 4. Interfaccia Semplice (Per evitare il removeChild error)
st.title(" Victory Radar - MySQL Test")

# Test Scrittura
with st.expander("➕ Inserisci un test rapido"):
    t_nome = st.text_input("Nome Ospite (es. Luigi)")
    if st.button("Invia al Database"):
        try:
            with conn.session as s:
                s.execute(text("INSERT INTO prenotazioni (Data, Struttura, Nome) VALUES (CURDATE(), 'Test Unità', :nome)"), {"nome": t_nome})
                s.commit()
            st.success("Dato inviato! Ricarica la pagina.")
            st.rerun()
        except Exception as e:
            st.error(f"Errore in scrittura: {e}")

# Visualizzazione Dati (Uso st.dataframe che è indistruttibile)
st.subheader("Dati nel Database Aruba")
df_p = carica_dati()

if not df_p.empty:
    st.dataframe(df_p, use_container_width=True)
else:
    st.info("La tabella è connessa ma è ancora vuota. Inserisci un test sopra.")

st.markdown("---")
st.write("Se vedi questa pagina senza errori rossi, la connessione MySQL è PERFETTA.")