
import pandas as pd
import streamlit as st
from scipy.stats import percentileofscore

st.set_page_config(page_title="Tool Scambi Fantacalcio", layout="wide")

st.title("⚽ Tool Scambi Fantacalcio – Calcolo con Soglia e Multi-scambio")

# Caricamento file
file_quot = st.file_uploader("📥 Carica file Quotazioni", type=["xlsx"])
file_stat = st.file_uploader("📥 Carica file Statistiche", type=["xlsx"])

# Soglia dinamica
soglia_percentuale = st.slider("🎯 Imposta la soglia massima di differenza (%)", 0.0, 50.0, 10.0)

if file_quot and file_stat:
    try:
        # Lettura file
        df_quot = pd.read_excel(file_quot)
        df_stat = pd.read_excel(file_stat)

        # Uniforma nomi delle colonne in minuscolo
        df_quot.columns = df_quot.columns.str.lower().str.strip()
        df_stat.columns = df_stat.columns.str.lower().str.strip()

        # Seleziona colonne rilevanti
        df_quot = df_quot[["nome", "ruolo", "squadra", "qta", "fvm m"]]
        df_stat = df_stat[["nome", "presenze", "mv", "fm", "gol", "assist", "ammonizione", "espulsione", "rigori segnati", "rigori sbagliati", "rigori parati", "porta inviolata"]]

        # Merge su nome (senza distinzione maiuscole/minuscole)
        df = pd.merge(df_quot, df_stat, on="nome", how="inner")

        # Calcolo punteggio personalizzato
        df["punteggio_eventi"] = (
            df["gol"] * 3 +
            df["assist"] * 1 +
            df["ammonizione"] * -0.5 +
            df["espulsione"] * -1 +
            df["rigori segnati"] * 3 +
            df["rigori sbagliati"] * -3 +
            df["rigori parati"] * 3 +
            df["porta inviolata"] * 1
        )

        # Formula finale combinata
        df["punteggio_totale"] = (
            0.4 * df["fm"] +
            0.4 * df["qta"] +
            0.1 * df["fvm m"] +
            0.05 * df["presenze"] +
            0.05 * df["punteggio_eventi"]
        )

        # Calcolo percentile
        df["percentile"] = df["punteggio_totale"].rank(pct=True) * 100

        # Interfaccia di selezione giocatori
        st.subheader("👥 Seleziona i giocatori da scambiare")

        col1, col2 = st.columns(2)
        options = df["nome"].tolist()

        squadra_a = [col1.selectbox(f"A{i+1}", options, key=f"a{i}") for i in range(7)]
        squadra_b = [col2.selectbox(f"B{i+1}", options, key=f"b{i}") for i in range(7)]

        # Rimuovi vuoti
        squadra_a = [p for p in squadra_a if p]
        squadra_b = [p for p in squadra_b if p]

        if squadra_a and squadra_b:
            somma_a = df[df["nome"].isin(squadra_a)]["punteggio_totale"].sum()
            somma_b = df[df["nome"].isin(squadra_b)]["punteggio_totale"].sum()
            diff = abs(somma_a - somma_b)
            media = (somma_a + somma_b) / 2
            percentuale_diff = (diff / media) * 100

            st.markdown("### 📊 Risultato confronto")
            st.write(f"Totale Squadra A: **{somma_a:.2f}**")
            st.write(f"Totale Squadra B: **{somma_b:.2f}**")
            st.write(f"Differenza %: **{percentuale_diff:.2f}%**")
            st.write(f"Soglia impostata: **{soglia_percentuale:.2f}%**")

            if percentuale_diff <= soglia_percentuale:
                st.success("✅ Scambio VALIDO!")
            else:
                st.error("❌ Scambio NON valido")

    except Exception as e:
        st.error(f"Errore: {e}")
