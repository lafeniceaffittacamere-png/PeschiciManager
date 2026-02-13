import streamlit as st
import pandas as pd
import requests
import json
import calendar
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Victory Radar Peschici 2026", layout="wide")

# --- 2. COSTANTI PESCHICI ---
# URL SCRIPT (Per SCRIVERE/ELIMINARE - Il tuo link funzionante)
URL_SCRIPT_GOOGLE = "https://script.google.com/macros/s/AKfycby0mE0ltg7MMQlwUb-jPmLuuUD-raHRLLV1vW7wJjk8VpJZIftWZ-M8Beuvwkrf5cROKA/exec"

# URL LETTURA (Anti-Cache)
SHEET_ID = "1I34jTQs-qVlwqkoeUsXpHhzNBiZTLwvAVjmmjs_My-o"
URL_LETTURA_DIRETTA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Prenotazioni"

# STRUTTURE E PREZZI BASE
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

# RELAZIONI PARENT/CHILD (Per i blocchi automatici)
PARENT_UNIT = "Il Melograno (VILLA)"
CHILD_UNITS = ["Il Melograno (SUITE)", "Il Melograno (FAMILY)"]

# CALENDARIO EVENTI PESCHICI
EVENTI_BASE = [
    {"m": 6, "s": 20, "e": 21, "n": "TRIATHLON", "w": 1.5},
    {"m": 7, "s": 4,  "e": 5,  "n": "ZAIANA OPEN", "w": 1.6},
    {"m": 7, "s": 19, "e": 21, "n": "SANT'ELIA", "w": 2.2},
    {"m": 8, "s": 14, "e": 16, "n": "FERRAGOSTO B.", "w": 2.8},
    {"m": 8, "s": 8,  "e": 22, "n": "GOLD WEEK", "w": 2.5},
    {"m": 8, "s": 26, "e": 28, "n": "PESCHICI JAZZ", "w": 1.4},
]

# --- 3. LOGICA ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2

