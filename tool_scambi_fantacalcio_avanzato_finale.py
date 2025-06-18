
import streamlit as st
import pandas as pd
from scipy.stats import percentileofscore

st.set_page_config(page_title="Tool Scambi Fantacalcio", layout="wide")

st.title("⚽ Tool Scambi Fantacalcio - Avanzato")
st.markdown("Carica i file **Quotazioni** e **Statistiche** ufficiali di fantacalcio.it")

# Caricamento file
quot_file = st.file_uploader("📈 Carica file quotazioni", type=["xlsx"])
stat_file = st.file_uploader("📊 Carica file statistiche", type=["xlsx"])

if quot_file and stat_file:
    try:
        # Lettura file Excel con header alla riga 1 (indice 1)
        df_quot = pd.read_excel(quot_file, sheet_name="Tutti", header=1)
        df_stat = pd.read_excel(stat_file, sheet_name="Tutti", header=1)

        # Merge sui nomi
        df = pd.merge(df_quot, df_stat, on=["Nome", "Squadra"], how="inner")

        # Conversione numerica
        for col in ["Qt.A", "FVM M", "Fm", "Ass", "Amm", "Esp", "R+", "R-", "Pv", "Gol"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Calcolo punteggio bonus/malus
        df["Bonus"] = (
            df["Gol"] * 3 +
            df["Ass"] * 1 +
            df["R+"] * 3 +
            df["R-"] * -3 +
            df["Amm"] * -0.5 +
            df["Esp"] * -1
        )

        # Formula finale: percentili combinati + bonus su scala 150
        df["Score_Raw"] = (
            df["Qt.A"].rank(pct=True) * 0.4 +
            df["FVM M"].rank(pct=True) * 0.4 +
            df["Bonus"].rank(pct=True) * 0.1 +
            df["Pv"].rank(pct=True) * 0.1
        )

        df["Punteggio"] = (df["Score_Raw"] * 150).round(4)

        # Ordinamento per punteggio
        df = df.sort_values("Punteggio", ascending=False)

        # INTERFACCIA SCAMBI
        st.divider()
        st.header("🤝 Confronta uno scambio")

        players = df["Nome"].tolist()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Squadra A")
            team_a = [st.selectbox(f"A{i+1}", [""] + players, key=f"A{i}") for i in range(7)]
        with col2:
            st.subheader("Squadra B")
            team_b = [st.selectbox(f"B{i+1}", [""] + players, key=f"B{i}") for i in range(7)]

        # Soglia dinamica
        soglia = st.slider("🎯 Soglia di validità (%)", 0.0, 20.0, 10.0, 0.5)

        # Calcolo totale e differenza
        def calcola_totale(lista):
            return df[df["Nome"].isin([n for n in lista if n])]["Punteggio"].sum()

        tot_a = calcola_totale(team_a)
        tot_b = calcola_totale(team_b)

        diff = abs(tot_a - tot_b)
        perc = diff / max(tot_a, tot_b) if max(tot_a, tot_b) > 0 else 0

        st.markdown("### 📊 Risultato confronto")
        col1, col2, col3 = st.columns(3)
        col1.metric("Totale Squadra A", f"{tot_a:.2f}")
        col2.metric("Totale Squadra B", f"{tot_b:.2f}")
        col3.metric("Differenza %", f"{perc*100:.2f}%")

        if perc <= soglia / 100:
            st.success("✅ Scambio VALIDO!")
        else:
            st.error("❌ Scambio NON valido!")

    except Exception as e:
        st.error(f"Errore nel caricamento dei dati: {e}")
else:
    st.info("📂 Carica entrambi i file per iniziare.")
