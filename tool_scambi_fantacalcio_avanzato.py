
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import percentileofscore
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Fantacalcio - Scambi Avanzati by Onidarf ", layout="wide")
st.title("⚽ Fantacalcio - Tool Scambi Avanzati Pro")

# Sidebar per configurazioni
st.sidebar.header("⚙️ Configurazioni")

# Configurazione soglia scambi
st.sidebar.subheader("🔄 Configurazione Scambi")
soglia_max = st.sidebar.number_input(
    "🎯 Soglia Massima (%) Differenza", 
    min_value=0.0, 
    max_value=100.0, 
    value=10.0, 
    step=0.5,
    help="Differenza percentuale massima accettabile tra le squadre per considerare lo scambio valido"
)

# NUOVE OPZIONI PER COMPARABILITÀ
st.sidebar.subheader("🎯 Comparabilità Punteggi tra Ruoli")
usa_percentile_ruolo = st.sidebar.checkbox(
    "📊 Normalizzazione Percentile per Ruolo",
    value=False,
    help="Normalizza i punteggi rispetto al ruolo (top portiere = top attaccante)"
)

# Pesi personalizzabili
st.sidebar.subheader("📊 Pesi Formula Punteggio")
peso_fvm = st.sidebar.slider("Peso FVM M", 0.0, 1.0, 0.30, step=0.05)
peso_fm = st.sidebar.slider("Peso Fm", 0.0, 1.0, 0.25, step=0.05)
peso_qta = st.sidebar.slider("Peso Qt.A", 0.0, 1.0, 0.20, step=0.05)
peso_pres = st.sidebar.slider("Peso Presenze", 0.0, 1.0, 0.15, step=0.05)
peso_bonus = st.sidebar.slider("Peso Bonus/Malus", 0.0, 1.0, 0.10, step=0.05)

# Configurazione scale per ruolo (solo se non si usa percentile)
if not usa_percentile_ruolo:
    st.sidebar.subheader("⚖️ Scale Punteggio per Ruolo")
    scala_por = st.sidebar.slider("Scala Portieri", 80, 150, 120, step=5)
    scala_dif = st.sidebar.slider("Scala Difensori", 100, 170, 140, step=5)
    scala_cen = st.sidebar.slider("Scala Centrocampisti", 120, 190, 160, step=5)
    scala_att = st.sidebar.slider("Scala Attaccanti", 140, 200, 180, step=5)

# Normalizzazione pesi
totale_pesi = peso_fvm + peso_fm + peso_qta + peso_pres + peso_bonus
if totale_pesi != 1.0:
    st.sidebar.warning(f"⚠️ Totale pesi: {totale_pesi:.2f} (dovrebbe essere 1.0)")

# Istruzioni
with st.expander("📋 Istruzioni d'uso"):
    st.write("""
    **Come usare il tool:**

    1. **Carica i file Excel** delle quotazioni e statistiche
    2. **Configura i pesi** nella sidebar per personalizzare la formula
    3. **Esplora le diverse tab:**
       - 🏆 **Classifica**: Top giocatori con filtri avanzati
       - 🔄 **Scambi**: Simula scambi tra squadre
       - 📈 **Analisi**: Grafici e correlazioni
       - 🎯 **Raccomandazioni**: Giocatori sottovalutati
       - 📊 **Statistiche**: Dati aggregati per ruolo

    **Caratteristiche del sistema:**
    - ✅ Punteggi specifici per ruolo
    - ✅ Fattore continuità basato sulle presenze
    - ✅ Analisi sottovalutati
    - ✅ Grafici interattivi
    - ✅ Filtri avanzati
    """)

with st.expander("🔍 Dettaglio Sistema Punteggio"):
    st.write("""
    **📊 Sistema di Punteggio Ruolo-Specifico:**

    **🎯 NOVITÀ - Comparabilità tra Ruoli:**
    - **Normalizzazione Percentile**: I punteggi sono comparabili tra ruoli diversi
    - **Ora puoi scambiare il top portiere con il top attaccante!**

    **🥅 PORTIERI (Scala classica: 80-150)**
    - Gol: x10 (rarissimi, massimo valore)
    - Assist: x3 (rari ma preziosi)  
    - Rigori Parati: x8 (specialità del ruolo)
    - Ammonizioni: -1 (meno gravi)
    - Espulsioni: -6 (molto gravi)

    **🛡️ DIFENSORI (Scala classica: 100-170)**
    - Gol: x5 (molto preziosi)
    - Assist: x3 (importanti)
    - Rigori: x1 (meno comuni)
    - Ammonizioni: -1.5 (più accettabili)
    - Espulsioni: -4 (gravi)

    **⚽ CENTROCAMPISTI (Scala classica: 120-190)**
    - Gol: x4 (buoni)
    - Assist: x3 (frequenti)
    - Rigori Parati/Segnati: x3 (importanti)
    - Rigori Calciati: x2 (frequenti)
    - Ammonizioni: -1.5 (nella media)

    **🎯 ATTACCANTI (Scala classica: 140-200)**
    - Gol: x2.5 (dovere del ruolo)
    - Assist: x2.5 (comunque utili)
    - Rigori Parati/Segnati: x4 (molto importanti)
    - Rigori Calciati: x2 (frequenti)
    - Ammonizioni: -2 (più pesanti)

    **🔄 Modalità Percentile (Nuova!):**
    - Tutti i ruoli hanno scala 50-1000
    - Il miglior giocatore per ruolo ha punteggio simile
    - Perfetto per scambi cross-ruolo
    """)

# FUNZIONE BONUS AGGIORNATA

def calcola_bonus_ruolo(row):
    ruolo = row["R"]
    if ruolo == "Por":
        return 10 * row["Gf"] + 3 * row["Ass"] + 8 * row["Rp"] - 1 * row["Amm"] - 6 * row["Esp"]
    elif ruolo == "Dif":
        return 5 * row["Gf"] + 3 * row["Ass"] + 1 * row["Rp"] + 0.5 * row["Rc"] - 1.5 * row["Amm"] - 4 * row["Esp"]
    elif ruolo == "Cen":  # ⚠️ Modificato: Gol 4, Assist 3
        return 4 * row["Gf"] + 3 * row["Ass"] + 3 * row["Rp"] + 2 * row["Rc"] - 1.5 * row["Amm"] - 3 * row["Esp"]
    else:
        return 2.5 * row["Gf"] + 2.5 * row["Ass"] + 4 * row["Rp"] + 2 * row["Rc"] - 2 * row["Amm"] - 3 * row["Esp"]

# Quando calcoli i punteggi normalizzati percentile:
# df.loc[mask, "Punteggio"] = 50 + (percentili * 950)
# (per avere una scala finale da 50 a 1000)