def carica_prenotazioni():
    try:
        # Trucco del timestamp per forzare il download fresco
        timestamp = int(time.time())
        df = pd.read_csv(f"{URL_LETTURA_DIRETTA}&v={timestamp}")
        
        if df is not None and not df.empty:
            df.columns = [c.strip() for c in df.columns]
            df.rename(columns=lambda x: x.capitalize(), inplace=True) 
            if 'Data' in df.columns and 'Struttura' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
                df['Struttura'] = df['Struttura'].astype(str).str.strip()
                return df.dropna(subset=['Data', 'Struttura'])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def invia_al_cloud(payload):
    try: 
        requests.post(URL_SCRIPT_GOOGLE, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        return True
    except: return False

def calcola_prezzo_strategico(giorno, mese, anno, info):
    dt = datetime(anno, mese, giorno)
    molt = 1.0
    # Stagionalità
    if mese == 8: molt = 2.4
    elif mese == 7: molt = 1.7
    elif mese in [6, 9]: molt = 1.2
    # Eventi
    ev_oggi = [e for e in EVENTI_BASE if e['m'] == mese and e['s'] <= giorno <= e['e']]
    if ev_oggi: molt = max(molt, max([e['w'] for e in ev_oggi]))
    # Weekend
    if dt.weekday() >= 4: molt *= 1.15
    return int(info['base'] * molt), ev_oggi

# --- 4. GRAFICA CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; background: white; border: 1px solid #a5d6a7; border-radius: 8px; }
    table { border-collapse: separate; width: 100%; border-spacing: 0; }
    th, td { padding: 4px; text-align: center; border: 1px solid #eee; min-width: 95px; height: 65px; vertical-align: middle; font-size: 11px; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 160px; z-index: 10; text-align: left; padding-left: 8px; }
    .cell-booked { background: #ffcdd2 !important; color: #b71c1c !important; font-weight: bold; border-left: 5px solid #d32f2f !important; }
    .cell-locked { background: #eeeeee !important; color: #bdbdbd; font-style: italic; }
    .ev-tag { color: #f57f17; font-weight: bold; font-size: 10px; display: block; text-transform: uppercase; }
    .price-tag { font-size: 14px; color: #1b5e20; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 5. INTERFACCIA ---
def main():
    st.markdown(f"<h1 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PESCHICI 2026</h1>", unsafe_allow_html=True)
    
    # Pulsante emergenza aggiornamento
    if st.button("🔄 AGGIORNA ORA"):
        st.cache_data.clear()
        st.rerun()

    # Navigazione
    n1, n2, n3 = st.columns([1, 8, 1])
    if n1.button("◀ MESE PRECEDENTE"): 
        st.session_state.mese -= 1
        if st.session_state.mese < 1: st.session_state.mese = 12; st.session_state.anno -= 1
        st.rerun()
    n2.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h3>", unsafe_allow_html=True)
    if n3.button("MESE SUCCESSIVO ▶"): 
        st.session_state.mese += 1
        if st.session_state.mese > 12: st.session_state.mese = 1; st.session_state.anno += 1
        st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # TABELLA RADAR
    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURA</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#e8f5e9"
        html += f'<th style="background:{bg}">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    # RIGA EVENTI
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100})
        txt = "".join([f'<span class="ev-tag">{ev["n"][:10]}</span>' for ev in evs])
        html += f'<td style="background:#fff9c4;">{txt}</td>'
    html += '</tr>'

    # RIGHE STRUTTURE
    for ns, info in STRUTTURE.items():
        # Calcolo blocchi
        conflitti = []
        chk_units = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        if not df_p.empty and 'Struttura' in df_p.columns:
            conflitti = df_p[df_p['Struttura'].isin(chk_units)]['Data'].tolist()

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            m = pd.DataFrame()
            if not df_p.empty and 'Data' in df_p.columns:
                m = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)]

            if k in conflitti: 
                html += '<td class="cell-locked">🔒</td>'
            elif not m.empty:
                nome_c = str(m.iloc[0]["Nome"]).upper()[:9]
                html += f'<td class="cell-booked">{nome_c}</td>'
            else:
                prz, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                # Se c'è un evento, metti un puntino colorato
                dot = "🔴" if evs else ""
                html += f'<td><span class="price-tag">€{prz}</span><br>{dot}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # AZIONI
    st.divider()
    c_book, c_del = st.columns(2)
    
    with c_book:
        with st.form("bk"):
            st.subheader("📝 PRENOTA")
            su = st.selectbox("Unità", list(STRUTTURE.keys())); b1 = st.date_input("In"); b2 = st.date_input("Out")
            nm = st.text_input("Nome"); tl = st.text_input("Tel"); nt = st.text_input("Note")
            
            notti = (b2-b1).days if (b2-b1).days > 0 else 1
            prz_s, _ = calcola_prezzo_strategico(b1.day, b1.month, st.session_state.anno, STRUTTURE[su])
            pt = st.number_input("Totale (€)", value=float(prz_s * notti)); ac = st.number_input("Acconto (€)", value=0.0)
            
            if st.form_submit_button("SALVA PRENOTAZIONE"):
                nuove = []
                for i in range(notti):
                    g = (b1 + timedelta(days=i)).strftime("%Y-%m-%d")
                    nuove.append({"Data": g, "Struttura": su, "Nome": nm, "Tel": tl, "Note": nt, "Prezzo_Totale": pt, "Acconto": ac, "Saldo": pt-ac})
                
                if invia_al_cloud(nuove): 
                    with st.spinner("Sincronizzazione Cloud in corso... (3s)"):
                        time.sleep(3)
                        st.cache_data.clear()
                    st.success("✅ Salvato!")
                    st.rerun()

    with c_del:
        st.subheader("🗑️ ELIMINA")
        d_d = st.date_input("Giorno"); d_s = st.selectbox("Unità", list(STRUTTURE.keys()), key="del_s")
        if st.button("ELIMINA DEFINITIVAMENTE", type="primary"):
            if invia_al_cloud({"action": "DELETE", "date": d_d.strftime("%Y-%m-%d"), "structure": d_s}):
                with st.spinner("Rimozione dal Cloud... (3s)"):
                    time.sleep(3)
                    st.cache_data.clear()
                st.success("✅ Cancellato!")
                st.rerun()

if __name__ == "__main__": main()
