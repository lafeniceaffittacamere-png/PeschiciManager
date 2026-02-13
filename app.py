import streamlit as st
import calendar
import json
import os
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Peschici Manager 2026", layout="wide", page_icon="🏡")

# --- CSS: CELLE GIGANTI E LEGGBILI ---
st.markdown("""
    <style>
    /* Stile Bottoni del Calendario */
    div.stButton > button {
        width: 100%;
        height: 150px !important; /* ALTEZZA AUMENTATA PER VEDERE TUTTO */
        white-space: pre-wrap !important; /* Testo a capo */
        text-align: left !important;
        padding: 5px !important;
        border-radius: 8px !important;
        border: 1px solid #bbb !important;
        font-size: 13px !important;
        line-height: 1.3 !important;
        vertical-align: top !important;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Hover */
    div.stButton > button:hover {
        border-color: #000 !important;
        background-color: #e3f2fd !important;
    }

    /* Bottoni Navigazione in alto (più piccoli) */
    div[data-testid="column"] > div.stButton > button {
        height: 50px !important;
        background-color: #eeeeee;
        text-align: center !important;
        font-weight: bold !important;
        font-size: 18px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
if 'anno' not in st.session_state: st.session_state.anno = 2026
if 'mese' not in st.session_state: st.session_state.mese = datetime.now().month
# IMPOSTATO DEFAULT SU "INTERA VILLA" COME RICHIESTO
if 'struttura' not in st.session_state: st.session_state.struttura = "Il Melograno (INTERA VILLA)"
if 'selezione' not in st.session_state: st.session_state.selezione = [] 

# --- DATI STRUTTURE ---
STRUTTURE = {
    "Il Melograno (INTERA VILLA)":       {"base": 88.0,  "pulizie": 40.0}, 
    "Il Melograno (SUITE INDIPENDENTE)": {"base": 50.0,  "pulizie": 20.0},
    "Il Melograno (FAMILY SUITE)":       {"base": 60.0,  "pulizie": 25.0},
    "Villetta Baia S.Nicola":            {"base": 120.0, "pulizie": 60.0},
    "Casa Centro Storico":               {"base": 95.0,  "pulizie": 45.0},
    "Appartamento Il Trabucco":          {"base": 100.0, "pulizie": 50.0},
    "Monolocale Castello":               {"base": 85.0,  "pulizie": 35.0},
    "Villa degli Ulivi":                 {"base": 140.0, "pulizie": 70.0}
}
PARENT_UNIT = "Il Melograno (INTERA VILLA)"
CHILD_UNITS = ["Il Melograno (SUITE INDIPENDENTE)", "Il Melograno (FAMILY SUITE)"]

# --- FILE SYSTEM ---
def get_filenames(anno, struttura):
    s_safe = struttura.replace(" ", "_").lower()
    return f"prenotazioni_{anno}_{s_safe}.json"

def carica_dati(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

def salva_dati(path, dati):
    with open(path, 'w', encoding='utf-8') as f: json.dump(dati, f, indent=4)

# --- MOTORE EVENTI (NON TOCCATO) ---
def calcola_pasqua(anno):
    a = anno % 19; b = anno // 100; c = anno % 100; d = b // 4; e = b % 4
    f = (b + 8) // 25; g = (b - f + 1) // 3; h = (19 * a + b - d - g + 15) % 30
    i = c // 4; k = c % 4; l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mese = (h + l - 7 * m + 114) // 31
    giorno = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(anno, mese, giorno)

def get_eventi_completi(anno):
    eventi = []
    p = calcola_pasqua(anno)
    pq = p + timedelta(days=1)
    
    # Feste fisse
    feste = [
        (1, 1, "CAPODANNO", 1.5), (1, 6, "EPIFANIA", 1.3),
        (4, 25, "LIBERAZIONE", 1.3), (5, 1, "PRIMO MAGGIO", 1.4),
        (6, 2, "REPUBBLICA", 1.4), (8, 15, "FERRAGOSTO", 2.5),
        (11, 1, "OGNISSANTI", 1.3), (12, 8, "IMMACOLATA", 1.3),
        (12, 25, "NATALE", 1.5), (12, 31, "S.SILVESTRO", 1.8),
        (p.month, p.day, "PASQUA", 1.4), (pq.month, pq.day, "PASQUETTA", 1.3)
    ]
    for m, d, n, w in feste: eventi.append({"m": m, "d": d, "n": n, "w": w})

    # EVENTI LOCALI 2026 (Lista Originale)
    if anno == 2026:
        # Ponti
        extra = [(5, 2, "PONTE 1 MAG", 1.4), (5, 3, "PONTE 1 MAG", 1.4), (6, 1, "PONTE 2 GIU", 1.4)]
        # Eventi Specifici
        ranges = [
            (6, 20, 21, "TRIATHLON", 1.2),
            (7, 4, 5, "ZAIANA OPEN", 1.6),
            (7, 11, 12, "WKND ZAIANA", 1.5),
            (7, 18, 18, "WKND ZAIANA", 1.5),
            (7, 19, 21, "SANT'ELIA", 1.9),
            (8, 4, 10, "CARPINO FOLK", 1.6),
            (8, 10, 10, "S.LORENZO", 1.8),
            (8, 14, 14, "FERRAGOSTO B.", 2.7),
            (8, 8, 22, "GOLD WEEK", 2.5),
            (8, 26, 28, "JAZZ", 1.3),
            (9, 8, 10, "MADONNA CALENA", 1.2)
        ]
        for m, d, n, w in extra: eventi.append({"m": m, "d": d, "n": n, "w": w})
        for m, d_s, d_e, n, w in ranges:
            for d in range(d_s, d_e + 1):
                eventi.append({"m": m, "d": d, "n": n, "w": w})
        
        # Generazione Automatica Weekend Zaiana
        for m in [7, 8]:
            for d in range(1, 32):
                try:
                    dt = datetime(anno, m, d)
                    if dt.weekday() in [4, 5]: # Ven/Sab
                        if not any(e['m'] == m and e['d'] == d for e in eventi):
                            eventi.append({"m": m, "d": d, "n": "ZAIANA PARTY", "w": 1.2})
                except: continue
    return eventi

# --- CALCOLO PREZZI ---
def calcola_prezzo(giorno, mese, anno, info, eventi_db):
    molt = 1.0
    prezzo_base = info['base']
    
    if mese in [11, 12, 1, 2]: molt = 0.60
    elif mese in [3, 10]: molt = 0.75
    elif mese in [4, 5]: molt = 0.90
    elif mese == 6: molt = 1.15
    elif mese == 9: molt = 1.10
    elif mese == 7: molt = 1.60
    elif mese == 8: molt = 2.00
    
    try:
        dt = datetime(anno, mese, giorno)
        if dt.weekday() in [4, 5] and mese in [6, 7, 8, 9]: molt *= 1.15
    except: pass

    ev_nome = ""
    w_max = 0
    for e in eventi_db:
        if e['m'] == mese and e['d'] == giorno:
            if e['w'] > w_max:
                w_max = e['w']
                ev_nome = e['n']
    
    if w_max > 0:
        if w_max > molt: molt = w_max
        else: molt *= 1.05

    prezzo_finale = max(prezzo_base * molt, info['pulizie'] + 25)
    return int(prezzo_finale), ev_nome

# --- GESTIONE CLICK ---
def gestisci_click(giorno):
    dt = datetime(st.session_state.anno, st.session_state.mese, giorno).date()
    if dt in st.session_state.selezione:
        st.session_state.selezione.remove(dt)
    else:
        st.session_state.selezione.append(dt)
        st.session_state.selezione.sort()
        if len(st.session_state.selezione) > 2:
            st.session_state.selezione = [dt]

# --- UI MAIN ---
def main():
    # SIDEBAR
    st.sidebar.title("Peschici Manager")
    st.sidebar.caption("Versione Drive 2026")
    
    # Selezione Struttura
    lista = list(STRUTTURE.keys())
    # Assicuro che l'indice esista (per evitare errori se cambi codice)
    if st.session_state.struttura not in lista: st.session_state.struttura = lista[0]
    idx = lista.index(st.session_state.struttura)
    
    nuova_s = st.sidebar.selectbox("Struttura", lista, index=idx)
    if nuova_s != st.session_state.struttura:
        st.session_state.struttura = nuova_s
        st.session_state.selezione = []
        st.rerun()

    # CARICAMENTO
    info = STRUTTURE[st.session_state.struttura]
    f_pren = get_filenames(st.session_state.anno, st.session_state.struttura)
    prenotazioni = carica_dati(f_pren)
    eventi_list = get_eventi_completi(st.session_state.anno)

    # CONFLITTI PARENT/CHILD
    conflitti = []
    da_check = CHILD_UNITS if st.session_state.struttura == PARENT_UNIT else ([PARENT_UNIT] if st.session_state.struttura in CHILD_UNITS else [])
    for u in da_check:
        f_ext = get_filenames(st.session_state.anno, u)
        p_ext = carica_dati(f_ext)
        conflitti.extend(list(p_ext.keys()))

    # --- HEADER NAVIGAZIONE ---
    col1, col2, col3 = st.columns([1, 4, 1])
    if col1.button("◀ INDIETRO", use_container_width=True):
        st.session_state.mese -= 1
        if st.session_state.mese < 1: st.session_state.mese=12; st.session_state.anno-=1
        st.session_state.selezione = []
        st.rerun()

    with col2:
        titolo = f"{calendar.month_name[st.session_state.mese].upper()} {st.session_state.anno}"
        st.markdown(f"<h1 style='text-align: center; margin:0; color:#006064'>{titolo}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center; margin:0; color:#555'>{st.session_state.struttura}</h3>", unsafe_allow_html=True)

    if col3.button("AVANTI ▶", use_container_width=True):
        st.session_state.mese += 1
        if st.session_state.mese > 12: st.session_state.mese=1; st.session_state.anno+=1
        st.session_state.selezione = []
        st.rerun()

    st.write("") # Spaziatura

    # --- GRIGLIA CALENDARIO ---
    cal = calendar.monthcalendar(st.session_state.anno, st.session_state.mese)
    giorni = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]
    
    cols = st.columns(7)
    for i, g in enumerate(giorni): cols[i].markdown(f"<div style='text-align:center; font-weight:bold'>{g}</div>", unsafe_allow_html=True)

    for week in cal:
        cols = st.columns(7)
        for i, giorno in enumerate(week):
            with cols[i]:
                if giorno == 0:
                    st.write("")
                    continue
                
                # Calcoli Data
                dt_obj = datetime(st.session_state.anno, st.session_state.mese, giorno).date()
                dt_str = dt_obj.strftime("%Y-%m-%d")
                prz, nm_ev = calcola_prezzo(giorno, st.session_state.mese, st.session_state.anno, info, eventi_list)
                
                # --- COSTRUZIONE ETICHETTA ---
                # Riga 1: Numero Giorno (Grassetto)
                label = f"{giorno}"
                tipo_btn = "secondary"
                disabled = False
                
                # CASO 1: BLOCCO DA ALTRA UNITA'
                if dt_str in conflitti:
                    label += "\n🔒 BLOCCO\n(Altra Unità)"
                    disabled = True
                
                # CASO 2: PRENOTATO
                elif dt_str in prenotazioni:
                    p = prenotazioni[dt_str]
                    # Gestione compatibilità dati
                    if isinstance(p, dict):
                        nome = p.get('nome', 'Ospite')
                        tel = p.get('tel', '')
                    else:
                        nome = p[0].split('|')[0]
                        tel = "?"
                    
                    # QUI C'È LA MODIFICA: NUMERO DI TELEFONO VISIBILE NELLA CELLA
                    label += f"\n⛔ {nome}\n📞 {tel}"
                    disabled = True 
                
                # CASO 3: LIBERO
                else:
                    if nm_ev: label += f"\n🎉 {nm_ev}" # Evento
                    label += f"\n💰 {prz}€"

                # CASO 4: SELEZIONATO
                if dt_obj in st.session_state.selezione:
                    label = f"✅ {giorno}\nSELEZIONATO"
                    tipo_btn = "primary"

                # RENDER BOTTONE
                if st.button(label, key=f"d_{giorno}", type=tipo_btn, disabled=disabled):
                    gestisci_click(giorno)
                    st.rerun()

    # --- AREA AZIONI ---
    if len(st.session_state.selezione) > 0:
        st.markdown("---")
        d_sel = sorted(st.session_state.selezione)
        d_in = d_sel[0]
        d_out = d_sel[-1]
        
        if len(d_sel) == 1:
            st.warning("👇 Seleziona la data di PARTENZA cliccando su un'altra casella.")
        else:
            notti = (d_out - d_in).days
            if notti == 0: notti = 1
            
            # Preventivo
            tot = 0
            for x in range(notti):
                g = d_in + timedelta(days=x)
                p, _ = calcola_prezzo(g.day, g.month, g.year, info, eventi_list)
                tot += p
            
            st.success(f"📅 Periodo: {d_in.strftime('%d/%m')} - {d_out.strftime('%d/%m')} ({notti} notti)")
            
            with st.form("prenota"):
                col_a, col_b, col_c = st.columns(3)
                nome = col_a.text_input("Nome Cliente")
                tel = col_b.text_input("Telefono")
                prezzo = col_c.number_input(f"Totale (€)", value=tot)
                
                if st.form_submit_button("SALVA PRENOTAZIONE ✅", use_container_width=True):
                    if not nome: st.error("Manca il Nome!")
                    else:
                        giorni = [d_in + timedelta(days=x) for x in range(notti)]
                        # Check conflitto finale
                        err = False
                        for g in giorni:
                            k = g.strftime("%Y-%m-%d")
                            if k in prenotazioni or k in conflitti: err = True
                        
                        if err: st.error("Errore: Date occupate nel mezzo!")
                        else:
                            for g in giorni:
                                k = g.strftime("%Y-%m-%d")
                                prenotazioni[k] = {"nome": nome, "tel": tel, "prezzo": prezzo/notti}
                            salva_dati(f_pren, prenotazioni)
                            st.session_state.selezione = []
                            st.balloons()
                            st.rerun()

    # LISTA RIASSUNTIVA SOTTO
    st.markdown("---")
    st.caption("Gestione Rapida Prenotazioni Mese")
    keys = [k for k in prenotazioni if f"-{st.session_state.mese:02d}-" in k]
    if keys:
        for k in sorted(keys):
            p = prenotazioni[k]
            n = p.get('nome','?') if isinstance(p,dict) else p[0].split('|')[0]
            with st.expander(f"Giorno {k[8:10]} - {n}"):
                if st.button("Cancella Prenotazione", key=f"del_{k}"):
                    del prenotazioni[k]
                    salva_dati(f_pren, prenotazioni)
                    st.rerun()

if __name__ == "__main__":
    main()