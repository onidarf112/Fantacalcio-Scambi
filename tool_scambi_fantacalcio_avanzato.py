import streamlit as st
import pandas as pd
from scipy.stats import percentileofscore

st.set_page_config(page_title="Fantacalcio - Tool Scambi", layout="wide")
st.title("⚽ Fantacalcio - Tool Scambi By Onidarf")

# Caricamento file
file_quot = st.file_uploader("Carica il file delle Quotazioni (.xlsx)", type="xlsx")
file_stat = st.file_uploader("Carica il file delle Statistiche (.xlsx)", type="xlsx")

soglia_max = st.slider("🎯 Soglia Massima (%) di Differenza Accettabile", 0.0, 50.0, 10.0, step=0.5)

if file_quot and file_stat:
    try:
        df_quot = pd.read_excel(file_quot, header=1)
        df_stat = pd.read_excel(file_stat, header=1)
        df = pd.merge(df_quot, df_stat, on="Nome", how="inner")
        
        # Controllo colonne richieste
        colonne_necessarie = ["FVM M", "Fm", "Qt.A", "Pv", "Gf", "Ass", "Amm", "Esp", "Rp", "Rc"]
        for col in colonne_necessarie:
            if col not in df.columns:
                st.error(f"Colonna mancante nel file: {col}")
                st.stop()
        
        # Calcolo percentili
        df["Perc_FVM_M"] = df["FVM M"].rank(pct=True)
        df["Perc_FM"] = df["Fm"].rank(pct=True)
        df["Perc_QTA"] = df["Qt.A"].rank(pct=True)
        df["Perc_Pres"] = df["Pv"].rank(pct=True)
        
        # Bonus/malus
        bonus_raw = (
    5 * stats.zscore(df["Gf"]) +
    2 * stats.zscore(df["Ass"]) +
    -1 * stats.zscore(df["Amm"]) +
    -2 * stats.zscore(df["Esp"]) +
    4 * stats.zscore(df["Rp"]) +
    1 * stats.zscore(df["Rc"])
)
        bonus_norm = (bonus_raw - bonus_raw.min()) / (bonus_raw.max() - bonus_raw.min())
        df["BonusMalus"] = bonus_norm.fillna(0)
        
        # Formula combinata
        # Aumenta il peso a 15-20%
df["Punteggio"] = (
    0.20 * df["Perc_FVM_M"] +
    0.35 * df["Perc_FM"] +
    0.20 * df["Perc_QTA"] +
    0.10 * df["Perc_Pres"] +
    0.15 * df["BonusMalus"]  # Aumentato da 0.05
) * 150
        
        # Sezione per mostrare i 30 migliori punteggi
        st.subheader("🏆 Top 30 Migliori Punteggi")
        top_30 = df.nlargest(30, "Punteggio")[["Nome", "Punteggio", "FVM M", "Fm", "Qt.A", "Pv"]]
        top_30_display = top_30.copy()
        top_30_display["Punteggio"] = top_30_display["Punteggio"].round(2)
        top_30_display.index = range(1, len(top_30_display) + 1)
        st.dataframe(top_30_display, use_container_width=True)
        
        # Scelta giocatori per lo scambio
        nomi_giocatori = df["Nome"].sort_values().tolist()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔵 Squadra A")
            squadra_a = [st.selectbox(f"A{i+1}", [""] + nomi_giocatori, key=f"A{i}") for i in range(7)]
        
        with col2:
            st.subheader("🔴 Squadra B")
            squadra_b = [st.selectbox(f"B{i+1}", [""] + nomi_giocatori, key=f"B{i}") for i in range(7)]
        
        squadra_a = [g for g in squadra_a if g]
        squadra_b = [g for g in squadra_b if g]
        
        if squadra_a and squadra_b:
            tot_a = df[df["Nome"].isin(squadra_a)]["Punteggio"].sum()
            tot_b = df[df["Nome"].isin(squadra_b)]["Punteggio"].sum()
            diff = abs(tot_a - tot_b)
            media = (tot_a + tot_b) / 2
            perc_diff = (diff / media) * 100 if media != 0 else 0
            
            st.subheader("📊 Risultato dello Scambio")
            st.write(f"**Totale Squadra A**: {tot_a:.2f}")
            st.write(f"**Totale Squadra B**: {tot_b:.2f}")
            st.write(f"**Differenza Percentuale**: {perc_diff:.2f}%")
            
            if perc_diff <= soglia_max:
                st.success("✅ Scambio VALIDO")
            else:
                st.error("❌ Scambio NON valido (fuori soglia)")
                
    except Exception as e:
        st.error(f"Errore durante il caricamento o l'elaborazione: {e}")
