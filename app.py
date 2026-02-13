import streamlit as st
from streamlit_gsheets import GSheetsConnection
import calendar
import pandas as pd
import requests
import json
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici ULTIMATE", layout="wide")

# --- 2. LINK CLOUD (VERSIONE 2) ---
URL_SCRIPT_GOOGLE = "https://script.google.com/macros/s/AKfycbyTvoDo6v9PwwdcyK3V6PKlkLS8gMi7PqEE79dfdRMoiRhMj7MWmIMbCT6OTfN62Uyc/exec"

# --- 3. INIZIALIZZAZIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2
if 'market_prices' not in st.session_state: st.session_state.market_prices = {}

# CONNESSIONE
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

# --- 4. FUNZIONI DATI (PIÙ TOLLERANTE) ---
def carica_prenotazioni():
    try: 
        df = conn.read(worksheet="Prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df.columns = [c.strip() for c in df.columns]
            # Proviamo a convertire le date in modo più flessibile
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
            df['Struttura'] = df['Struttura'].astype(str).str.strip()
            # Non cancelliamo le righe se c'è un errore, così le vediamo nel debug
        return df
    except Exception as e:
        st.error(f"Errore di connessione: {e}")
        return pd.DataFrame()

def invia_al_cloud(payload):
    try: 
        r = requests.post(URL_SCRIPT_GOOGLE, data=json.dumps(payload))
        return r.status_code == 200
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

# --- 5. CSS (MASSIMA VISIBILITÀ) ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; background: white; border: 2px solid #2e7d32; border-radius: 10px; }
    table { border-collapse: separate; width: 100%; border-spacing: 0; }
    th, td { padding: 8px; text-align: center; border: 1px solid #ddd; min-width: 110px; height: 90px; vertical-align: middle; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 180px; z-index: 10; font-size: 12px; text-align: left; }
    .cell-booked { background: #d32f2f !important; color: white !important; font-weight: 900; font-size: 13px; border: 2px solid #b71c1c !important; }
    .info-price { font-size: 15px; color: #1b5e20; font-weight: 800; display: block; }
    .info-market { font-size: 10px; color: #c62828; font-weight: bold; }
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 6. MAIN UI ---
def main():
    st.markdown(f"<h2 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PRO ONLINE</h2>", unsafe_allow_html=True)

    n1, n2, n3 = st.columns([1, 8, 1])
    if n1.button("◀ MESE PRECEDENTE"): st.session_state.mese -= 1; st.rerun()
    n2.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()}</h3>", unsafe_allow_html=True)
    if n3.button("MESE SUCCESSIVO ▶"): st.session_state.mese += 1; st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # TABELLA CALENDARIO
    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURE</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#e8f5e9"
        html += f'<th style="background:{bg};">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    # RIGA RADAR
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100})
        txt = "".join([f'<div style="font-size:10px; font-weight:bold;">{ev["n"][:10]}</div>' for ev in evs[:2]])
        html += f'<td style="background:#fff9c4;">{txt}</td>'
    html += '</tr>'

    for ns, info in STRUTTURE.items():
        confl = []
        if not df_p.empty:
            chk = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
            confl = df_p[df_p['Struttura'].isin(chk)]['Data'].tolist()

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            
            # Controllo se prenotato
            res = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)] if not df_p.empty else pd.DataFrame()

            if k in confl: html += '<td style="background:#eee; color:#bbb;">🔒</td>'
            elif not res.empty:
                nome_ospite = str(res.iloc[0]["Nome"]).upper()[:12]
                html += f'<td class="cell-booked">{nome_ospite}</td>'
            else:
                prz, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                html += f'<td><span class="info-price">€{prz}</span></td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # AZIONI
    st.markdown("<br>", unsafe_allow_html=True)
    c_book, c_del = st.columns(2)

    with c_book:
        with st.form("bk"):
            st.subheader("📝 NUOVA PRENOTAZIONE")
            su = st.selectbox("Unità", list(STRUTTURE.keys())); b1 = st.date_input("Check-in"); b2 = st.date_input("Check-out")
            nm = st.text_input("Nome Cliente"); tl = st.text_input("Telefono"); nt = st.text_input("Note")
            if st.form_submit_button("SALVA SUL CLOUD", use_container_width=True):
                notti = (b2-b1).days if (b2-b1).days > 0 else 1
                prz, _ = calcola_prezzo_strategico(b1.day, b1.month, st.session_state.anno, STRUTTURE[su])
                nuove = [{"Data": (b1+timedelta(days=i)).strftime("%Y-%m-%d"), "Struttura": su, "Nome": nm, "Tel": tl, "Note": nt, "Prezzo_Totale": prz*notti, "Acconto": 0, "Saldo": prz*notti} for i in range(notti)]
                if invia_al_cloud(nuove): st.rerun()

    with c_del:
        st.subheader("🗑️ CANCELLA")
        del_date = st.date_input("Data da liberare")
        del_struct = st.selectbox("Struttura da liberare", list(STRUTTURE.keys()))
        if st.button("ELIMINA PRENOTAZIONE", type="primary", use_container_width=True):
            if invia_al_cloud({"action": "DELETE", "date": del_date.strftime("%Y-%m-%d"), "structure": del_struct}):
                st.rerun()

    # --- DEBUG FINALE ---
    st.markdown("---")
    st.subheader("🔍 COSA VEDE L'APP NEL TUO FOGLIO GOOGLE")
    if not df_p.empty:
        st.write("Dati caricati:")
        st.dataframe(df_p)
    else:
        st.warning("La tabella è VUOTA. Controlla che il foglio si chiami 'Prenotazioni' e che il link nei Secrets sia corretto!")

if __name__ == "__main__": main()