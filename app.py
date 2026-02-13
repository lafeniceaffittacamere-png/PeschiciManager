import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from sqlalchemy import text

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici DB-PRO", layout="wide")

# --- 2. CONNESSIONE DATABASE ---
conn = st.connection('mysql', type='sql')

# --- 3. INIZIALIZZAZIONE SESSIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2

# --- 4. COSTANTI ---
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
PARENT_UNIT = "Il Melograno (VILLA)"
CHILD_UNITS = ["Il Melograno (SUITE)", "Il Melograno (FAMILY)"]

EVENTI_BASE = [
    {"m": 6, "s": 20, "e": 21, "n": "TRIATHLON", "w": 1.5},
    {"m": 7, "s": 4,  "e": 5,  "n": "ZAIANA OPEN", "w": 1.6},
    {"m": 7, "s": 19, "e": 21, "n": "SANT'ELIA", "w": 2.2},
    {"m": 8, "s": 14, "e": 16, "n": "FERRAGOSTO B.", "w": 2.8},
    {"m": 8, "s": 8,  "e": 22, "n": "GOLD WEEK", "w": 2.5},
    {"m": 8, "s": 26, "e": 28, "n": "PESCHICI JAZZ", "w": 1.4},
]

# --- 5. FUNZIONI DATI ---
def carica_prenotazioni():
    try:
        df = conn.query("SELECT * FROM prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m-%d')
        return df
    except:
        return pd.DataFrame()

def salva_prenotazione(lista_p):
    try:
        with conn.session as s:
            for p in lista_p:
                s.execute(text("""INSERT INTO prenotazioni (Data, Struttura, Nome, Tel, Note, Prezzo_Totale, Acconto, Saldo) 
                                VALUES (:Data, :Struttura, :Nome, :Tel, :Note, :Prezzo_Totale, :Acconto, :Saldo)"""), p)
            s.commit()
        return True
    except: return False

def elimina_prenotazione(data, struttura):
    try:
        with conn.session as s:
            s.execute(text("DELETE FROM prenotazioni WHERE Data = :d AND Struttura = :s"), {"d": data, "s": struttura})
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

# --- 6. MAIN UI ---
def main():
    st.markdown("""
        <style>
        .planning-container { overflow-x: auto; background: white; border: 1px solid #ddd; border-radius: 4px; }
        table { border-collapse: collapse; width: 100%; font-family: sans-serif; font-size: 11px; }
        th, td { border: 1px solid #eee; min-width: 80px; height: 60px; text-align: center; }
        .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; z-index: 2; min-width: 150px; text-align: left; padding-left: 5px; }
        .cell-booked { background: #ffcdd2 !important; color: #b71c1c; font-weight: bold; }
        .cell-lock { background: #f0f0f0 !important; color: #ccc; }
        .info-price { color: #1b5e20; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    st.title(" Victory Radar Peschici")

    # Navigazione Mesi
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ Mese Prec."):
        st.session_state.mese -= 1
        if st.session_state.mese < 1: st.session_state.mese = 12; st.session_state.anno -= 1
        st.rerun()
    c2.subheader(f"{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}")
    if c3.button("Mese Succ. ▶"):
        st.session_state.mese += 1
        if st.session_state.mese > 12: st.session_state.mese = 1; st.session_state.anno += 1
        st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # --- GENERAZIONE HTML ---
    # Usiamo una chiave univoca basata sul tempo per forzare il refresh del DOM ed evitare il removeChild error
    tab_key = f"table_{st.session_state.mese}_{st.session_state.anno}"
    
    html = f'<div class="planning-container" id="{tab_key}"><table><thead><tr><th class="sticky-col">STRUTTURA</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#f9f9f9"
        html += f'<th style="background:{bg};">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    # Radar Eventi
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100})
        txt = " ".join([e["n"][:10] for e in evs])
        html += f'<td style="background:#fff9c4; color:#f57f17; font-size:9px;">{txt}</td>'
    html += '</tr>'

    for ns, info in STRUTTURE.items():
        target_units = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        blocked = df_p[df_p['Struttura'].isin(target_units)]['Data'].tolist() if not df_p.empty else []

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            res = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)] if not df_p.empty else pd.DataFrame()

            if k in blocked: html += '<td class="cell-lock">🔒</td>'
            elif not res.empty:
                nome = str(res.iloc[0]["Nome"])[:10]
                html += f'<td class="cell-booked">{nome}</td>'
            else:
                p, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                html += f'<td><span class="info-price">€{p}</span></td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    
    # Visualizza la tabella
    st.markdown(html, unsafe_allow_html=True)

    # --- AZIONI ---
    st.divider()
    col_a, col_b = st.columns(2)
    
    with col_a:
        with st.form("prenota"):
            st.subheader("📝 Nuova Prenotazione")
            f_str = st.selectbox("Struttura", list(STRUTTURE.keys()))
            f_in = st.date_input("In")
            f_out = st.date_input("Out")
            f_nom = st.text_input("Nome")
            f_not = st.text_input("Note")
            if st.form_submit_button("Salva"):
                notti = (f_out - f_in).days
                if notti <= 0: notti = 1
                p_base, _ = calcola_prezzo_strategico(f_in.day, f_in.month, f_in.year, STRUTTURE[f_str])
                payload = [{"Data": (f_in + timedelta(days=i)).strftime("%Y-%m-%d"), "Struttura": f_str, "Nome": f_nom, "Tel": "", "Note": f_not, "Prezzo_Totale": p_base*notti, "Acconto": 0, "Saldo": p_base*notti} for i in range(notti)]
                if salva_prenotazione(payload): st.rerun()

    with col_b:
        st.subheader("🗑️ Elimina")
        d_day = st.date_input("Giorno")
        d_str = st.selectbox("Unità", list(STRUTTURE.keys()), key="del_s")
        if st.button("Elimina"):
            if elimina_prenotazione(d_day.strftime("%Y-%m-%d"), d_str): st.rerun()

if __name__ == "__main__":
    main()