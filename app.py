import streamlit as st
from streamlit_gsheets import GSheetsConnection
import calendar
import pandas as pd
import requests
import json
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici ULTIMATE", layout="wide")

# --- 2. IL TUO LINK "PIANO B" (Senza Carta di Credito) ---
URL_SCRIPT_GOOGLE = "https://script.google.com/macros/s/AKfycbx7X-0P63XjFNEJ9lA_CHVLN-u0at_kxpEd-O5YSBi98sNvr9wsBmR7GNZqA0GSDgRa/exec"

# --- 3. INIZIALIZZAZIONE STATO ---
if 'anno' not in st.session_state:
    st.session_state.anno = 2026
if 'mese' not in st.session_state:
    st.session_state.mese = datetime.now().month
if 'market_prices' not in st.session_state:
    st.session_state.market_prices = {}

# --- 4. CONNESSIONE & COSTANTI ---
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

# --- 5. FUNZIONI DATI (Lettura da GSheets, Scrittura via Script) ---
def carica_prenotazioni():
    try: return conn.read(worksheet="Prenotazioni", ttl="1m")
    except: return pd.DataFrame(columns=["Data", "Struttura", "Nome", "Tel", "Note", "Prezzo_Totale", "Acconto", "Saldo"])

def carica_eventi_manuali():
    try: return conn.read(worksheet="Eventi", ttl="1m")
    except: return pd.DataFrame(columns=["Nome", "Mese", "Inizio", "Fine", "Peso"])

def salva_prenotazione_via_script(lista_nuove_date):
    try:
        r = requests.post(URL_SCRIPT_GOOGLE, data=json.dumps(lista_nuove_date))
        return r.status_code == 200
    except: return False

# --- 6. LOGICA PREZZI ---
def get_market_average(date_str):
    check_out = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    params = {"engine": "google_hotels", "q": "hotel peschici foggia", "check_in_date": date_str, "check_out_date": check_out, "currency": "EUR", "api_key": API_KEY}
    try:
        res = requests.get("https://serpapi.com/search", params=params, timeout=10).json()
        prezzi = [int(''.join(filter(str.isdigit, p.get("rate_per_night", {}).get("lowest")))) for p in res.get("properties", []) if p.get("rate_per_night", {}).get("lowest")]
        return sum(prezzi) / len(prezzi) if prezzi else 95.0
    except: return 95.0

def calcola_prezzo_strategico(giorno, mese, anno, info, manuali_df):
    dt = datetime(anno, mese, giorno)
    molt = 1.0
    if mese == 8: molt = 2.4
    elif mese == 7: molt = 1.7
    elif mese in [6, 9]: molt = 1.2
    tutti = EVENTI_BASE.copy()
    for _, r in manuali_df.iterrows():
        tutti.append({"m": int(r['Mese']), "s": int(r['Inizio']), "e": int(r['Fine']), "n": r['Nome'], "w": float(r['Peso'])})
    ev_oggi = [e for e in tutti if e['m'] == mese and e['s'] <= giorno <= e['e']]
    if ev_oggi: molt = max(molt, max([e['w'] for e in ev_oggi]))
    if dt.weekday() >= 4: molt *= 1.15
    return int(info['base'] * molt), ev_oggi

