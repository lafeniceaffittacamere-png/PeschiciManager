import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Victory Radar Peschici (Direct)", layout="wide")

# Link DIRETTO al foglio (senza passare dai Secrets)
SHEET_ID = "1I34jTQs-qVlwqkoeUsXpHhzNBiZTLwvAVjmmjs_My-o"
# Questo URL scarica i dati direttamente in formato CSV
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2

# --- 2. COSTANTI ---
STRUTTURE = {
    "Il Melograno (VILLA)": {"base": 100}, "Il Melograno (SUITE)": {"base": 60},
    "Il Melograno (FAMILY)": {"base": 75}, "Hotel Peschici": {"base": 110},
    "Residenza Il Dragone": {"base": 150}, "B&B La Sorgente": {"base": 85},
    "Suite Vista Trabucco": {"base": 220}, "Camping Int. Peschici": {"base": 55},
    "Case Bianche Centro": {"base": 95}
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

# --- 3. FUNZIONI DATI (Metodo Diretto) ---
def carica_prenotazioni():
    try:
        # Legge direttamente dal link pubblico - ZERO ERRORI DI CONFIGURAZIONE
        df = pd.read_csv(CSV_URL)
        # Pulizia nomi colonne per sicurezza
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        # Se il foglio è vuoto o irraggiungibile
        return pd.DataFrame(columns=["Data", "Struttura", "Nome", "Tel", "Note", "Prezzo_Totale", "Acconto", "Saldo"])

def calcola_prezzo_strategico(giorno, mese, anno, info):
    dt = datetime(anno, mese, giorno)
    molt = 1.0
    if mese == 8: molt = 2.4
    elif mese == 7: molt = 1.7
    ev_oggi = [e for e in EVENTI_BASE if e['m'] == mese and e['s'] <= giorno <= e['e']]
    if ev_oggi: molt = max(molt, max([e['w'] for e in ev_oggi]))
    if dt.weekday() >= 4: molt *= 1.15
    return int(info['base'] * molt), ev_oggi

# --- 4. CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; background: white; border: 1px solid #a5d6a7; border-radius: 8px; }
    table { border-collapse: collapse; width: 100%; font-family: sans-serif; }
    th, td { border: 1px solid #eee; min-width: 90px; height: 60px; text-align: center; font-size: 11px; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 160px; z-index: 5; text-align: left; padding-left: 10px; }
    .booked { background: #ffcdd2 !important; color: #b71c1c; font-weight: bold; border: 1px solid #ef9a9a !important; }
    .locked { background: #f5f5f5 !important; color: #bdbdbd; font-style: italic; }
    .price-tag { color: #2e7d32; font-weight: 800; font-size: 13px; }
    .event-tag { color: #f57f17; font-size: 9px; font-weight: bold; display: block; }
    </style>
""", unsafe_allow_html=True)

# --- 5. INTERFACCIA ---
def main():
    st.markdown("<h1 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PESCHICI (Mod. Diretto)</h1>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀"): st.session_state.mese -= 1; st.rerun()
    c2.markdown(f"<h2 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h2>", unsafe_allow_html=True)
    if c3.button("▶"): st.session_state.mese += 1; st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # TABELLA
    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURA</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#fff"
        html += f'<th style="background:{bg}">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    for ns, info in STRUTTURE.items():
        target = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        blocked = []
        if not df_p.empty and 'Struttura' in df_p.columns and 'Data' in df_p.columns:
            blocked = df_p[df_p['Struttura'].astype(str).isin(target)]['Data'].astype(str).tolist()

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            # Controllo esistenza dati
            res = pd.DataFrame()
            if not df_p.empty and 'Data' in df_p.columns:
                res = df_p[(df_p['Data'].astype(str) == k) & (df_p['Struttura'] == ns)]

            if k in blocked:
                html += '<td class="locked">🔒</td>'
            elif not res.empty:
                nome = str(res.iloc[0]["Nome"])[:10].upper()
                html += f'<td class="booked">{nome}</td>'
            else:
                p, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                ev_txt = f'<span class="event-tag">{" ".join([e["n"][:6] for e in evs])}</span>' if evs else ""
                html += f'<td><span class="price-tag">€{p}</span>{ev_txt}</td>'
        html += '</tr>'
    
    st.markdown(html + '</tbody></table></div>', unsafe_allow_html=True)
    
    st.divider()
    st.info("ℹ️ In questa modalità 'Diretta', puoi vedere le prenotazioni che aggiungi manualmente nel file Google Sheets. Per riattivare il salvataggio automatico da qui, dobbiamo sistemare i Secrets con calma.")

if __name__ == "__main__":
    main()