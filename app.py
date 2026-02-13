import streamlit as st
import pandas as pd
import requests
import json
import calendar
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici ULTIMATE", layout="wide")

# --- 2. COSTANTI DI CONNESSIONE ---
# Script per SCRIVERE ed ELIMINARE
URL_SCRIPT_GOOGLE = "https://script.google.com/macros/s/AKfycby0mE0ltg7MMQlwUb-jPmLuuUD-raHRLLV1vW7wJjk8VpJZIftWZ-M8Beuvwkrf5cROKA/exec"

# Link per LEGGERE (Anti-Cache)
SHEET_ID = "1I34jTQs-qVlwqkoeUsXpHhzNBiZTLwvAVjmmjs_My-o"
URL_LETTURA_DIRETTA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Prenotazioni"

# API Key per Google Hotels
API_KEY = "1eefd886de298c71a9832a62837c0adb7ddc471ee28ded6ce24d9682f39c4ee1" 

# --- 3. INIZIALIZZAZIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2
if 'market_prices' not in st.session_state: st.session_state.market_prices = {}

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

# --- 4. FUNZIONI DATI ---
def carica_prenotazioni():
    try:
        timestamp = int(time.time())
        df = pd.read_csv(f"{URL_LETTURA_DIRETTA}&v={timestamp}")
        
        if df is not None and not df.empty:
            df.columns = [c.strip() for c in df.columns]
            df.rename(columns=lambda x: x.capitalize(), inplace=True) 
            
            if 'Data' in df.columns and 'Struttura' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
                df['Struttura'] = df['Struttura'].astype(str).str.strip()
                df = df.dropna(subset=['Data', 'Struttura'])
                return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def invia_al_cloud(payload):
    try: 
        headers = {'Content-Type': 'application/json'}
        requests.post(URL_SCRIPT_GOOGLE, data=json.dumps(payload), headers=headers)
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

def get_market_average(date_str):
    # Logica SerpApi
    params = {"engine": "google_hotels", "q": "hotel peschici foggia", "check_in_date": date_str, "api_key": API_KEY}
    try:
        res = requests.get("https://serpapi.com/search", params=params, timeout=5).json()
        prezzi = [int(''.join(filter(str.isdigit, p.get("rate_per_night", {}).get("lowest")))) for p in res.get("properties", []) if p.get("rate_per_night", {}).get("lowest")]
        return int(sum(prezzi) / len(prezzi)) if prezzi else 95
    except: return 95

