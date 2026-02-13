import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import calendar
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Victory Radar Peschici PRO", layout="wide")

# Connessione Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2

# --- COSTANTI ---
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

# --- LOGICA DATI ---
def carica_prenotazioni():
    try:
        # Carica i dati dal foglio "prenotazioni"
        return conn.read(worksheet="prenotazioni", ttl=0)
    except:
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

# --- CSS PERSONALIZZATO ---
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

# --- UI PRINCIPALE ---
def main():
    st.markdown("<h1 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PESCHICI 2026</h1>", unsafe_allow_html=True)

    # Navigazione Mesi
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ Precedente"):
        st.session_state.mese -= 1
        if st.session_state.mese < 1: st.session_state.mese = 12; st.session_state.anno -= 1
        st.rerun()
    c2.markdown(f"<h2 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h2>", unsafe_allow_html=True)
    if c3.button("Successivo ▶"):
        st.session_state.mese += 1
        if st.session_state.mese > 12: st.session_state.mese = 1; st.session_state.anno += 1
        st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # COSTRUZIONE TABELLA
    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURA</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#fff"
        html += f'<th style="background:{bg}">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    for ns, info in STRUTTURE.items():
        # Logica Villa/Suite
        target = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        blocked = []
        if not df_p.empty:
            blocked = df_p[df_p['Struttura'].astype(str).isin(target)]['Data'].astype(str).tolist()

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            res = df_p[(df_p['Data'].astype(str) == k) & (df_p['Struttura'] == ns)] if not df_p.empty else pd.DataFrame()

            if k in blocked:
                html += '<td class="locked">🔒 BLOCC.</td>'
            elif not res.empty:
                nome = str(res.iloc[0]["Nome"])[:10].upper()
                html += f'<td class="booked">{nome}</td>'
            else:
                p, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                ev_txt = f'<span class="event-tag">{" ".join([e["n"][:6] for e in evs])}</span>' if evs else ""
                html += f'<td><span class="price-tag">€{p}</span>{ev_txt}</td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # AZIONI
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        with st.form("bk"):
            st.subheader("📝 Nuova Prenotazione")
            f_s = st.selectbox("Unità", list(STRUTTURE.keys()))
            f_in = st.date_input("Inizio"); f_out = st.date_input("Fine")
            f_n = st.text_input("Nome Ospite")
            if st.form_submit_button("REGISTRA"):
                notti = (f_out - f_in).days if (f_out - f_in).days > 0 else 1
                p_u, _ = calcola_prezzo_strategico(f_in.day, f_in.month, f_in.year, STRUTTURE[f_s])
                
                # Creiamo le righe
                nuove_righe = []
                for i in range(notti):
                    g = (f_in + timedelta(days=i)).strftime("%Y-%m-%d")
                    nuove_righe.append([g, f_s, f_n, "", "", p_u*notti, 0, p_u*notti])
                
                df_nuovo = pd.DataFrame(nuove_righe, columns=df_p.columns)
                df_finale = pd.concat([df_p, df_nuovo], ignore_index=True)
                conn.update(worksheet="prenotazioni", data=df_finale)
                st.success("Sincronizzato!")
                st.rerun()

    with col_b:
        st.subheader("🗑️ Elimina")
        d_d = st.date_input("Giorno"); d_s = st.selectbox("Unità", list(STRUTTURE.keys()), key="del")
        if st.button("ELIMINA RIGA", type="primary"):
            df_p = df_p[~((df_p['Data'].astype(str) == d_d.strftime("%Y-%m-%d")) & (df_p['Struttura'] == d_s))]
            conn.update(worksheet="prenotazioni", data=df_p)
            st.rerun()

if __name__ == "__main__":
    main()