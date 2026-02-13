import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from sqlalchemy import text

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Victory Radar Peschici PRO", layout="wide")

# Connessione PostgreSQL
try:
    conn = st.connection('postgresql', type='sql', ttl=0)
except Exception as e:
    st.error(f"Errore inizializzazione connessione: {e}")
    conn = None

if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2

# --- 2. COSTANTI ---
STRUTTURE = {
    "Il Melograno (VILLA)": {"base": 100}, "Il Melograno (SUITE)": {"base": 60},
    "Il Melograno (FAMILY)": {"base": 75}, "Hotel Peschici": {"base": 110},
    "Residenza Il Dragone": {"base": 150}, "B&B La Sorgente": {"base": 85},
    "Suite Vista Trabucco": {"base": 220}, "Camping Int. Peschici": {"base": 55},
    "Case Bianche Centro": {"base": 95}
}
PARENT_UNIT = "Il Melograno (VILLA)"
CHILD_UNITS = ["Il Melograno (SUITE)", "Il Melograno (FAMILY)"]

# --- 3. FUNZIONI DATI ---
def carica_prenotazioni():
    if conn is None: return pd.DataFrame()
    try:
        df = conn.query("SELECT * FROM prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.strftime('%Y-%m-%d')
        return df
    except Exception as e:
        st.error(f"Errore lettura: {e}")
        return pd.DataFrame()

def salva_prenotazione(batch):
    try:
        with conn.session as s:
            for p in batch:
                s.execute(text("""INSERT INTO prenotazioni (data, struttura, nome, tel, note, prezzo_totale, acconto, saldo) 
                                VALUES (:data, :struttura, :nome, :tel, :note, :prezzo_totale, :acconto, :saldo)"""), p)
            s.commit()
        return True
    except Exception as e:
        st.error(f"Errore scrittura: {e}")
        return False

def calcola_prezzo_strategico(giorno, mese, anno, info):
    dt = datetime(anno, mese, giorno)
    molt = 1.0
    if mese == 8: molt = 2.4
    elif mese == 7: molt = 1.7
    if dt.weekday() >= 4: molt *= 1.15
    return int(info['base'] * molt)

# --- 4. INTERFACCIA ---
def main():
    st.markdown("<h2 style='text-align:center; color:#2e7d32;'>Victory Radar Peschici (Supabase)</h2>", unsafe_allow_html=True)

    if conn is None:
        st.warning("In attesa di connessione al database... Controlla i Secrets.")
        return

    # Navigazione
    n1, n2, n3 = st.columns([1, 4, 1])
    if n1.button("◀"): st.session_state.mese -= 1; st.rerun()
    n2.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h3>", unsafe_allow_html=True)
    if n3.button("▶"): st.session_state.mese += 1; st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # TABELLA HTML
    st.markdown("""
        <style>
        .planning-container { overflow-x: auto; background: white; border-radius: 8px; border: 1px solid #ddd; }
        table { border-collapse: collapse; width: 100%; font-size: 11px; }
        th, td { border: 1px solid #eee; min-width: 80px; height: 45px; text-align: center; }
        .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; z-index: 5; text-align: left; padding-left: 8px; font-weight: bold; }
        .booked { background: #ffcdd2 !important; color: #b71c1c; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURA</th>'
    for d in range(1, num_days + 1):
        html += f'<th>{d}</th>'
    html += '</tr></thead><tbody>'

    for ns, info in STRUTTURE.items():
        # Blocco Villa/Suite
        target = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        blocked = df_p[df_p['struttura'].isin(target)]['data'].tolist() if not df_p.empty else []

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            res = df_p[(df_p['data'] == k) & (df_p['struttura'] == ns)] if not df_p.empty else pd.DataFrame()
            
            if k in blocked: html += '<td style="background:#f0f0f0; color:#ccc;">🔒</td>'
            elif not res.empty:
                html += f'<td class="booked">{str(res.iloc[0]["nome"])[:8]}</td>'
            else:
                p = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                html += f'<td>€{p}</td>'
        html += '</tr>'
    
    st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)

    # --- AZIONI ---
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        with st.form("bk"):
            st.subheader("📝 Nuova Prenotazione")
            f_unita = st.selectbox("Unità", list(STRUTTURE.keys()))
            f_in = st.date_input("In"); f_out = st.date_input("Out")
            f_nome = st.text_input("Nome Cliente")
            if st.form_submit_button("CONFERMA"):
                notti = (f_out - f_in).days if (f_out - f_in).days > 0 else 1
                p_base = calcola_prezzo_strategico(f_in.day, f_in.month, f_in.year, STRUTTURE[f_unita])
                payload = [{"data": (f_in + timedelta(days=i)).strftime("%Y-%m-%d"), "struttura": f_unita, "nome": f_nome, "tel": "", "note": "", "prezzo_totale": p_base*notti, "acconto": 0, "saldo": p_base*notti} for i in range(notti)]
                if salva_prenotazione(payload): st.rerun()
    
    with col2:
        st.subheader("🗑️ Stato Database")
        st.dataframe(df_p)

if __name__ == "__main__":
    main()