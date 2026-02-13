import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import calendar
from datetime import datetime, timedelta
from sqlalchemy import text

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Victory Radar Peschici PRO", layout="wide")

# Connessione DB
conn = st.connection('mysql', type='sql')

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

# --- 3. FUNZIONI DATI ---
def carica_prenotazioni():
    try:
        df = conn.query("SELECT * FROM prenotazioni", ttl=0)
        if df is not None and not df.empty:
            df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%Y-%m-%d')
        return df
    except: return pd.DataFrame()

def salva_prenotazione(lista_p):
    try:
        with conn.session as s:
            for p in lista_p:
                s.execute(text("INSERT INTO prenotazioni (Data, Struttura, Nome, Tel, Note, Prezzo_Totale, Acconto, Saldo) VALUES (:Data, :Struttura, :Nome, :Tel, :Note, :Prezzo_Totale, :Acconto, :Saldo)"), p)
            s.commit()
        return True
    except: return False

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
    ev_oggi = [e for e in EVENTI_BASE if e['m'] == mese and e['s'] <= giorno <= e['e']]
    if ev_oggi: molt = max(molt, max([e['w'] for e in ev_oggi]))
    if dt.weekday() >= 4: molt *= 1.15
    return int(info['base'] * molt), ev_oggi

# --- 4. COSTRUZIONE HTML PER IFRAME ---
def genera_html_tabella(df_p, mese, anno):
    num_days = calendar.monthrange(anno, mese)[1]
    
    css = """
    <style>
        body { font-family: sans-serif; margin: 0; padding: 0; }
        .planning-container { overflow-x: auto; border: 1px solid #ccc; }
        table { border-collapse: collapse; width: 100%; font-size: 11px; table-layout: fixed; }
        th, td { border: 1px solid #ddd; width: 80px; height: 60px; text-align: center; }
        .sticky-col { position: sticky; left: 0; background: #2e7d32; color: white; width: 140px; z-index: 10; text-align: left; padding-left: 5px; }
        .booked { background: #ffcdd2 !important; color: #b71c1c; font-weight: bold; }
        .locked { background: #f0f0f0 !important; color: #ccc; }
        .price { color: #2e7d32; font-weight: bold; font-size: 12px; }
        .ev { color: #f57f17; font-size: 9px; font-weight: bold; }
    </style>
    """
    
    html = f'{css}<div class="planning-container"><table><thead><tr><th class="sticky-col">STRUTTURA</th>'
    for d in range(1, num_days + 1):
        dt_t = datetime(anno, mese, d)
        bg = "#c8e6c9" if dt_t.weekday() >= 5 else "#fff"
        html += f'<th style="background:{bg}">{d}<br>{dt_t.strftime("%a")}</th>'
    html += '</tr></thead><tbody>'

    # Riga Eventi
    html += '<tr><td class="sticky-col" style="background:#fff9c4; color:#f57f17">📡 RADAR</td>'
    for d in range(1, num_days + 1):
        _, evs = calcola_prezzo_strategico(d, mese, anno, {"base":100})
        txt = " ".join([e["n"][:8] for e in evs])
        html += f'<td style="background:#fff9c4" class="ev">{txt}</td>'
    html += '</tr>'

    for ns, info in STRUTTURE.items():
        target = CHILD_UNITS if ns == PARENT_UNIT else ([PARENT_UNIT] if ns in CHILD_UNITS else [])
        blocked = df_p[df_p['Struttura'].isin(target)]['Data'].tolist() if not df_p.empty else []
        
        html += f'<tr><td class="sticky-col">{ns}</td>'
        for d in range(1, num_days + 1):
            k = f"{anno}-{mese:02d}-{d:02d}"
            res = df_p[(df_p['Data'] == k) & (df_p['Struttura'] == ns)] if not df_p.empty else pd.DataFrame()
            
            if k in blocked: html += '<td class="locked">🔒</td>'
            elif not res.empty: html += f'<td class="booked">{str(res.iloc[0]["Nome"])[:9]}</td>'
            else:
                p, _ = calcola_prezzo_strategico(d, mese, anno, info)
                html += f'<td><span class="price">€{p}</span></td>'
        html += '</tr>'
    
    return html + '</tbody></table></div>'

# --- 5. MAIN UI ---
def main():
    st.title("Victory Radar Peschici 2026")

    # Controlli Mese
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ Mese Prec."):
        st.session_state.mese -= 1
        if st.session_state.mese < 1: st.session_state.mese = 12; st.session_state.anno -= 1
        st.rerun()
    c2.markdown(f"<h2 style='text-align:center'>{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}</h2>", unsafe_allow_html=True)
    if c3.button("Mese Succ. ▶"):
        st.session_state.mese += 1
        if st.session_state.mese > 12: st.session_state.mese = 1; st.session_state.anno += 1
        st.rerun()

    df_p = carica_prenotazioni()
    
    # RENDERING TABELLA VIA IFRAME (La soluzione definitiva al removeChild)
    tab_html = genera_html_tabella(df_p, st.session_state.mese, st.session_state.anno)
    components.html(tab_html, height=600, scrolling=True)

    # --- AZIONI ---
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        with st.form("bk"):
            st.subheader("📝 Prenota")
            f_s = st.selectbox("Unità", list(STRUTTURE.keys()))
            f_i = st.date_input("In"); f_o = st.date_input("Out")
            f_n = st.text_input("Nome")
            if st.form_submit_button("Salva"):
                n = (f_o - f_i).days if (f_o - f_i).days > 0 else 1
                p_b, _ = calcola_prezzo_strategico(f_i.day, f_i.month, f_i.year, STRUTTURE[f_s])
                payload = [{"Data": (f_i + timedelta(days=i)).strftime("%Y-%m-%d"), "Struttura": f_s, "Nome": f_n, "Tel": "", "Note": "", "Prezzo_Totale": p_b*n, "Acconto": 0, "Saldo": p_b*n} for i in range(n)]
                if salva_prenotazione(payload): st.rerun()

    with col_b:
        st.subheader("🗑️ Elimina")
        d_d = st.date_input("Giorno"); d_s = st.selectbox("Unità", list(STRUTTURE.keys()), key="del")
        if st.button("ELIMINA"):
            if elimina_prenotazione(d_d.strftime("%Y-%m-%d"), d_s): st.rerun()

if __name__ == "__main__":
    main()