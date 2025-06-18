
# tool_scambi_fantacalcio_avanzato.py
import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import percentileofscore

st.set_page_config(page_title="Tool Scambi Fantacalcio Avanzato", layout="wide")
st.title("⚽ Tool Scambi Fantacalcio - Formula Avanzata con Statistiche")

file_quot = st.file_uploader("📁 Carica file delle Quotazioni", type="xlsx", key="quot")
file_stat = st.file_uploader("📁 Carica file delle Statistiche", type="xlsx", key="stat")

if file_quot and file_stat:
    try:
        df_quot = pd.read_excel(file_quot)
        df_stat = pd.read_excel(file_stat)

        df_quot = df_quot.rename(columns=str.strip)
        df_stat = df_stat.rename(columns=str.strip)

        df_quot = df_quot[["Nome", "Ruolo", "Squadra", "QtA", "FVM M"]]
        df_stat = df_stat[["Nome", "FM", "Gol", "Assist", "Amm", "Esp", "Rigori Segnati", "Rigori Sbagliati", "Porta Inviolata", "Rigori Parati", "Presenze"]]

        df = pd.merge(df_quot, df_stat, on="Nome", how="inner")

        def calc_bonus(row):
            return (
                row["Gol"] * 3 +
                row["Assist"] * 1 -
                row["Amm"] * 0.5 -
                row["Esp"] * 1 +
                row["Rigori Segnati"] * 3 -
                row["Rigori Sbagliati"] * 3 +
                row["Porta Inviolata"] * 1 +
                row["Rigori Parati"] * 3
            )

        df["Bonus"] = df.apply(calc_bonus, axis=1)

        df["Perc_QtA"] = df["QtA"].rank(pct=True)
        df["Perc_FVM"] = df["FVM M"].rank(pct=True)
        df["Perc_FM"] = df["FM"].rank(pct=True)
        df["Perc_Pres"] = df["Presenze"].rank(pct=True)

        df["Punteggio"] = (
            0.3 * df["Perc_QtA"] +
            0.3 * df["Perc_FVM"] +
            0.3 * df["Perc_FM"] +
            0.1 * df["Perc_Pres"]
        ) * 150 + df["Bonus"]

        st.success("✅ File caricati e uniti con successo!")

        soglia_diff = st.slider("🔧 Soglia di differenza massima (%)", 0.0, 0.5, 0.1, step=0.01)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔵 Squadra A")
            squadra_a = [st.selectbox(f"A{i+1}", df["Nome"].unique().tolist() + [""], key=f"a{i}") for i in range(7)]
        with col2:
            st.subheader("🔴 Squadra B")
            squadra_b = [st.selectbox(f"B{i+1}", df["Nome"].unique().tolist() + [""], key=f"b{i}") for i in range(7)]

        if st.button("🔄 Reset Giocatori"):
            st.experimental_rerun()

        def calcola_totale(lista):
            return df[df["Nome"].isin([x for x in lista if x])]["Punteggio"].sum()

        total_a = calcola_totale(squadra_a)
        total_b = calcola_totale(squadra_b)
        diff = abs(total_a - total_b) / max(total_a, total_b) if max(total_a, total_b) > 0 else 0

        st.markdown("## 📊 Risultato confronto")
        col3, col4, col5 = st.columns(3)
        col3.metric("Totale Squadra A", f"{total_a:.2f}")
        col4.metric("Totale Squadra B", f"{total_b:.2f}")
        col5.metric("Differenza %", f"{diff*100:.2f}%")

        if diff <= soglia_diff:
            st.success("✅ Scambio VALIDO!")
        else:
            st.error("❌ Scambio NON valido")

    except Exception as e:
        st.error(f"Errore durante la lettura o unione dei file: {e}")
else:
    st.info("📥 Carica entrambi i file per iniziare.")
