import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from sqlalchemy import text

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Victory Radar Peschici ULTIMATE", layout="wide")

# Connessione Supabase
conn = st.connection('postgresql', type='sql', ttl=0)

if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2

STRUTTURE = {
    "Il Melograno (VILLA)":       {"base": 100},
    "Il Melograno (SUITE)":       {"base": 60},
    "Il Melograno (FAMILY)":      {"base": 75},
    "Hotel Peschici":             {"base": 110},
    "Residenza Il Dragone":       {"base": 150},
    "B&B La Sorgente":            {"base": 85},
    "Suite Vista Trabucco":       {"base": 220},
    "Camping Int. Peschici":      {"base": 55},
    "Case Bianche Centro":        {"base": 95}
}
PARENT_UNIT, CHILD_UNITS = "Il Melograno (VILLA)", ["Il Melograno (SUITE)", "Il Melograno (FAMILY)"]

EVENTI_BASE = [
    {"m": 6, "s": 20, "e": 21, "n": "TRIATHLON", "w": 1.5},
    {"m": 7, "s": 4,  "e": 5,  "n": "ZAIANA OPEN", "w": 1.6},
    {"m": 7, "s": 19, "e": 21, "n": "SANT'ELIA", "w": 2.2},
    {"m": 8, "s": 14, "e": 16, "n": "FERRAGOSTO B.", "w": 2.8},
    {"m": 8, "s": 8,  "e": 22, "n": "GOLD WEEK", "w": 2.5},
    {"m": 8, "s": 26, "e": 28, "n": "PESCHICI JAZZ", "w": 1.4},
]

# --- FUNZIONI DATI ---
def carica_prenotazioni():
    try:
        df = conn.query("SELECT * FROM prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.strftime('%Y-%m-%d')
        return df
    except: return pd.DataFrame()

def salva_prenotazione(batch):
    try:
        with conn.session as s:
            for p in batch:
                s.execute(text("""INSERT INTO prenotazioni (data, struttura, nome, tel, note, prezzo_totale, acconto, saldo) 
                                VALUES (:data, :struttura, :nome, :tel, :note, :prezzo_totale, :acconto, :saldo)"""), p)
            s.commit()
        return True
    except Exception as e:
        st.error(f"Errore: {e}")
        return False

def elimina_prenotazione(data, struttura):
    try:
        with conn.session as s:
            s.execute(text("DELETE FROM prenotazioni WHERE data = :d AND struttura = :s"), {"d": data, "s": struttura})
            s.commit()
        return True
    except: return False

def calcola_prezzo_strategico(giorno, mese, anno, info):
    dt = datetime(anno, mese, giorno)
    molt = 1.0
    if mese == 8: molt = 2.4
    elif mese == 7: molt = 1.7
    elif mese in [6, 9]: molt = 1.2
    ev_oggi = [e for e in EVENTI_BASE if e['m'] == mese and e['s'] <= giorno <= e['e']]
    if ev_oggi: molt = max(molt, max([e['w'] for e in ev_oggi]))
    if dt.weekday() >= 4: molt *= 1.15
    return int(info['base'] * molt), ev_oggi

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; background: white; border: 1px solid #a5d6a7; border-radius: 8px; }
    table { border-collapse: collapse; width: 100%; border-spacing: 0; }
    th, td { padding: 4px; text-align: center; border: 1px solid #eee; min-width: 95px; height: 75px; font-size: 11px; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 160px; z-index: 5; text-align: left; padding-left: 8px; }
    .cell-booked { background: #ffcdd2 !important; color: #b71c1c !important; font-weight: bold; }
    .cell-lock { background: #f5f5f5 !important; color: #ccc; }
    .info-price { font-size: 13px; color: #1b5e20; font-weight: 800; display: block; }
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- UI ---
def main():
    st.markdown("<h3 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PRO (Supabase)</h3>", unsafe_allow_html=True)

    n1, n2, n3 = st.columns([1, 4, 1])
    if n1.button("◀"): st.session_state.mese -= 1; st.rerun()
    n2.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h3>", unsafe_allow_html=True)
    if n3.button("▶"): st.session_state.mese += 1; st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # COSTRUZIONE TABELLA HTML
    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURE</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#e8f5e9"
        html += f'<th style="background:{bg}">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    # RIGHE STRUTTURE
    for ns, info in STRUTTURE.items():
        target_units = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        blocked_dates = df_p[df_p['struttura'].isin(target_units)]['data'].tolist() if not df_p.empty else []

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            m = df_p[(df_p['data'] == k) & (df_p['struttura'] == ns)] if not df_p.empty else pd.DataFrame()

            if k in blocked_dates: html += '<td class="cell-lock">🔒</td>'
            elif not m.empty:
                nome_c = str(m.iloc[0]["nome"]).upper()[:9]
                html += f'<td class="cell-booked">{nome_c}</td>'
            else:
                prz, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                html += f'<td><span class="info-price">€{prz}</span></td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # AREA AZIONI
    st.markdown("---")
    c_book, c_del = st.columns(2)
    with c_book:
        with st.form("bk"):
            st.subheader("📝 Prenota")
            su = st.selectbox("Unità", list(STRUTTURE.keys()))
            b1 = st.date_input("In"); b2 = st.date_input("Out")
            nm = st.text_input("Nome")
            if st.form_submit_button("SALVA PRENOTAZIONE"):
                notti = (b2-b1).days if (b2-b1).days > 0 else 1
                p_base, _ = calcola_prezzo_strategico(b1.day, b1.month, b1.year, STRUTTURE[su])
                batch = [{"data": (b1 + timedelta(days=i)).strftime("%Y-%m-%d"), "struttura": su, "nome": nm, "tel": "", "note": "", "prezzo_totale": p_base*notti, "acconto": 0, "saldo": p_base*notti} for i in range(notti)]
                if salva_prenotazione(batch): st.rerun()

    with c_del:
        st.subheader("🗑️ Elimina")
        d_day = st.date_input("Giorno")
        d_str = st.selectbox("Unità", list(STRUTTURE.keys()), key="del_s")
        if st.button("ELIMINA PRENOTAZIONE", type="primary"):
            if elimina_prenotazione(d_day.strftime("%Y-%m-%d"), d_str): st.rerun()

    with st.expander("🔍 Vedi Database"):
        st.dataframe(df_p)

if __name__ == "__main__": main()