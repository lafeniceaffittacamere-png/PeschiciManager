import streamlit as st
import pandas as pd
import calendar
import requests
import json
from datetime import datetime, timedelta
from sqlalchemy import text

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici DB-PRO", layout="wide")

# --- 2. CONNESSIONE DATABASE (MySQL/Percona) ---
conn = st.connection('mysql', type='sql')

# --- 3. INIZIALIZZAZIONE SESSIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2
if 'market_prices' not in st.session_state: st.session_state.market_prices = {}

# --- 4. COSTANTI E CONFIGURAZIONI ---
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

# --- 5. FUNZIONI DATI (VERSIONE DATABASE) ---

def carica_prenotazioni():
    try:
        # ttl=0 forza la lettura immediata dal database senza cache
        df = conn.query("SELECT * FROM prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m-%d')
            df['Struttura'] = df['Struttura'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Errore caricamento Database: {e}")
        return pd.DataFrame(columns=["Data", "Struttura", "Nome", "Tel", "Note", "Prezzo_Totale", "Acconto", "Saldo"])

def salva_prenotazione(lista_p):
    try:
        with conn.session as s:
            for p in lista_p:
                query = text("""
                    INSERT INTO prenotazioni (Data, Struttura, Nome, Tel, Note, Prezzo_Totale, Acconto, Saldo) 
                    VALUES (:Data, :Struttura, :Nome, :Tel, :Note, :Prezzo_Totale, :Acconto, :Saldo)
                """)
                s.execute(query, p)
            s.commit()
        return True
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")
        return False

def elimina_prenotazione(data, struttura):
    try:
        with conn.session as s:
            query = text("DELETE FROM prenotazioni WHERE Data = :data AND Struttura = :struttura")
            s.execute(query, {"data": data, "struttura": struttura})
            s.commit()
        return True
    except Exception as e:
        st.error(f"Errore eliminazione: {e}")
        return False

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

# --- 6. CSS PERSONALIZZATO ---
st.markdown("""
    <style>
    .stApp { background-color: #f1f8e9; }
    .planning-container { overflow-x: auto; background: white; border: 1px solid #a5d6a7; border-radius: 8px; }
    table { border-collapse: separate; width: 100%; border-spacing: 0; }
    th, td { padding: 4px; text-align: center; border: 1px solid #eee; min-width: 100px; height: 80px; vertical-align: middle; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 170px; z-index: 10; font-size: 11px; text-align: left; padding-left: 8px; }
    .cell-booked { background: #ffcdd2 !important; color: #b71c1c !important; font-weight: bold; font-size: 11px; border-left: 6px solid #d32f2f !important; }
    .ev-1 { color: #f57f17; font-weight: bold; font-size: 10px; }
    .info-price { font-size: 13px; color: #1b5e20; font-weight: 800; display: block; }
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 7. UI PRINCIPALE ---
def main():
    st.markdown(f"<h3 style='text-align:center; color:#2e7d32;'>VICTORY RADAR - MYSQL DATABASE</h3>", unsafe_allow_html=True)

    # Navigazione Mesi
    n1, n2, n3 = st.columns([1, 8, 1])
    if n1.button("◀"): 
        st.session_state.mese -= 1
        if st.session_state.mese < 1: st.session_state.mese = 12; st.session_state.anno -= 1
        st.rerun()
    n2.markdown(f"<h4 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h4>", unsafe_allow_html=True)
    if n3.button("▶"): 
        st.session_state.mese += 1
        if st.session_state.mese > 12: st.session_state.mese = 1; st.session_state.anno += 1
        st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # COSTRUZIONE TABELLA HTML
    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURE</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#e8f5e9"
        html += f'<th style="background:{bg}; font-size:11px;">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    # RIGA RADAR EVENTI
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100})
        txt = "".join([f'<div class="ev-1">{ev["n"][:10]}</div>' for ev in evs])
        html += f'<td style="background:#fff9c4;">{txt}</td>'
    html += '</tr>'

    # RIGHE STRUTTURE
    for ns, info in STRUTTURE.items():
        # Verifica conflitti per blocco Villa/Suite
        confl_dates = []
        target_units = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        if not df_p.empty:
            confl_dates = df_p[df_p['Struttura'].isin(target_units)]['Data'].tolist()

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            m = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)] if not df_p.empty else pd.DataFrame()

            if k in confl_dates: 
                html += '<td style="background:#f5f5f5; color:#ccc;">🔒</td>'
            elif not m.empty:
                nome_c = str(m.iloc[0]["Nome"]).upper()[:9]
                html += f'<td class="cell-booked">{nome_c}</td>'
            else:
                prz, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                html += f'<td><span class="info-price">€{prz}</span></td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

    # AREA AZIONI
    st.markdown("<br>", unsafe_allow_html=True)
    c_book, c_del = st.columns(2)
    
    with c_book:
        with st.form("bk"):
            st.subheader("📝 NUOVA PRENOTAZIONE")
            su = st.selectbox("Unità", list(STRUTTURE.keys()))
            b1 = st.date_input("Check-in")
            b2 = st.date_input("Check-out")
            nm = st.text_input("Nome Cliente")
            tl = st.text_input("Telefono")
            nt = st.text_area("Note")
            
            notti = (b2-b1).days
            if notti <= 0: notti = 1
            
            prz_s, _ = calcola_prezzo_strategico(b1.day, b1.month, b1.year, STRUTTURE[su])
            pt = st.number_input("Totale", value=float(prz_s * notti))
            ac = st.number_input("Acconto", value=0.0)
            
            if st.form_submit_button("SALVA NEL DATABASE"):
                nuove = []
                for i in range(notti):
                    giorno = (b1 + timedelta(days=i)).strftime("%Y-%m-%d")
                    nuove.append({
                        "Data": giorno, "Struttura": su, "Nome": nm, 
                        "Tel": tl, "Note": nt, "Prezzo_Totale": pt, 
                        "Acconto": ac, "Saldo": pt-ac
                    })
                if salva_prenotazione(nuove):
                    st.success("Sincronizzazione completata!")
                    st.rerun()

    with c_del:
        st.subheader("🗑️ CANCELLA")
        del_date = st.date_input("Giorno da liberare")
        del_struct = st.selectbox("Unità", list(STRUTTURE.keys()), key="del_s")
        if st.button("ELIMINA PRENOTAZIONE", type="primary"):
            if elimina_prenotazione(del_date.strftime("%Y-%m-%d"), del_struct):
                st.warning("Prenotazione eliminata.")
                st.rerun()

    # DEBUG VIEW
    with st.expander("Visualizza Tabella Dati Crudi (Database)"):
        st.dataframe(df_p)

if __name__ == "__main__":
    main()