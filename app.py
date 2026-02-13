import streamlit as st
from streamlit_gsheets import GSheetsConnection
import calendar
import pandas as pd
import requests
import json
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici ULTIMATE", layout="wide")

# --- 2. LINK CLOUD PIANO B ---
URL_SCRIPT_GOOGLE = "https://script.google.com/macros/s/AKfycbx7X-0P63XjFNEJ9lA_CHVLN-u0at_kxpEd-O5YSBi98sNvr9wsBmR7GNZqA0GSDgRa/exec"

# --- 3. INIZIALIZZAZIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = datetime.now().month
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
            # Forza la pulizia delle date: se Google mette orari o formati strani, li pialliamo
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['Struttura'] = df['Struttura'].astype(str).str.strip()
            df = df.dropna(subset=['Data', 'Struttura'])
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Data", "Struttura", "Nome", "Tel", "Note", "Prezzo_Totale", "Acconto", "Saldo"])

def carica_eventi_manuali():
    try: 
        df = conn.read(worksheet="Eventi", ttl=0)
        return df if df is not None else pd.DataFrame()
    except: return pd.DataFrame()

def salva_via_script(dati):
    try: return requests.post(URL_SCRIPT_GOOGLE, data=json.dumps(dati)).status_code == 200
    except: return False

# --- 5. LOGICA PREZZI ---
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
    .planning-container { overflow-x: auto; background: white; border-radius: 6px; border: 1px solid #a5d6a7; }
    table.victory-table { border-collapse: separate; width: 100%; border-spacing: 0; }
    th, td { padding: 4px; text-align: center; border: 1px solid #eee; min-width: 95px; height: 65px; vertical-align: middle; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 150px; z-index: 10; font-size: 11px; text-align: left; padding-left: 5px;}
    .cell-booked { background: #ffcdd2 !important; color: #b71c1c !important; font-weight: bold; font-size: 10px; border-left: 4px solid #d32f2f !important; }
    .ev-1 { color: #f57f17; font-weight: bold; font-size: 9px; }
    .info-price { font-size: 13px; color: #1b5e20; font-weight: 800; display: block; }
    .info-market { font-size: 9px; color: #c62828; font-weight: bold; }
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 7. MAIN UI ---
def main():
    st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PESCHICI PRO</h3>", unsafe_allow_html=True)

    n1, n2, n3 = st.columns([1, 8, 1])
    if n1.button("◀"): st.session_state.mese -= 1; st.rerun()
    n2.markdown(f"<h4 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h4>", unsafe_allow_html=True)
    if n3.button("▶"): st.session_state.mese += 1; st.rerun()

    df_p = carica_prenotazioni()
    df_e = carica_eventi_manuali()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # TABELLA
    html = '<div class="planning-container"><table class="victory-table"><thead><tr><th class="sticky-col">STRUTTURE</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#e8f5e9"
        html += f'<th style="background:{bg}; font-size:11px;">{d}</th>'
    html += '</tr></thead><tbody>'

    # RIGA RADAR
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100}, df_e)
        txt = "".join([f'<div class="ev-1">{ev["n"][:10]}</div>' for ev in evs[:1]])
        html += f'<td style="background:#fff9c4;">{txt}</td>'
    html += '</tr>'

    for ns, info in STRUTTURE.items():
        confl = []
        chk = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        if not df_p.empty:
            confl = df_p[df_p['Struttura'].isin(chk)]['Data'].tolist()

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            
            # Controllo Prenotazione
            is_booked = False
            nome_ospite = ""
            if not df_p.empty:
                m = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)]
                if not m.empty:
                    is_booked = True
                    nome_ospite = str(m.iloc[0]["Nome"])[:8]

            if k in confl: html += '<td style="background:#eee; color:#bbb;">🔒</td>'
            elif is_booked: html += f'<td class="cell-booked">{nome_ospite}</td>'
            else:
                prz, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info, df_e)
                mkt = st.session_state.market_prices.get(k, "---")
                html += f'<td><span class="info-price">€{prz}</span><span class="info-market">M: {mkt}</span></td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # AZIONI
    st.markdown("<br>", unsafe_allow_html=True)
    c_form, c_debug = st.columns([2, 1])
    
    with c_form:
        with st.form("bk"):
            st.subheader("📝 PRENOTA")
            su = st.selectbox("Unità", MELOGRANO_UNITS); b1 = st.date_input("In"); b2 = st.date_input("Out")
            nm = st.text_input("Nome"); tl = st.text_input("Tel"); nt = st.text_input("Note")
            notti = (b2-b1).days if (b2-b1).days > 0 else 1
            prz_s, _ = calcola_prezzo_strategico(b1.day, b1.month, st.session_state.anno, STRUTTURE[su], df_e)
            pt = st.number_input("Totale (€)", value=float(prz_s * notti)); ac = st.number_input("Acconto (€)", value=0.0)
            if st.form_submit_button("SALVA"):
                nuove = [{"Data": (b1+timedelta(days=i)).strftime("%Y-%m-%d"), "Struttura": su, "Nome": nm, "Tel": tl, "Note": nt, "Prezzo_Totale": pt, "Acconto": ac, "Saldo": pt-ac} for i in range(notti)]
                if salva_via_script(nuove): st.rerun()

    with c_debug:
        st.subheader("🔍 DEBUG")
        st.write("Dati letti dal foglio:")
        st.dataframe(df_p[['Data', 'Struttura', 'Nome']].head(10))

if __name__ == "__main__": main()