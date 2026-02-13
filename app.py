import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from sqlalchemy import text

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici MYSQL", layout="wide")

# --- 2. CONNESSIONE DB ---
# Nota: usa st.connection per MySQL
conn = st.connection('mysql', type='sql')

# --- 3. FUNZIONI DATI (MYSQL) ---
def carica_prenotazioni():
    try:
        # Usiamo ttl=0 per avere dati sempre freschi senza cache
        df = conn.query("SELECT * FROM prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m-%d')
        return df
    except Exception as e:
        st.error(f"Errore lettura Database: {e}")
        return pd.DataFrame(columns=["Data", "Struttura", "Nome", "Tel", "Note", "Prezzo_Totale", "Acconto", "Saldo"])

def salva_prenotazione(lista_p):
    try:
        with conn.session as s:
            for p in lista_p:
                query = text("""
                    INSERT INTO prenotazioni (Data, Struttura, Nome, Tel, Note, Prezzo_Totale, Acconto, Saldo) 
                    VALUES (:Data, :Struttura, :Nome, :Tel, :Note, :Prezzo_Totale, :Acconto, :Saldo)
                """)
                s.execute(query, p)
            s.commit()
        return True
    except Exception as e:
        st.error(f"Errore scrittura Database: {e}")
        return False

def elimina_prenotazione(data, struttura):
    try:
        with conn.session as s:
            query = text("DELETE FROM prenotazioni WHERE Data = :data AND Struttura = :struttura")
            s.execute(query, {"data": data, "struttura": struttura})
            s.commit()
        return True
    except Exception as e:
        st.error(f"Errore eliminazione: {e}")
        return False

# --- 4. LOGICA RADAR (Costanti e Prezzi) ---
# [Qui rimangono invariate le tue definizioni STRUTTURE e EVENTI_BASE]
STRUTTURE = {
    "Il Melograno (VILLA)": {"base": 100}, "Il Melograno (SUITE)": {"base": 60},
    "Il Melograno (FAMILY)": {"base": 75}, "Hotel Peschici": {"base": 110},
    "Residenza Il Dragone": {"base": 150}, "B&B La Sorgente": {"base": 85},
    "Suite Vista Trabucco": {"base": 220}, "Camping Int. Peschici": {"base": 55},
    "Case Bianche Centro": {"base": 95}
}
PARENT_UNIT, CHILD_UNITS = "Il Melograno (VILLA)", ["Il Melograno (SUITE)", "Il Melograno (FAMILY)"]

def calcola_prezzo_strategico(giorno, mese, anno, info):
    dt = datetime(anno, mese, giorno)
    molt = 1.0
    if mese == 8: molt = 2.4
    elif mese == 7: molt = 1.7
    if dt.weekday() >= 4: molt *= 1.15
    return int(info['base'] * molt)

# --- 5. INTERFACCIA ---
if 'mese' not in st.session_state: st.session_state.mese = 2
if 'anno' not in st.session_state: st.session_state.anno = 2026

st.title("Victory Radar Pro - MySQL Edition")

df_p = carica_prenotazioni()

# [Inserire qui la logica della tabella HTML del tuo post precedente]
# L'unica differenza è che ora df_p viene dal database!

# ESEMPIO TASTO SALVA:
# if st.form_submit_button("SALVA"):
#     nuove = [...] # lista di dizionari con i dati
#     if salva_prenotazione(nuove):
#         st.success("Salvato!")
#         st.rerun()

# ESEMPIO TASTO ELIMINA:
# if st.button("ELIMINA"):
#     if elimina_prenotazione(del_date, del_struct):
#         st.rerun()