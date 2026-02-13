import streamlit as st
from streamlit_gsheets import GSheetsConnection
import calendar
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici CLOUD", layout="wide")

# --- 2. INIZIALIZZAZIONE STATO ---
if 'anno' not in st.session_state:
    st.session_state.anno = 2026
if 'mese' not in st.session_state:
    st.session_state.mese = datetime.now().month
if 'market_prices' not in st.session_state:
    st.session_state.market_prices = {}

# --- 3. CONNESSIONE GOOGLE SHEETS & API ---
# Questa riga collega l'app al tuo Foglio Google online
conn = st.connection("gsheets", type=GSheetsConnection)

API_KEY = "1eefd886de298c71a9832a62837c0adb7ddc471ee28ded6ce24d9682f39c4ee1" 

STRUTTURE = {
    "Il Melograno (VILLA)":       {"base": 100, "pulizie": 40},
    "Il Melograno (SUITE)":       {"base": 60,  "pulizie": 20},
    "Il Melograno (FAMILY)":      {"base": 75,  "pulizie": 25},
    "Hotel Peschici":             {"base": 110, "pulizie": 0},
    "Residenza Il Dragone":       {"base": 150, "pulizie": 30},
    "B&B La Sorgente":            {"base": 85,  "pulizie": 15},
    "Suite Vista Trabucco":       {"base": 220, "pulizie": 50},
    "Camping Int. Peschici":      {"base": 55,  "pulizie": 20},
    "Case Bianche Centro":        {"base": 95,  "pulizie": 35}
}

MELOGRANO_UNITS = [k for k in STRUTTURE.keys() if "Il Melograno" in k]
EVENTI_BASE = [
    {"m": 6, "s": 20, "e": 21, "n": "TRIATHLON", "w": 1.5},
    {"m": 7, "s": 4,  "e": 5,  "n": "ZAIANA OPEN", "w": 1.6},
    {"m": 7, "s": 19, "e": 21, "n": "SANT'ELIA", "w": 2.2},
    {"m": 8, "s": 14, "e": 16, "n": "FERRAGOSTO B.", "w": 2.8},
    {"m": 8, "s": 8,  "e": 22, "n": "GOLD WEEK", "w": 2.5},
    {"m": 8, "s": 26, "e": 28, "n": "PESCHICI JAZZ", "w": 1.4},
]

# --- 4. FUNZIONI DATI (CLOUD) ---
def carica_prenotazioni_cloud():
    try:
        return conn.read(worksheet="Prenotazioni")
    except:
        return pd.DataFrame(columns=["Data", "Struttura", "Nome", "Tel", "Prezzo"])

def salva_prenotazione_cloud(nuovi_dati_df):
    df_esistente = carica_prenotazioni_cloud()
    df_finale = pd.concat([df_esistente, nuovi_dati_df], ignore_index=True)
    conn.update(worksheet="Prenotazioni", data=df_finale)

# --- 5. LOGICA PREZZI ---
def get_market_average(date_str):
    check_out = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    params = {"engine": "google_hotels", "q": "hotel peschici foggia", "check_in_date": date_str, "check_out_date": check_out, "currency": "EUR", "api_key": API_KEY}
    try:
        res = requests.get("https://serpapi.com/search", params=params, timeout=10).json()
        prezzi = [int(''.join(filter(str.isdigit, p.get("rate_per_night", {}).get("lowest")))) for p in res.get("properties", []) if p.get("rate_per_night", {}).get("lowest")]
        return sum(prezzi) / len(prezzi) if prezzi else 95.0
    except: return 95.0

def calcola_prezzo_strategico(giorno, mese, anno, info, eventi_db):
    dt = datetime(anno, mese, giorno)
    molt = 1.0
    if mese == 8: molt = 2.4
    elif mese == 7: molt = 1.7
    elif mese in [6, 9]: molt = 1.2
    elif mese in [4, 5]: molt = 0.8
    ev_trovati = [e for e in eventi_db if e['m'] == mese and e['s'] <= giorno <= e['e']]
    if ev_trovati:
        peso_max = max([e['w'] for e in ev_trovati])
        if peso_max > molt: molt = peso_max
    if dt.weekday() >= 4: molt *= 1.15
    return int(info['base'] * molt), ev_trovati

