import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from sqlalchemy import text

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici PRO", layout="wide")

# --- 2. CONNESSIONE DATABASE ---
# Assicurati di avere SQLAlchemy e mysqlclient nel requirements.txt
conn = st.connection('mysql', type='sql')

# --- 3. INIZIALIZZAZIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2

# --- 4. COSTANTI E LOGICA PREZZI ---
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
PARENT_UNIT, CHILD_UNITS = "Il Melograno (VILLA)", ["Il Melograno (SUITE)", "Il Melograno (FAMILY)"]

EVENTI_BASE = [
    {"m": 6, "s": 20, "e": 21, "n": "TRIATHLON", "w": 1.5},
    {"m": 7, "s": 4,  "e": 5,  "n": "ZAIANA OPEN", "w": 1.6},
    {"m": 7, "s": 19, "e": 21, "n": "SANT'ELIA", "w": 2.2},
    {"m": 8, "s": 14, "e": 16, "n": "FERRAGOSTO B.", "w": 2.8},
    {"m": 8, "s": 8,  "e": 22, "n": "GOLD WEEK", "w": 2.5},
    {"m": 8, "s": 26, "e": 28, "n": "PESCHICI JAZZ", "w": 1.4},
]

# --- 5. FUNZIONI OPERATIVE ---
def carica_prenotazioni():
    try:
        return conn.query("SELECT * FROM prenotazioni", ttl=0)
    except:
        return pd.DataFrame()

def salva_prenotazione(lista_p):
    try:
        with conn.session as s:
            for p in lista_p:
                s.execute(text("""INSERT INTO prenotazioni (Data, Struttura, Nome, Tel, Note, Prezzo_Totale, Acconto, Saldo) 
                                VALUES (:Data, :Struttura, :Nome, :Tel, :Note, :Prezzo_Totale, :Acconto, :Saldo)"""), p)
            s.commit()
        return True
    except Exception as e:
        st.error(f"Errore: {e}")
        return False

def elimina_prenotazione(data, struttura):
    try:
        with conn.session as s:
            s.execute(text("DELETE FROM prenotazioni WHERE Data = :d AND Struttura = :s"), {"d": data, "s": struttura})
            s.commit()
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

# --- 6. INTERFACCIA UTENTE ---
def main():
    st.markdown("""
        <style>
        .main-container { overflow-x: auto; background: white; border-radius: 8px; border: 1px solid #ddd; }
        table { border-collapse: collapse; width: 100%; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        th, td { border: 1px solid #eee; min-width: 90px; height: 70px; text-align: center; font-size: 12px; }
        .sticky-col { position: sticky; left: 0; background: #1b5e20; color: white; font-weight: bold; min-width: 170px; z-index: 10; text-align: left; padding-left: 10px; }
        .booked { background: #ffcdd2 !important; color: #b71c1c; font-weight: bold; border-left: 5px solid #d32f2f !important; }
        .locked { background: #eeeeee !important; color: #999; }
        .price { font-weight: 800; color: #2e7d32; display: block; font-size: 14px; }
        .event-label { color: #f57f17; font-size: 10px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #2e7d32;'>Victory Radar Peschici</h1>", unsafe_allow_html=True)

    # Navigazione
    n1, n2, n3 = st.columns([1, 3, 1])
    if n1.button("◀ MESE PRECEDENTE"):
        st.session_state.mese -= 1
        if st.session_state.mese < 1: st.session_state.mese = 12; st.session_state.anno -= 1
        st.rerun()
    n2.markdown(f"<h2 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h2>", unsafe_allow_html=True)
    if n3.button("MESE SUCCESSIVO ▶"):
        st.session_state.mese += 1
        if st.session_state.mese > 12: st.session_state.mese = 1; st.session_state.anno += 1
        st.rerun()

    df_p = carica_prenotazioni()
    if not df_p.empty:
        df_p['Data'] = pd.to_datetime(df_p['Data']).dt.strftime('%Y-%m-%d')

    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # --- COSTRUZIONE TABELLA ---
    # translate="no" previene crash causati dai traduttori dei browser
    html = f'<div class="main-container" translate="no"><table><thead><tr><th class="sticky-col">UNITÀ</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#f1f8e9"
        html += f'<th style="background:{bg};">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    # Riga Radar
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100})
        txt = "".join([f'<div class="event-label">{ev["n"][:12]}</div>' for ev in evs])
        html += f'<td style="background:#fff9c4;">{txt}</td>'
    html += '</tr>'

    # Righe Strutture
    for ns, info in STRUTTURE.items():
        # Calcolo conflitti Villa/Suite
        target_units = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        blocked_dates = df_p[df_p['Struttura'].isin(target_units)]['Data'].tolist() if not df_p.empty else []

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            res = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)] if not df_p.empty else pd.DataFrame()

            if k in blocked_dates:
                html += '<td class="locked">🔒</td>'
            elif not res.empty:
                nome = str(res.iloc[0]["Nome"]).upper()[:10]
                html += f'<td class="booked">{nome}</td>'
            else:
                p, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                html += f'<td><span class="price">€{p}</span></td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'

    # IL TRUCCO: Usiamo un contenitore con chiave dinamica per evitare il removeChild error
    with st.container(border=False):
        st.markdown(html, unsafe_allow_html=True)

    # --- ZONA AZIONI ---
    st.markdown("---")
    col_book, col_del = st.columns(2)

    with col_book:
        with st.form("form_prenota", clear_on_submit=True):
            st.subheader("📝 Registra Prenotazione")
            f_unita = st.selectbox("Seleziona Unità", list(STRUTTURE.keys()))
            f_checkin = st.date_input("Check-in")
            f_checkout = st.date_input("Check-out")
            f_nome = st.text_input("Nome Ospite")
            f_tel = st.text_input("Telefono")
            f_note = st.text_area("Note")
            
            notti = (f_checkout - f_checkin).days
            prz_base, _ = calcola_prezzo_strategico(f_checkin.day, f_checkin.month, f_checkin.year, STRUTTURE[f_unita])
            f_totale = st.number_input("Prezzo Totale (€)", value=float(prz_base * (notti if notti > 0 else 1)))
            f_acconto = st.number_input("Acconto (€)", value=0.0)

            if st.form_submit_button("SALVA PRENOTAZIONE"):
                if notti <= 0: notti = 1
                batch = []
                for i in range(notti):
                    batch.append({
                        "Data": (f_checkin + timedelta(days=i)).strftime("%Y-%m-%d"),
                        "Struttura": f_unita, "Nome": f_nome, "Tel": f_tel,
                        "Note": f_note, "Prezzo_Totale": f_totale,
                        "Acconto": f_acconto, "Saldo": f_totale - f_acconto
                    })
                if salva_prenotazione(batch):
                    st.success("Prenotazione salvata con successo!")
                    st.rerun()

    with col_del:
        st.subheader("🗑️ Cancella Prenotazione")
        d_data = st.date_input("Data del giorno da liberare")
        d_unita = st.selectbox("Unità da liberare", list(STRUTTURE.keys()), key="del_un")
        if st.button("ELIMINA DEFINITIVAMENTE", type="primary"):
            if elimina_prenotazione(d_data.strftime("%Y-%m-%d"), d_unita):
                st.warning("Prenotazione rimossa dal database.")
                st.rerun()

    # Anteprima Tabella
    with st.expander("🔍 Log Dati (Database)"):
        st.write(df_p)

if __name__ == "__main__":
    main()