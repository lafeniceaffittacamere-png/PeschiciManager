import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from sqlalchemy import text

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Victory Radar Peschici DB-PRO", layout="wide")

# --- 2. CONNESSIONE DATABASE ---
# Assicurati di avere SQLAlchemy e mysqlclient nel requirements.txt
conn = st.connection('mysql', type='sql')

# --- 3. INIZIALIZZAZIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = 2

# --- 4. COSTANTI ---
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

EVENTI_BASE = [
    {"m": 6, "s": 20, "e": 21, "n": "TRIATHLON", "w": 1.5},
    {"m": 7, "s": 4,  "e": 5,  "n": "ZAIANA OPEN", "w": 1.6},
    {"m": 7, "s": 19, "e": 21, "n": "SANT'ELIA", "w": 2.2},
    {"m": 8, "s": 14, "e": 16, "n": "FERRAGOSTO B.", "w": 2.8},
    {"m": 8, "s": 8,  "e": 22, "n": "GOLD WEEK", "w": 2.5},
    {"m": 8, "s": 26, "e": 28, "n": "PESCHICI JAZZ", "w": 1.4},
]

# --- 5. FUNZIONI DATI ---
def carica_prenotazioni():
    try:
        df = conn.query("SELECT * FROM prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m-%d')
        return df
    except:
        return pd.DataFrame(columns=["Data", "Struttura", "Nome", "Tel", "Note", "Prezzo_Totale", "Acconto", "Saldo"])

def salva_prenotazione(lista_p):
    try:
        with conn.session as s:
            for p in lista_p:
                query = text("""INSERT INTO prenotazioni (Data, Struttura, Nome, Tel, Note, Prezzo_Totale, Acconto, Saldo) 
                                VALUES (:Data, :Struttura, :Nome, :Tel, :Note, :Prezzo_Totale, :Acconto, :Saldo)""")
                s.execute(query, p)
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
    except:
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

# --- 6. STILI ---
CSS = """
<style>
    .planning-container { overflow-x: auto; background: white; border: 1px solid #a5d6a7; border-radius: 8px; font-family: sans-serif; }
    table { border-collapse: collapse; width: 100%; border-spacing: 0; }
    th, td { padding: 4px; text-align: center; border: 1px solid #eee; min-width: 85px; height: 70px; }
    .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; font-weight: bold; min-width: 160px; z-index: 5; text-align: left; padding-left: 8px; font-size: 12px; }
    .cell-booked { background: #ffcdd2 !important; color: #b71c1c !important; font-weight: bold; font-size: 11px; border-left: 4px solid #d32f2f !important; }
    .cell-lock { background: #f5f5f5 !important; color: #bbb !important; }
    .ev-tag { color: #f57f17; font-weight: bold; font-size: 9px; }
    .info-price { font-size: 13px; color: #1b5e20; font-weight: bold; }
</style>
"""

# --- 7. MAIN UI ---
def main():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#2e7d32;'>VICTORY RADAR PRO (MySQL)</h2>", unsafe_allow_html=True)

    # Navigazione
    col_n1, col_n2, col_n3 = st.columns([1, 4, 1])
    with col_n1:
        if st.button("◀ Mese Prec."):
            st.session_state.mese -= 1
            if st.session_state.mese < 1: st.session_state.mese = 12; st.session_state.anno -= 1
            st.rerun()
    with col_n2:
        st.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h3>", unsafe_allow_html=True)
    with col_n3:
        if st.button("Mese Succ. ▶"):
            st.session_state.mese += 1
            if st.session_state.mese > 12: st.session_state.mese = 1; st.session_state.anno += 1
            st.rerun()

    df_p = carica_prenotazioni()
    num_days = calendar.monthrange(st.session_state.anno, st.session_state.mese)[1]

    # --- COSTRUZIONE TABELLA ---
    html = '<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURE</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(st.session_state.anno, st.session_state.mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#e8f5e9"
        html += f'<th style="background:{bg};">{d}<br><small>{dt_t.strftime("%a")}</small></th>'
    html += '</tr></thead><tbody>'

    # Radar Eventi
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR EVENTI</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, {"base":100})
        txt = "<br>".join([f'<span class="ev-tag">{e["n"][:10]}</span>' for e in evs])
        html += f'<td style="background:#fff9c4;">{txt}</td>'
    html += '</tr>'

    # Righe Strutture
    for ns, info in STRUTTURE.items():
        # Logica Blocco Incrociato
        target_units = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        blocked_dates = df_p[df_p['Struttura'].isin(target_units)]['Data'].tolist() if not df_p.empty else []

        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{st.session_state.anno}-{st.session_state.mese:02d}-{d:02d}"
            res = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)] if not df_p.empty else pd.DataFrame()

            if k in blocked_dates:
                html += '<td class="cell-lock">🔒</td>'
            elif not res.empty:
                nome = str(res.iloc[0]["Nome"]).upper()[:10]
                html += f'<td class="cell-booked">{nome}</td>'
            else:
                p, _ = calcola_prezzo_strategico(d, st.session_state.mese, st.session_state.anno, info)
                html += f'<td><span class="info-price">€{p}</span></td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    
    # Rendering Tabella con Placeholder per stabilità
    st.markdown(html, unsafe_allow_html=True)

    # --- AREA AZIONI ---
    st.markdown("---")
    col_form, col_del = st.columns(2)

    with col_form:
        with st.form("nuova_pre"):
            st.subheader("📝 Prenota")
            f_str = st.selectbox("Unità", list(STRUTTURE.keys()))
            f_in = st.date_input("Check-in")
            f_out = st.date_input("Check-out")
            f_nom = st.text_input("Nome")
            f_tel = st.text_input("Tel")
            f_not = st.text_input("Note")
            
            notti = (f_out - f_in).days
            prz_base, _ = calcola_prezzo_strategico(f_in.day, f_in.month, f_in.year, STRUTTURE[f_str])
            f_tot = st.number_input("Totale (€)", value=float(prz_base * (notti if notti > 0 else 1)))
            f_acc = st.number_input("Acconto (€)", value=0.0)

            if st.form_submit_button("CONFERMA PRENOTAZIONE"):
                if notti <= 0: notti = 1
                payload = []
                for i in range(notti):
                    g = (f_in + timedelta(days=i)).strftime("%Y-%m-%d")
                    payload.append({
                        "Data": g, "Struttura": f_str, "Nome": f_nom, "Tel": f_tel,
                        "Note": f_not, "Prezzo_Totale": f_tot, "Acconto": f_acc, "Saldo": f_tot - f_acc
                    })
                if salva_prenotazione(payload):
                    st.success("Sincronizzato!")
                    st.rerun()

    with col_del:
        st.subheader("🗑️ Elimina")
        d_day = st.date_input("Giorno")
        d_str = st.selectbox("Unità da liberare", list(STRUTTURE.keys()))
        if st.button("ELIMINA PRENOTAZIONE", type="primary"):
            if elimina_prenotazione(d_day.strftime("%Y-%m-%d"), d_str):
                st.rerun()

    # Visualizzazione Dati per controllo
    with st.expander("Vedi Database"):
        st.dataframe(df_p)

if __name__ == "__main__":
    main()