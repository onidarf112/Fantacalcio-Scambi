
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Tool Scambi Fantacalcio 2024/25", layout="wide")
st.title("⚽ Tool Scambi Fantacalcio - Versione con Formula Avanzata")

uploaded_file = st.file_uploader("📂 Carica il file Excel combinato (quotazioni + statistiche)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df = df[["Nome", "Ruolo", "Squadra", "Qt.A", "FVM M", "FM", "Gol"]].dropna()

        # Convertiamo in numerico
        df["Qt.A"] = pd.to_numeric(df["Qt.A"], errors="coerce")
        df["FVM M"] = pd.to_numeric(df["FVM M"], errors="coerce")
        df["FM"] = pd.to_numeric(df["FM"], errors="coerce")
        df["Gol"] = pd.to_numeric(df["Gol"], errors="coerce")
        df = df.dropna()

        # Percentili per ruolo
        df["Perc_FM"] = df.groupby("Ruolo")["FM"].rank(pct=True) * 100
        df["Perc_QtA"] = df.groupby("Ruolo")["Qt.A"].rank(pct=True) * 100
        df["Perc_FVM"] = df.groupby("Ruolo")["FVM M"].rank(pct=True) * 100
        df["Perc_Gol"] = df.groupby("Ruolo")["Gol"].rank(pct=True) * 100

        # Bonus percentilico per ruolo (punteggio complessivo percentile nel ruolo)
        df["Perc_Ruolo"] = df.groupby("Ruolo")["FM"].rank(pct=True) * 100

        # Calcolo punteggio finale (formula avanzata)
        df["Punteggio"] = (
            0.4 * df["Perc_FM"] +
            0.3 * df["Perc_QtA"] +
            0.2 * df["Perc_FVM"] +
            0.1 * df["Perc_Gol"] +
            0.1 * df["Perc_Ruolo"]
        )

        st.success("✅ File caricato correttamente!")

        giocatori = df["Nome"].tolist()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🟦 Squadra A")
            squadra_a = []
            for i in range(7):
                nome = st.selectbox(f"A{i+1}", [""] + giocatori, key=f"a_{i}")
                if nome:
                    punteggio = df[df["Nome"] == nome]["Punteggio"].values[0]
                    squadra_a.append(punteggio)

        with col2:
            st.subheader("🟥 Squadra B")
            squadra_b = []
            for i in range(7):
                nome = st.selectbox(f"B{i+1}", [""] + giocatori, key=f"b_{i}")
                if nome:
                    punteggio = df[df["Nome"] == nome]["Punteggio"].values[0]
                    squadra_b.append(punteggio)

        if squadra_a and squadra_b:
            total_a = sum(squadra_a)
            total_b = sum(squadra_b)
            diff = abs(total_a - total_b) / max(total_a, total_b)

            st.markdown("---")
            st.subheader("📊 Risultato confronto")

            col3, col4, col5 = st.columns(3)
            col3.metric("Totale Squadra A", f"{total_a:.2f}")
            col4.metric("Totale Squadra B", f"{total_b:.2f}")
            col5.metric("Differenza %", f"{diff*100:.2f}%")

            soglia = 0.07  # 7% di soglia

            if diff <= soglia:
                st.success("✅ Scambio VALIDO!")
            else:
                st.error("❌ Scambio NON valido!")

    except Exception as e:
        st.error(f"Errore nella lettura del file: {e}")
else:
    st.info("🔄 Carica il file Excel con le quotazioni e statistiche unite per iniziare.")