# --- 5. CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; background: white; border: 1px solid #a5d6a7; border-radius: 8px; }
    table { border-collapse: separate; width: 100%; border-spacing: 0; }
    th, td { padding: 4px; text-align: center; border: 1px solid #eee; min-width: 100px; height: 80px; vertical-align: middle; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 170px; z-index: 10; font-size: 11px; text-align: left; padding-left: 8px; }
    .cell-booked { background: #ffcdd2 !important; color: #b71c1c !important; font-weight: bold; font-size: 11px; border-left: 6px solid #d32f2f !important; }
    .cell-locked { background: #eeeeee !important; color: #bbb; font-style: italic; }
    .ev-1 { color: #f57f17; font-weight: bold; font-size: 10px; line-height: 1; }
    .ev-2 { color: #8e44ad; font-weight: bold; font-size: 10px; border-top: 1px dashed #ddd; }
    .info-price { font-size: 13px; color: #1b5e20; font-weight: 800; display: block; }
    .info-market { font-size: 9px; color: #c62828; font-weight: bold; }
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 6. MAIN UI ---
def main():
    st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PRO (Google Connected)</h3>", unsafe_allow_html=True)

    if st.button("🔄 AGGIORNA DATI"):
        st.cache_data.clear()
        st.rerun()

    n1, n2, n3 = st.columns([1, 8, 1])
    if n1.button("◀"): st.session_state.mese -= 1; st.rerun()
    n2.markdown(f"<h4 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h4>", unsafe_allow_html=True)
    if n3.button("▶"): st.session_state.mese += 1; st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # TABELLA PLANNING
    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURA</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#e8f5e9"
        html += f'<th style="background:{bg}; font-size:11px;">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    # RADAR EVENTI
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100})
        txt = "".join([f'<div class="ev-{i+1}">{ev["n"][:10]}</div>' for i, ev in enumerate(evs[:2])])
        html += f'<td style="background:#fff9c4;">{txt}</td>'
    html += '</tr>'

    for ns, info in STRUTTURE.items():
        confl = []
        chk_units = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        if not df_p.empty and 'Struttura' in df_p.columns:
            confl = df_p[df_p['Struttura'].isin(chk_units)]['Data'].tolist()

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            m = pd.DataFrame()
            if not df_p.empty and 'Data' in df_p.columns:
                m = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)]

            if k in confl: 
                html += '<td class="cell-locked">🔒</td>'
            elif not m.empty:
                nome_c = str(m.iloc[0]["Nome"]).upper()[:9]
                html += f'<td class="cell-booked">{nome_c}</td>'
            else:
                prz, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                mkt = st.session_state.market_prices.get(k, "---")
                html += f'<td><span class="info-price">€{prz}</span><span class="info-market">M: {mkt}</span></td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # AREA AZIONI
    st.markdown("<br>", unsafe_allow_html=True)
    c_radar, c_book, c_del = st.columns(3)
    
    with c_radar:
        st.subheader("🚀 RADAR GOOGLE")
        # RIPRISTINATE LE DATE DI SCANSIONE COME RICHIESTO
        scan_start = st.date_input("Dal", value=datetime(st.session_state.anno, st.session_state.mese, 1))
        scan_end = st.date_input("Al", value=datetime(st.session_state.anno, st.session_state.mese, 1) + timedelta(days=6))
        
        if st.button("SCANSIONA PREZZI"):
            with st.spinner(f"Analisi mercato dal {scan_start} al {scan_end}..."):
                delta = (scan_end - scan_start).days
                for i in range(delta + 1):
                    giorno = scan_start + timedelta(days=i)
                    ds = giorno.strftime("%Y-%m-%d")
                    st.session_state.market_prices[ds] = get_market_average(ds)
                st.success("Scansione Completata!")
                st.rerun()

    with c_book:
        with st.form("bk"):
            st.subheader("📝 PRENOTA")
            su = st.selectbox("Unità", list(STRUTTURE.keys())); b1 = st.date_input("In"); b2 = st.date_input("Out")
            nm = st.text_input("Nome"); tl = st.text_input("Tel"); nt = st.text_input("Note")
            notti = (b2-b1).days if (b2-b1).days > 0 else 1
            prz_s, _ = calcola_prezzo_strategico(b1.day, b1.month, st.session_state.anno, STRUTTURE[su])
            pt = st.number_input("Totale", value=float(prz_s * notti)); ac = st.number_input("Acconto", value=0.0)
            st.write(f"Saldo: {pt-ac} €")
            if st.form_submit_button("SALVA PRENOTAZIONE"):
                nuove = []
                for i in range(notti):
                    g = (b1 + timedelta(days=i)).strftime("%Y-%m-%d")
                    nuove.append({"Data": g, "Struttura": su, "Nome": nm, "Tel": tl, "Note": nt, "Prezzo_Totale": pt, "Acconto": ac, "Saldo": pt-ac})
                
                if invia_al_cloud(nuove): 
                    with st.spinner("Sincronizzazione Cloud... (3s)"):
                        time.sleep(3) 
                        st.cache_data.clear()
                    st.success("✅ Salvato!")
                    st.rerun()

    with c_del:
        st.subheader("🗑️ ELIMINA")
        d_d = st.date_input("Giorno"); d_s = st.selectbox("Unità da liberare", list(STRUTTURE.keys()), key="del_s")
        if st.button("ELIMINA PRENOTAZIONE", type="primary"):
            if invia_al_cloud({"action": "DELETE", "date": d_d.strftime("%Y-%m-%d"), "structure": d_s}):
                with st.spinner("Cancellazione Cloud... (3s)"):
                    time.sleep(3)
                    st.cache_data.clear()
                st.success("✅ Cancellato!")
                st.rerun()

    with st.expander("🔍 DEBUG: DATI NEL CLOUD"):
        st.dataframe(df_p)

if __name__ == "__main__": main()
