import streamlit as st
import pandas as pd
from sqlalchemy import text

st.set_page_config(page_title="Victory Radar - Connessione Protetta", layout="wide")

# Connessione usando il nuovo driver pymysql
try:
    conn = st.connection('mysql', type='sql')
    st.success("✅ Sistema connesso al Database Aruba (Sql1816157_3)")
except Exception as e:
    st.error(f"❌ Errore di connessione: {e}")

# Funzione per leggere i dati
def carica_prenotazioni():
    try:
        # Legge i dati reali dal database
        df = conn.query("SELECT * FROM prenotazioni ORDER BY Data DESC", ttl=0)
        return df
    except Exception as e:
        st.error(f"Errore nella lettura dei dati: {e}")
        return pd.DataFrame()

st.title(" Victory Radar Peschici - Gestione Database")

# Sezione Inserimento
with st.expander("📝 Inserisci una prenotazione di prova"):
    with st.form("test_form"):
        f_nome = st.text_input("Nome Ospite")
        f_data = st.date_input("Giorno")
        f_unita = st.selectbox("Unità", ["Hotel Peschici", "Il Melograno (VILLA)", "B&B La Sorgente"])
        if st.form_submit_button("Invia al Database"):
            try:
                with conn.session as s:
                    s.execute(
                        text("INSERT INTO prenotazioni (Data, Struttura, Nome) VALUES (:d, :s, :n)"),
                        {"d": f_data, "s": f_unita, "n": f_nome}
                    )
                    s.commit()
                st.success("Dato salvato!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore salvataggio: {e}")

# Visualizzazione Dati
st.subheader("Tabella Prenotazioni")
df = carica_prenotazioni()

if not df.empty:
    # Usiamo la tabella nativa di Streamlit: non può crashare!
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nessuna prenotazione trovata nel database.")

st.markdown("---")
st.caption("Victory Radar Pro v3.0 - MySQL Connection")