# --- 7. CSS VICTORY GREEN ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; padding-bottom: 20px; background: white; border-radius: 6px; }
    table.victory-table { border-collapse: separate; border-spacing: 0; width: 100%; font-family: 'Segoe UI', sans-serif; }
    th, td { padding: 4px; text-align: center; border-right: 1px solid #eee; border-bottom: 1px solid #eee; min-width: 95px; height: 65px; vertical-align: middle; }
    th.date-header { position: sticky; top: 0; background-color: #e8f5e9; color: #1b5e20; z-index: 10; border-bottom: 2px solid #81c784; font-size: 11px; }
    .sticky-col { position: sticky; left: 0; background-color: #2e7d32; z-index: 11; color: white; text-align: left; padding-left: 8px; min-width: 150px; font-weight: bold; font-size: 11px; }
    .ev-1 { color: #f57f17; font-weight: bold; font-size: 9px; }
    .ev-2 { color: #8e44ad; font-weight: bold; font-size: 9px; border-top: 1px dashed #ddd; }
    .cell-event { background-color: #fff9c4; border-bottom: 2px solid #fbc02d; line-height: 1.1; }
    .cell-booked { background-color: #ffcdd2 !important; color: #b71c1c !important; border-left: 3px solid #d32f2f; font-weight: bold; text-align: left; padding-left: 4px; font-size: 9px; }
    .info-price { font-size: 13px; color: #1b5e20; font-weight: 800; display: block; }
    .info-market { font-size: 9px; color: #c62828; display: block; font-weight: bold; margin-top: 2px; }
    .section-box { background: white; padding: 12px; border-radius: 8px; border: 1px solid #a5d6a7; }
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 8. MAIN UI ---
def main():
    st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PRO ONLINE</h3>", unsafe_allow_html=True)

    # Navigazione
    nav1, nav2, nav3 = st.columns([1, 8, 1])
    if nav1.button("◀"): st.session_state.mese -= 1; st.rerun()
    nav2.markdown(f"<h4 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()}</h4>", unsafe_allow_html=True)
    if nav3.button("▶"): st.session_state.mese += 1; st.rerun()

    df_p = carica_prenotazioni()
    df_e = carica_eventi_manuali()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # Planning
    html = '<div class="planning-container"><table class="victory-table"><thead><tr><th class="sticky-col">STRUTTURE</th>'
    for d in range(1, num_days + 1): html += f'<th class="date-header">{d}</th>'
    html += '</tr></thead><tbody>'

    # Riga Radar
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100}, df_e)
        txt = ""
        for i, ev in enumerate(evs[:2]): txt += f'<div class="ev-{i+1}">{ev["n"][:10]}</div>'
        html += f'<td class="cell-event">{txt}</td>'
    html += '</tr>'

    for nome_s, info in STRUTTURE.items():
        confl = []
        chk = CHILD_UNITS if nome_s == PARENT_UNIT else ([PARENT_UNIT] if nome_s in CHILD_UNITS else [])
        for c in chk: confl.extend(df_p[df_p['Struttura'] == c]['Data'].tolist())

        html += f'<tr><td class="sticky-col">{nome_s}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            m = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == nome_s)]
            
            if k in confl: html += '<td style="background:#eee;">🔒</td>'
            elif not m.empty:
                html += f'<td class="cell-booked">{m.iloc[0]["Nome"][:8]}</td>'
            else:
                prz, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info, df_e)
                mkt = st.session_state.market_prices.get(k, "---")
                html += f'<td><span class="info-price">€{prz}</span><span class="info-market">M: {mkt}</span></td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # 3 Colonne Azioni
    st.markdown("<br>", unsafe_allow_html=True)
    ca, cb, cc = st.columns(3)

    with ca:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("🚩 EVENTI")
        with st.form("ev"):
            en = st.text_input("Nome Evento")
            c1, c2, c3 = st.columns(3); em = c1.number_input("M", 1, 12, st.session_state.mese); es = c2.number_input("In", 1, 31, 1); ee = c3.number_input("Fi", 1, 31, 1)
            ew = st.slider("Peso", 1.0, 3.0, 1.5, 0.1)
            if st.form_submit_button("AGGIUNGI"):
                st.info("Aggiunta eventi via script non configurata, ma i manuali letti appaiono!")
        st.markdown('</div>', unsafe_allow_html=True)

    with cb:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("📡 RADAR GOOGLE")
        r1, r2 = st.columns(2); d1 = r1.date_input("Dal"); d2 = r2.date_input("Al")
        if st.button("🚀 SCANSIONA", use_container_width=True):
            with st.spinner("Analisi..."):
                curr = d1
                while curr <= d2:
                    ds = curr.strftime("%Y-%m-%d")
                    st.session_state.market_prices[ds] = int(get_market_average(ds))
                    curr += timedelta(days=1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with cc:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("📝 PRENOTAZIONE")
        with st.form("bk"):
            su = st.selectbox("Unità", MELOGRANO_UNITS)
            bc1, bc2 = st.columns(2); b1 = bc1.date_input("In"); b2 = bc2.date_input("Out")
            nm = st.text_input("Nome Cliente"); tl = st.text_input("Telefono"); note = st.text_input("Note")
            
            notti = (b2-b1).days if (b2-b1).days > 0 else 1
            prz_sug = sum([calcola_prezzo_strategico((b1+timedelta(days=x)).day, (b1+timedelta(days=x)).month, st.session_state.anno, STRUTTURE[su], df_e)[0] for x in range(notti)])
            p_tot = st.number_input("Prezzo Totale (€)", value=float(prz_sug))
            acc = st.number_input("Acconto (€)", value=0.0)
            
            st.write(f"**Saldo: {p_tot - acc} €**")
            
            if st.form_submit_button("CONFERMA E SALVA"):
                nuove = []
                for i in range(notti):
                    nuove.append({
                        "Data": (b1 + timedelta(days=i)).strftime("%Y-%m-%d"),
                        "Struttura": su, "Nome": nm, "Tel": tl, "Note": note,
                        "Prezzo_Totale": p_tot, "Acconto": acc, "Saldo": p_tot - acc
                    })
                if salva_prenotazione_via_script(nuove):
                    st.success("Salvato!")
                    st.rerun()
                else: st.error("Errore script!")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()