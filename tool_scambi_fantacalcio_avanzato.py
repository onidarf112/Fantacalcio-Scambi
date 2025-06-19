import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import percentileofscore
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Fantacalcio - Scambi Avanzati Pro", layout="wide")
st.markdown("""
<h1 style='text-align: center; color: #1E90FF;'>⚽ Fantacalcio<br><span style='font-size: 26px;'>Scambi Avanzati Pro</span></h1>
""", unsafe_allow_html=True)

# Sidebar per configurazioni
st.sidebar.markdown("## ⚙️ Configurazioni")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Soglia Scambi")
soglia_max = st.sidebar.slider("🎯 Soglia Massima (%) Differenza", 0.0, 50.0, 10.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Pesi Formula Punteggio")
peso_fvm = st.sidebar.slider("Peso FVM M", 0.0, 1.0, 0.30, step=0.05)
peso_fm = st.sidebar.slider("Peso Fm", 0.0, 1.0, 0.25, step=0.05)
peso_qta = st.sidebar.slider("Peso Qt.A", 0.0, 1.0, 0.20, step=0.05)
peso_pres = st.sidebar.slider("Peso Presenze", 0.0, 1.0, 0.15, step=0.05)
peso_bonus = st.sidebar.slider("Peso Bonus/Malus", 0.0, 1.0, 0.10, step=0.05)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚖️ Scale per Ruolo")
scala_por = st.sidebar.slider("Scala Portieri", 80, 150, 120, step=5)
scala_dif = st.sidebar.slider("Scala Difensori", 100, 170, 140, step=5)
scala_cen = st.sidebar.slider("Scala Centrocampisti", 120, 190, 160, step=5)
scala_att = st.sidebar.slider("Scala Attaccanti", 140, 200, 180, step=5)

# Normalizzazione pesi
totale_pesi = peso_fvm + peso_fm + peso_qta + peso_pres + peso_bonus
if totale_pesi != 1.0:
    st.sidebar.warning(f"⚠️ Totale pesi: {totale_pesi:.2f} (dovrebbe essere 1.0)")

# Caricamento file
st.markdown("#### 📁 Carica i tuoi file Excel")
col1, col2 = st.columns(2)
with col1:
    file_quot = st.file_uploader("Carica Quotazioni (.xlsx)", type="xlsx")
    if file_quot:
        st.success(f"✅ Quotazioni caricate: {file_quot.name}")
with col2:
    file_stat = st.file_uploader("Carica Statistiche (.xlsx)", type="xlsx")
    if file_stat:
        st.success(f"✅ Statistiche caricate: {file_stat.name}")

if file_quot and file_stat:
    try:
        df_quot = pd.read_excel(file_quot, header=1)
        df_stat = pd.read_excel(file_stat, header=1)
        df = pd.merge(df_quot, df_stat, on="Nome", how="inner", suffixes=("_quot", "_stat"))
        df["R"] = df["R_stat"]
        df["Squadra"] = df["Squadra_quot"]

        colonne_necessarie = ["FVM M", "Fm", "Qt.A", "Pv", "Gf", "Ass", "Amm", "Esp", "Rp", "Rc", "R"]
        colonne_mancanti = [col for col in colonne_necessarie if col not in df.columns]
        if colonne_mancanti:
            st.error(f"Colonne mancanti: {', '.join(colonne_mancanti)}")
            st.stop()

        df["Perc_FVM_M"] = df["FVM M"].rank(pct=True)
        df["Perc_FM"] = df["Fm"].rank(pct=True)
        df["Perc_QTA"] = df["Qt.A"].rank(pct=True)
        df["Perc_Pres"] = df["Pv"].rank(pct=True)

        def calcola_bonus_ruolo(row):
            ruolo = row["R"]
            if ruolo == "Por":
                return 10 * row["Gf"] + 3 * row["Ass"] + 8 * row["Rp"] - 1 * row["Amm"] - 6 * row["Esp"]
            elif ruolo == "Dif":
                return 5 * row["Gf"] + 3 * row["Ass"] + 1 * row["Rp"] + 0.5 * row["Rc"] - 1.5 * row["Amm"] - 4 * row["Esp"]
            elif ruolo == "Cen":
                return 3.5 * row["Gf"] + 4 * row["Ass"] + 3 * row["Rp"] + 2 * row["Rc"] - 1.5 * row["Amm"] - 3 * row["Esp"]
            else:
                return 2.5 * row["Gf"] + 2.5 * row["Ass"] + 4 * row["Rp"] + 2 * row["Rc"] - 2 * row["Amm"] - 3 * row["Esp"]

        df["BonusRaw"] = df.apply(calcola_bonus_ruolo, axis=1)

        df["BonusNorm"] = 0
        for ruolo in df["R"].unique():
            mask = df["R"] == ruolo
            bonus_ruolo = df.loc[mask, "BonusRaw"]
            if bonus_ruolo.max() != bonus_ruolo.min():
                df.loc[mask, "BonusNorm"] = (bonus_ruolo - bonus_ruolo.min()) / (bonus_ruolo.max() - bonus_ruolo.min())

        punteggio_base = (
            peso_fvm * df["Perc_FVM_M"] +
            peso_fm * df["Perc_FM"] +
            peso_qta * df["Perc_QTA"] +
            peso_pres * df["Perc_Pres"] +
            peso_bonus * df["BonusNorm"]
        )

        df["Punteggio"] = 0
        scale_ruolo = {"Por": scala_por, "Dif": scala_dif, "Cen": scala_cen, "Att": scala_att}

        for ruolo in df["R"].unique():
            mask = df["R"] == ruolo
            scala_ruolo = scale_ruolo.get(ruolo, 150)
            df.loc[mask, "Punteggio"] = punteggio_base[mask] * scala_ruolo

    except Exception as e:
        st.error(f"Errore durante l'elaborazione: {e}")
        st.write("Controlla che i file abbiano il formato corretto e tutte le colonne necessarie.")
