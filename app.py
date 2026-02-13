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
# Script Google (Scrittura/Eliminazione)
URL_SCRIPT_GOOGLE = "https://script.google.com/macros/s/AKfycby0mE0ltg7MMQlwUb-jPmLuuUD-raHRLLV1vW7wJjk8VpJZIftWZ-M8Beuvwkrf5cROKA/exec"
# Lettura Diretta CSV (Anti-Cache)
SHEET_ID = "1I34jTQs-qVlwqkoeUsXpHhzNBiZTLwvAVjmmjs_My-o"
URL_LETTURA_DIRETTA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Prenotazioni"
# API Google Hotels (SerpApi)
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

# --- CALENDARIO EVENTI COMPLETO (TUTTI GLI EVENTI) ---
EVENTI_BASE = [
    # PRIMAVERA
    {"m": 4, "s": 4,  "e": 6,  "n": "PASQUA 2026", "w": 1.8},
    {"m": 4, "s": 24, "e": 26, "n": "PONTE 25 APRILE", "w": 1.5},
    {"m": 5, "s": 1,  "e": 3,  "n": "PONTE 1 MAGGIO", "w": 1.5},
    
    # GIUGNO
    {"m": 6, "s": 1,  "e": 2,  "n": "PONTE 2 GIUGNO", "w": 1.4},
    {"m": 6, "s": 13, "e": 14, "n": "S.ANTONIO", "w": 1.3},
    {"m": 6, "s": 20, "e": 21, "n": "TRIATHLON", "w": 1.5},
    
    # LUGLIO (Esempio sovrapposizione: Notte Rosa + Zaiana Open)
    {"m": 7, "s": 4,  "e": 5,  "n": "NOTTE ROSA", "w": 1.6},
    {"m": 7, "s": 4,  "e": 5,  "n": "ZAIANA OPEN", "w": 1.6},
    {"m": 7, "s": 11, "e": 12, "n": "FESTA DEL MARE", "w": 1.4},
    {"m": 7, "s": 19, "e": 21, "n": "SANT'ELIA (PATRONO)", "w": 2.5},
    
    # AGOSTO
    {"m": 8, "s": 1,  "e": 5,  "n": "CARPINO FOLK", "w": 1.4},
    {"m": 8, "s": 8,  "e": 22, "n": "GOLD WEEK", "w": 2.8}, 
    {"m": 8, "s": 10, "e": 11, "n": "CALICI DI STELLE", "w": 1.5},
    {"m": 8, "s": 14, "e": 16, "n": "FERRAGOSTO", "w": 3.0},
    {"m": 8, "s": 24, "e": 28, "n": "PESCHICI JAZZ", "w": 1.5},
    
    # SETTEMBRE
    {"m": 9, "s": 7,  "e": 8,  "n": "MADONNA DI LORETO", "w": 1.4},
    {"m": 9, "s": 19, "e": 20, "n": "GARGANO RUN", "w": 1.2},
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
    params = {"engine": "google_hotels", "q": "hotel peschici foggia", "check_in_date": date_str, "api_key": API_KEY}
    try:
        res = requests.get("https://serpapi.com/search", params=params, timeout=5).json()
        prezzi = [int(''.join(filter(str.isdigit, p.get("rate_per_night", {}).get("lowest")))) for p in res.get("properties", []) if p.get("rate_per_night", {}).get("lowest")]
        return int(sum(prezzi) / len(prezzi)) if prezzi else 95
    except: return 95

# --- 5. CSS RESPONSIVE (MOBILE & DESKTOP) ---
st.markdown("""
    <style>
    /* STILE GENERALE */
    .stApp { background-color: #f1f8e9; }
    
    /* TABELLA PLANNING SCORREVOLE */
    .planning-container { 
        overflow-x: auto; 
        background: white; 
        border: 1px solid #a5d6a7; 
        border-radius: 8px; 
        -webkit-overflow-scrolling: touch; 
    }
    
    table { border-collapse: separate; width: 100%; border-spacing: 0; }
    
    /* CELLE */
    th, td { 
        padding: 4px; 
        text-align: center; 
        border: 1px solid #eee; 
        min-width: 90px; 
        height: 70px; 
        vertical-align: middle; 
    }
    
    /* COLONNA FISSA (NOMI STRUTTURE) */
    .sticky-col { 
        position: sticky; 
        left: 0; 
        background: #2e7d32; 
        color: white; 
        font-weight: bold; 
        min-width: 160px; 
        z-index: 10; 
        font-size: 11px; 
        text-align: left; 
        padding-left: 8px; 
        box-shadow: 2px 0 5px rgba(0,0,0,0.1); 
    }

    /* STATI CELLE */
    .cell-booked { background: #ffcdd2 !important; color: #b71c1c !important; font-weight: bold; font-size: 10px; border-left: 4px solid #d32f2f !important; }
    .cell-locked { background: #eeeeee !important; color: #bbb; font-style: italic; }
    
    /* CLASSI PER EVENTI MULTIPLI */
    .ev-1 { color: #f57f17; font-weight: bold; font-size: 9px; line-height: 1.1; margin-bottom: 2px; }
    .ev-2 { color: #8e44ad; font-weight: bold; font-size: 9px; line-height: 1.1; border-top: 1px dashed #ccc; padding-top: 1px; }
    
    .info-price { font-size: 13px; color: #1b5e20; font-weight: 800; display: block; }
    .info-market { font-size: 9px; color: #c62828; font-weight: bold; }
    header {visibility: hidden;}

    /* MEDIA QUERY PER CELLULARE */
    @media only screen and (max-width: 768px) {
        th, td { min-width: 60px; font-size: 10px; height: 60px; }
        .sticky-col { min-width: 100px; font-size: 10px; padding-left: 2px; }
        .info-price { font-size: 11px; }
        .info-market { display: none; } 
        h3 { font-size: 18px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 6. MAIN UI ---
def main():
    st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PRO</h3>", unsafe_allow_html=True)

    if st.button("🔄 AGGIORNA DATI"):
        st.cache_data.clear()
        st.rerun()

    # --- NAVIGAZIONE MESI ---
    c1, c2, c3 = st.columns([1, 6, 1])
    
    if c1.button("◀"): 
        st.session_state.mese -= 1
        if st.session_state.mese < 1: 
            st.session_state.mese = 12; st.session_state.anno -= 1
        st.rerun()
        
    c2.markdown(f"<h4 style='text-align:center; margin:0;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h4>", unsafe_allow_html=True)
    
    if c3.button("▶"): 
        st.session_state.mese += 1
        if st.session_state.mese > 12: 
            st.session_state.mese = 1; st.session_state.anno += 1
        st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # --- TABELLA PLANNING ---
    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURA</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#e8f5e9"
        html += f'<th style="background:{bg}; font-size:10px;">{d}<br>{dt_t.strftime("%a")[0]}</th>'
    html += '</tr></thead><tbody>'

    # RIGA EVENTI (MODIFICATA: MOSTRA TUTTI GLI EVENTI)
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100})
        if evs:
            # Qui costruiamo il contenuto della cella mostrando TUTTI gli eventi
            # Il primo avrà classe ev-1 (arancione), il secondo ev-2 (viola)
            txt = ""
            for i, ev in enumerate(evs):
                cls = "ev-1" if i == 0 else "ev-2"
                txt += f'<div class="{cls}">{ev["n"][:10]}</div>'
            html += f'<td style="background:#fff9c4;">{txt}</td>'
        else:
             html += f'<td style="background:#fff9c4;"></td>'
    html += '</tr>'

    # RIGHE STRUTTURE
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
                nome_c = str(m.iloc[0]["Nome"]).upper()[:6] 
                html += f'<td class="cell-booked">{nome_c}</td>'
            else:
                prz, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                mkt = st.session_state.market_prices.get(k, "")
                mkt_html = f'<span class="info-market">M:{mkt}</span>' if mkt else ""
                html += f'<td><span class="info-price">€{prz}</span>{mkt_html}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # --- AREA AZIONI (TABS PER MOBILE) ---
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📝 PRENOTA", "🗑️ ELIMINA", "🚀 RADAR GOOGLE"])
    
    with tab1:
        with st.form("bk"):
            c_a, c_b = st.columns(2)
            with c_a: su = st.selectbox("Unità", list(STRUTTURE.keys()))
            with c_b: nm = st.text_input("Nome Ospite")
            c_c, c_d = st.columns(2)
            with c_c: b1 = st.date_input("Check-in")
            with c_d: b2 = st.date_input("Check-out")
            tl = st.text_input("Telefono / Note")
            
            notti = (b2-b1).days if (b2-b1).days > 0 else 1
            prz_s, _ = calcola_prezzo_strategico(b1.day, b1.month, st.session_state.anno, STRUTTURE[su])
            
            c_e, c_f = st.columns(2)
            with c_e: pt = st.number_input("Totale (€)", value=float(prz_s * notti))
            with c_f: ac = st.number_input("Acconto (€)", value=0.0)
            
            st.info(f"Saldo da incassare: **{pt-ac} €**")
            
            if st.form_submit_button("💾 SALVA PRENOTAZIONE", type="primary"):
                nuove = []
                for i in range(notti):
                    g = (b1 + timedelta(days=i)).strftime("%Y-%m-%d")
                    nuove.append({"Data": g, "Struttura": su, "Nome": nm, "Tel": tl, "Note": "", "Prezzo_Totale": pt, "Acconto": ac, "Saldo": pt-ac})
                
                if invia_al_cloud(nuove): 
                    with st.spinner("Salvataggio..."):
                        time.sleep(3) 
                        st.cache_data.clear()
                    st.success("Fatto!")
                    st.rerun()

    with tab2:
        st.write("### Cancellazione Intelligente")
        if not df_p.empty and 'Data' in df_p.columns and 'Nome' in df_p.columns:
            df_view = df_p.sort_values(by=['Struttura', 'Data'])
            gruppi = {}
            for _, row in df_view.iterrows():
                key = f"{row['Nome']} - {row['Struttura']}"
                if key not in gruppi: gruppi[key] = []
                gruppi[key].append(row['Data'])
            
            opzioni_menu = []
            mappa_date = {} 
            for key, date_list in gruppi.items():
                date_list.sort()
                start = date_list[0]; end = date_list[-1]
                label = f"{key} | {start} -> {end} ({len(date_list)} notti)"
                opzioni_menu.append(label)
                nome, struttura = key.split(" - ")
                mappa_date[label] = {"struttura": struttura, "date": date_list}
            
            if opzioni_menu:
                scelta = st.selectbox("Seleziona gruppo:", opzioni_menu)
                if st.button("❌ ELIMINA GRUPPO", type="primary"):
                    dati = mappa_date[scelta]
                    progresso = st.progress(0)
                    for i, giorno in enumerate(dati["date"]):
                        invia_al_cloud({"action": "DELETE", "date": giorno, "structure": dati["struttura"]})
                        progresso.progress((i + 1) / len(dati["date"]))
                        time.sleep(0.3)
                    st.success("Cancellato!")
                    time.sleep(1); st.cache_data.clear(); st.rerun()
            else:
                st.info("Nessuna prenotazione attiva.")
        else:
            st.info("Lista vuota.")

    with tab3:
        st.write("### Scansione Competitor")
        scan_start = st.date_input("Dal", value=datetime(st.session_state.anno, st.session_state.mese, 1))
        scan_end = st.date_input("Al", value=datetime(st.session_state.anno, st.session_state.mese, 1) + timedelta(days=6))
        if st.button("🔎 AVVIA SCANSIONE"):
            with st.spinner("Analisi mercato Google Hotels..."):
                delta = (scan_end - scan_start).days
                for i in range(delta + 1):
                    giorno = scan_start + timedelta(days=i)
                    ds = giorno.strftime("%Y-%m-%d")
                    st.session_state.market_prices[ds] = get_market_average(ds)
                st.rerun()

    with st.expander("Debug Dati"):
        st.dataframe(df_p)

if __name__ == "__main__": main()
