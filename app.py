import streamlit as st
from streamlit_gsheets import GSheetsConnection
import calendar
import pandas as pd
import requests
import json
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici ULTIMATE", layout="wide")

# --- 2. IL TUO NUOVO URL CLOUD (VERSIONE 2) ---
URL_SCRIPT_GOOGLE = "https://script.google.com/macros/s/AKfycbyTvoDo6v9PwwdcyK3V6PKlkLS8gMi7PqEE79dfdRMoiRhMj7MWmIMbCT6OTfN62Uyc/exec"

# --- 3. INIZIALIZZAZIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2
if 'market_prices' not in st.session_state: st.session_state.market_prices = {}

conn = st.connection("gsheets", type=GSheetsConnection)
API_KEY = "1eefd886de298c71a9832a62837c0adb7ddc471ee28ded6ce24d9682f39c4ee1" 

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

MELOGRANO_UNITS = [k for k in STRUTTURE.keys() if "Il Melograno" in k]
PARENT_UNIT, CHILD_UNITS = "Il Melograno (VILLA)", ["Il Melograno (SUITE)", "Il Melograno (FAMILY)"]

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
        df = conn.read(worksheet="Prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df.columns = [c.strip() for c in df.columns]
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['Struttura'] = df['Struttura'].astype(str).str.strip()
            df = df.dropna(subset=['Data', 'Struttura'])
        return df
    except: return pd.DataFrame(columns=["Data", "Struttura", "Nome", "Tel", "Note", "Prezzo_Totale", "Acconto", "Saldo"])

def invia_al_cloud(payload):
    try: 
        r = requests.post(URL_SCRIPT_GOOGLE, data=json.dumps(payload))
        return r.status_code == 200
    except: return False

# --- 5. LOGICA PREZZI ---
def get_market_average(date_str):
    check_out = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    params = {"engine": "google_hotels", "q": "hotel peschici foggia", "check_in_date": date_str, "check_out_date": check_out, "api_key": API_KEY}
    try:
        res = requests.get("https://serpapi.com/search", params=params, timeout=10).json()
        prezzi = [int(''.join(filter(str.isdigit, p.get("rate_per_night", {}).get("lowest")))) for p in res.get("properties", []) if p.get("rate_per_night", {}).get("lowest")]
        return sum(prezzi) / len(prezzi) if prezzi else 95.0
    except: return 95.0

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

# --- 6. CSS (CELLE GRANDI E VISIBILI) ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; background: white; border: 1px solid #a5d6a7; border-radius: 8px; }
    table.victory-table { border-collapse: separate; width: 100%; border-spacing: 0; }
    th, td { padding: 4px; text-align: center; border: 1px solid #eee; min-width: 100px; height: 80px; vertical-align: middle; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 170px; z-index: 10; font-size: 11px; text-align: left; padding-left: 8px; }
    .cell-booked { background: #ffcdd2 !important; color: #b71c1c !important; font-weight: bold; font-size: 11px; border-left: 6px solid #d32f2f !important; }
    .ev-1 { color: #f57f17; font-weight: bold; font-size: 10px; }
    .ev-2 { color: #8e44ad; font-weight: bold; font-size: 10px; border-top: 1px dashed #ddd; }
    .info-price { font-size: 13px; color: #1b5e20; font-weight: 800; display: block; }
    .info-market { font-size: 9px; color: #c62828; font-weight: bold; }
    .section-box { background: white; padding: 12px; border-radius: 8px; border: 1px solid #a5d6a7; }
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 7. MAIN UI ---
def main():
    st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PRO {st.session_state.anno}</h3>", unsafe_allow_html=True)

    n1, n2, n3 = st.columns([1, 8, 1])
    if n1.button("◀"): st.session_state.mese -= 1; st.rerun()
    n2.markdown(f"<h4 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()}</h4>", unsafe_allow_html=True)
    if n3.button("▶"): st.session_state.mese += 1; st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # TABELLA
    html = '<div class="planning-container"><table class="victory-table"><thead><tr><th class="sticky-col">STRUTTURE</th>'
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
        if not df_p.empty: confl = df_p[df_p['Struttura'].isin(chk_units)]['Data'].tolist()

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            m = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)] if not df_p.empty else pd.DataFrame()

            if k in confl: html += '<td style="background:#eeeeee; color:#bbb;">🔒</td>'
            elif not m.empty:
                nome_ospite = str(m.iloc[0]["Nome"]).upper()[:10]
                html += f'<td class="cell-booked">{nome_ospite}</td>'
            else:
                prz, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                mkt = st.session_state.market_prices.get(k, "---")
                html += f'<td><span class="info-price">€{prz}</span><span class="info-market">M: {mkt}</span></td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # AZIONI
    st.markdown("<br>", unsafe_allow_html=True)
    c_radar, c_book, c_del = st.columns([1, 1, 1])

    with c_radar:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("🚀 RADAR GOOGLE")
        r1, r2 = st.columns(2); d1 = r1.date_input("Inizio", datetime.now()); d2 = r2.date_input("Fine", datetime.now() + timedelta(days=5))
        if st.button("SCANSIONA GOOGLE", use_container_width=True):
            with st.spinner("Analisi prezzi..."):
                tmp = d1
                while tmp <= d2:
                    ds = tmp.strftime("%Y-%m-%d")
                    st.session_state.market_prices[ds] = int(get_market_average(ds))
                    tmp += timedelta(days=1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c_book:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        with st.form("bk"):
            st.subheader("📝 PRENOTA")
            su = st.selectbox("Unità", list(STRUTTURE.keys())); b1 = st.date_input("In"); b2 = st.date_input("Out")
            nm = st.text_input("Nome"); tl = st.text_input("Tel"); nt = st.text_input("Note")
            notti = (b2-b1).days if (b2-b1).days > 0 else 1
            prz_s, _ = calcola_prezzo_strategico(b1.day, b1.month, st.session_state.anno, STRUTTURE[su])
            pt = st.number_input("Totale (€)", value=float(primport streamlit as st
from streamlit_gsheets import GSheetsConnection
import calendar
import pandas as pd
import requests
import json
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici ULTIMATE", layout="wide")

# --- 2. LINK CLOUD (VERSIONE 2 - QUELLA CHE FUNZIONA PER ELIMINARE) ---
URL_SCRIPT_GOOGLE = "https://script.google.com/macros/s/AKfycbyTvoDo6v9PwwdcyK3V6PKlkLS8gMi7PqEE79dfdRMoiRhMj7MWmIMbCT6OTfN62Uyc/exec"

# --- 3. INIZIALIZZAZIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2
if 'market_prices' not in st.session_state: st.session_state.market_prices = {}

conn = st.connection("gsheets", type=GSheetsConnection)
API_KEY = "1eefd886de298c71a9832a62837c0adb7ddc471ee28ded6ce24d9682f39c4ee1" 

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

MELOGRANO_UNITS = [k for k in STRUTTURE.keys() if "Il Melograno" in k]
PARENT_UNIT, CHILD_UNITS = "Il Melograno (VILLA)", ["Il Melograno (SUITE)", "Il Melograno (FAMILY)"]

EVENTI_BASE = [
    {"m": 6, "s": 20, "e": 21, "n": "TRIATHLON", "w": 1.5},
    {"m": 7, "s": 4,  "e": 5,  "n": "ZAIANA OPEN", "w": 1.6},
    {"m": 7, "s": 19, "e": 21, "n": "SANT'ELIA", "w": 2.2},
    {"m": 8, "s": 14, "e": 16, "n": "FERRAGOSTO B.", "w": 2.8},
    {"m": 8, "s": 8,  "e": 22, "n": "GOLD WEEK", "w": 2.5},
    {"m": 8, "s": 26, "e": 28, "n": "PESCHICI JAZZ", "w": 1.4},
]

# --- 4. FUNZIONI DATI (ANTI-ERRORE) ---
def carica_prenotazioni():
    try: 
        df = conn.read(worksheet="Prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df.columns = [c.strip() for c in df.columns]
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['Struttura'] = df['Struttura'].astype(str).str.strip()
            df = df.dropna(subset=['Data', 'Struttura'])
        return df
    except: return pd.DataFrame(columns=["Data", "Struttura", "Nome", "Tel", "Note", "Prezzo_Totale", "Acconto", "Saldo"])

def carica_eventi_manuali():
    try: 
        df = conn.read(worksheet="Eventi", ttl=0)
        return df if df is not None else pd.DataFrame()
    except: return pd.DataFrame()

def invia_al_cloud(payload):
    try: return requests.post(URL_SCRIPT_GOOGLE, data=json.dumps(payload)).status_code == 200
    except: return False

# --- 5. LOGICA PREZZI & RADAR ---
def get_market_average(date_str):
    check_out = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    params = {"engine": "google_hotels", "q": "hotel peschici foggia", "check_in_date": date_str, "check_out_date": check_out, "api_key": API_KEY}
    try:
        res = requests.get("https://serpapi.com/search", params=params, timeout=10).json()
        prezzi = [int(''.join(filter(str.isdigit, p.get("rate_per_night", {}).get("lowest")))) for p in res.get("properties", []) if p.get("rate_per_night", {}).get("lowest")]
        return sum(prezzi) / len(prezzi) if prezzi else 95.0
    except: return 95.0

def calcola_prezzo_strategico(giorno, mese, anno, info, df_e):
    dt = datetime(anno, mese, giorno)
    molt = 1.0
    if mese == 8: molt = 2.4
    elif mese == 7: molt = 1.7
    elif mese in [6, 9]: molt = 1.2
    
    tutti = EVENTI_BASE.copy()
    if df_e is not None and not df_e.empty:
        for _, r in df_e.iterrows():
            tutti.append({"m": int(r['Mese']), "s": int(r['Inizio']), "e": int(r['Fine']), "n": str(r['Nome']), "w": float(r['Peso'])})
    
    ev_oggi = [e for e in tutti if e['m'] == mese and e['s'] <= giorno <= e['e']]
    if ev_oggi: molt = max(molt, max([e['w'] for e in ev_oggi]))
    if dt.weekday() >= 4: molt *= 1.15
    return int(info['base'] * molt), ev_oggi

# --- 6. CSS VICTORY ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; background: white; border: 1px solid #a5d6a7; border-radius: 8px; }
    table.victory-table { border-collapse: separate; width: 100%; border-spacing: 0; }
    th, td { padding: 4px; text-align: center; border: 1px solid #eee; min-width: 100px; height: 80px; vertical-align: middle; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 170px; z-index: 10; font-size: 11px; text-align: left; padding-left: 8px; }
    .cell-booked { background: #ffcdd2 !important; color: #b71c1c !important; font-weight: bold; font-size: 11px; border-left: 6px solid #d32f2f !important; }
    .ev-1 { color: #f57f17; font-weight: bold; font-size: 10px; line-height: 1; }
    .ev-2 { color: #8e44ad; font-weight: bold; font-size: 10px; border-top: 1px dashed #ddd; }
    .info-price { font-size: 13px; color: #1b5e20; font-weight: 800; display: block; }
    .info-market { font-size: 9px; color: #c62828; font-weight: bold; }
    .section-box { background: white; padding: 12px; border-radius: 8px; border: 1px solid #a5d6a7; }
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 7. MAIN UI ---
def main():
    st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PESCHICI ULTIMATE</h3>", unsafe_allow_html=True)

    n1, n2, n3 = st.columns([1, 8, 1])
    if n1.button("◀ Mese"): st.session_state.mese -= 1; st.rerun()
    n2.markdown(f"<h4 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h4>", unsafe_allow_html=True)
    if n3.button("Mese ▶"): st.session_state.mese += 1; st.rerun()

    df_p = carica_prenotazioni()
    df_e = carica_eventi_manuali()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # TABELLA PLANNING
    html = '<div class="planning-container"><table class="victory-table"><thead><tr><th class="sticky-col">STRUTTURE</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#e8f5e9"
        html += f'<th style="background:{bg}; font-size:11px;">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    # RIGA RADAR (DOPPI EVENTI)
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100}, df_e)
        txt = "".join([f'<div class="ev-{i+1}">{ev["n"][:10]}</div>' for i, ev in enumerate(evs[:2])])
        html += f'<td style="background:#fff9c4;">{txt}</td>'
    html += '</tr>'

    for ns, info in STRUTTURE.items():
        # Blocco automatico Villa/Camere
        confl = []
        chk_units = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        if not df_p.empty:
            confl = df_p[df_p['Struttura'].isin(chk_units)]['Data'].tolist()

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            m = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)] if not df_p.empty else pd.DataFrame()

            if k in confl: 
                html += '<td style="background:#eeeeee; color:#bbb;">🔒</td>'
            elif not m.empty:
                nome_c = str(m.iloc[0]["Nome"])[:9].upper()
                html += f'<td class="cell-booked">{nome_c}</td>'
            else:
                prz, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info, df_e)
                mkt = st.session_state.market_prices.get(k, "---")
                html += f'<td><span class="info-price">€{prz}</span><span class="info-market">M: {mkt}</span></td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # AZIONI
    st.markdown("<br>", unsafe_allow_html=True)
    ca, cb, cc, cd = st.columns(4)
    
    with ca:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("🚩 EVENTO")
        with st.form("ev"):
            en = st.text_input("Nome"); c1, c2, c3 = st.columns(3); em = c1.number_input("M", 1, 12, st.session_state.mese); es = c2.number_input("In", 1, 31); ee = c3.number_input("Fi", 1, 31); ew = st.slider("Peso", 1.0, 3.0, 1.5)
            if st.form_submit_button("AGGIUNGI"):
                if invia_al_cloud([{"Nome": en, "Mese": em, "Inizio": es, "Fine": ee, "Peso": ew}]): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with cb:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("🚀 RADAR")
        r1, r2 = st.columns(2); d1 = r1.date_input("Inizio"); d2 = r2.date_input("Fine")
        if st.button("SCANSIONA GOOGLE", use_container_width=True):
            with st.spinner("Cercando..."):
                tmp = d1
                while tmp <= d2:
                    st.session_state.market_prices[tmp.strftime("%Y-%m-%d")] = int(get_market_average(tmp.strftime("%Y-%m-%d")))
                    tmp += timedelta(days=1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with cc:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        with st.form("bk"):
            st.subheader("📝 PRENOTA")
            su = st.selectbox("Unità", list(STRUTTURE.keys())); b1 = st.date_input("In"); b2 = st.date_input("Out")
            nm = st.text_input("Nome"); tl = st.text_input("Tel"); nt = st.text_input("Note")
            notti = (b2-b1).days if (b2-b1).days > 0 else 1
            prz_s, _ = calcola_prezzo_strategico(b1.day, b1.month, st.session_state.anno, STRUTTURE[su], df_e)
            pt = st.number_input("Totale", value=float(prz_s * notti)); ac = st.number_input("Acconto", value=0.0)
            if st.form_submit_button("CONFERMA"):
                nuove = [{"Data": (b1+timedelta(days=i)).strftime("%Y-%m-%d"), "Struttura": su, "Nome": nm, "Tel": tl, "Note": nt, "Prezzo_Totale": pt, "Acconto": ac, "Saldo": pt-ac} for i in range(notti)]
                if invia_al_cloud(nuove): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with cd:
        st.markdown('<div class="section-box" style="background-color:#fffde7;">', unsafe_allow_html=True)
        st.subheader("🗑️ ELIMINA")
        del_date = st.date_input("Giorno")
        del_struct = st.selectbox("Unità da liberare", list(STRUTTURE.keys()))
        if st.button("ELIMINA ORA", type="primary"):
            if invia_al_cloud({"action": "DELETE", "date": del_date.strftime("%Y-%m-%d"), "structure": del_struct}):
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 8. TEST DI COMUNICAZIONE (DEBUG) ---
    st.markdown("---")
    st.subheader("🔍 DEBUG: TEST DI COMUNICAZIONE")
    st.write("Questa tabella mostra esattamente quello che l'app legge dal tuo Foglio Google in questo momento:")
    if not df_p.empty:
        st.dataframe(df_p)
    else:
        st.error("ATTENZIONE: L'app non legge alcuna prenotazione dal Foglio Google. Controlla il nome della linguetta (Prenotazioni)!")

if __name__ == "__main__": main()z_s * notti)); ac = st.number_input("Acconto (€)", value=0.0)
            if st.form_submit_button("SALVA PRENOTAZIONE", use_container_width=True):
                nuove = [{"Data": (b1+timedelta(days=i)).strftime("%Y-%m-%d"), "Struttura": su, "Nome": nm, "Tel": tl, "Note": nt, "Prezzo_Totale": pt, "Acconto": ac, "Saldo": pt-ac} for i in range(notti)]
                if invia_al_cloud(nuove): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c_del:
        st.markdown('<div class="section-box" style="background-color:#fffde7;">', unsafe_allow_html=True)
        st.subheader("🗑️ ELIMINA")
        del_date = st.date_input("Giorno da liberare")
        del_struct = st.selectbox("Struttura da liberare", list(STRUTTURE.keys()))
        if st.button("ELIMINA ORA", type="primary", use_container_width=True):
            payload = {"action": "DELETE", "date": del_date.strftime("%Y-%m-%d"), "structure": del_struct}
            if invia_al_cloud(payload):
                st.success("Cancellato!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()