# --- 6. CSS VICTORY COMPACT ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; padding-bottom: 20px; background: white; border: 1px solid #a5d6a7; border-radius: 6px; }
    table.victory-table { border-collapse: separate; border-spacing: 0; width: 100%; font-family: 'Segoe UI', sans-serif; }
    th, td { padding: 4px; text-align: center; border-right: 1px solid #eee; border-bottom: 1px solid #eee; min-width: 95px; height: 65px; vertical-align: middle; }
    th.date-header { position: sticky; top: 0; background-color: #e8f5e9; color: #1b5e20; z-index: 10; border-bottom: 2px solid #81c784; font-size: 11px; }
    .sticky-col { position: sticky; left: 0; background-color: #2e7d32; z-index: 11; color: white; text-align: left; padding-left: 8px; min-width: 150px; font-weight: bold; font-size: 11px; }
    .cell-event { background-color: #fff9c4; font-weight: bold; color: #f57f17; font-size: 9px; line-height: 1.1; }
    .cell-booked { background-color: #ffcdd2 !important; color: #b71c1c !important; border-left: 3px solid #d32f2f; font-weight: bold; text-align: left; padding-left: 4px; font-size: 10px; }
    .info-price { font-size: 13px; color: #1b5e20; font-weight: 800; display: block; }
    .info-market { font-size: 9px; color: #c62828; display: block; font-weight: bold; margin-top: 2px; }
    .section-box { background: white; padding: 12px; border-radius: 8px; border: 1px solid #a5d6a7; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 7. MAIN UI ---
def main():
    st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PESCHICI PRO</h3>", unsafe_allow_html=True)

    # Navigazione
    c1, c2, c3 = st.columns([1, 8, 1])
    if c1.button("◀"):
        st.session_state.mese -= 1
        if st.session_state.mese < 1: st.session_state.mese=12; st.session_state.anno-=1
        st.rerun()
    c2.markdown(f"<h4 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h4>", unsafe_allow_html=True)
    if c3.button("▶"):
        st.session_state.mese += 1
        if st.session_state.mese > 12: st.session_state.mese=1; st.session_state.anno+=1
        st.rerun()

    # Caricamento dati
    df_pren = carica_prenotazioni_cloud()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # Tabella HTML
    html = '<div class="planning-container"><table class="victory-table"><thead><tr><th class="sticky-col">STRUTTURE</th>'
    for d in range(1, num_days + 1):
        html += f'<th class="date-header">{d}</th>'
    html += '</tr></thead><tbody>'

    # Riga Radar Eventi
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100}, EVENTI_BASE)
        txt = evs[0]['n'][:10] if evs else ""
        html += f'<td class="cell-event">{txt}</td>'
    html += '</tr>'

    # Righe Strutture
    for nome_s, info in STRUTTURE.items():
        html += f'<tr><td class="sticky-col">{nome_s}</td>'
        for d in range(1, num_days + 1):
            key_str = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            
            # Controllo prenotazione
            match = df_pren[(df_pren['Data'] == key_str) & (df_pren['Struttura'] == nome_s)]
            
            if not match.empty:
                ospite = match.iloc[0]['Nome']
                html += f'<td class="cell-booked">{str(ospite)[:8]}</td>'
            else:
                prezzo, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info, EVENTI_BASE)
                mkt = st.session_state.market_prices.get(key_str, "---")
                html += f'<td class="cell-free"><span class="info-price">€{prezzo}</span><span class="info-market">M: {mkt}</span></td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # Azioni
    col_a, col_b, col_c = st.columns(3)
    with col_b:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        if st.button("🚀 SCANSIONA MERCATO GOOGLE", use_container_width=True):
            with st.spinner("Analisi in corso..."):
                for d in range(1, 8): # Scansiona la prossima settimana per velocità
                    ds = (datetime.now() + timedelta(days=d)).strftime("%Y-%m-%d")
                    st.session_state.market_prices[ds] = int(get_market_average(ds))
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_c:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        with st.form("book"):
            s_u = st.selectbox("Unità", MELOGRANO_UNITS)
            d_u = st.date_input("Data")
            n_u = st.text_input("Nome")
            if st.form_submit_button("CONFERMA"):
                nuova = pd.DataFrame([{"Data": d_u.strftime("%Y-%m-%d"), "Struttura": s_u, "Nome": n_u, "Tel": "", "Prezzo": 0}])
                salva_prenotazione_cloud(nuova)
                st.success("Salvato su Google Sheets!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()