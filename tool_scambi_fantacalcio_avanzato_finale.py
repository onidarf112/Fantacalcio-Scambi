import streamlit as st
import pandas as pd
from scipy.stats import percentileofscore

st.set_page_config(page_title="Tool Scambi Fantacalcio", layout="wide")

st.title("⚽ Tool Scambi Fantacalcio - Multi Scambio + Formula Avanzata")

st.markdown("### 📂 Carica i file")
file_quot = st.file_uploader("Carica il file delle **quotazioni** (.xlsx)", type="xlsx")
file_stat = st.file_uploader("Carica il file delle **statistiche** (.xlsx)", type="xlsx")

soglia_max = st.slider("🎯 Soglia massima di scostamento (%)", 0.0, 50.0, 10.0, 0.1)

if file_quot and file_stat:
    try:
        # Leggi con header sulla riga 2 (indice 1)
        df_quot = pd.read_excel(file_quot, header=1)
        df_stat = pd.read_excel(file_stat, header=1)

        # Merge sui nomi
        df = pd.merge(df_quot, df_stat, on="Nome", how="inner")

        colonne = ["Nome", "RM", "Squadra", "QtA", "FVM M", "Presenze", "Gol", "Assist", "Ammonizioni", "Espulsioni", "Rigori Segnati", "Rigori Sbagliati", "Porta Inviolata", "Rigori Parati"]
        for col in colonne:
            if col not in df.columns:
                st.error(f"❌ Colonna mancante: '{col}'")
                st.stop()

        df["Perc_FVM"] = df["FVM M"].rank(pct=True) * 100
        df["Perc_QtA"] = df["QtA"].rank(pct=True) * 100

        df["Punteggio"] = (
            df["QtA"] * 0.3 +
            df["FVM M"] * 0.4 +
            df["Presenze"] * 0.05 +
            df["Gol"] * 3 +
            df["Assist"] * 1 +
            df["Ammonizioni"] * -0.5 +
            df["Espulsioni"] * -1 +
            df["Rigori Segnati"] * 3 +
            df["Rigori Sbagliati"] * -3 +
            df["Porta Inviolata"] * 1 +
            df["Rigori Parati"] * 3
        )

        giocatori = df["Nome"].tolist()
        colA, colB = st.columns(2)
        with colA:
            st.subheader("🔵 Squadra A")
            squadra_a = [st.selectbox(f"A{i+1}", [""] + giocatori, key=f"A{i}") for i in range(7)]
        with colB:
            st.subheader("🔴 Squadra B")
            squadra_b = [st.selectbox(f"B{i+1}", [""] + giocatori, key=f"B{i}") for i in range(7)]

        squadra_a = [g for g in squadra_a if g]
        squadra_b = [g for g in squadra_b if g]

        if squadra_a and squadra_b:
            tot_a = df[df["Nome"].isin(squadra_a)]["Punteggio"].sum()
            tot_b = df[df["Nome"].isin(squadra_b)]["Punteggio"].sum()
            diff = abs(tot_a - tot_b)
            media = (tot_a + tot_b) / 2
            perc_diff = (diff / media) * 100 if media != 0 else 0

            st.markdown("### 📊 Risultato confronto")
            st.write(f"**Totale Squadra A**: {tot_a:.2f}")
            st.write(f"**Totale Squadra B**: {tot_b:.2f}")
            st.write(f"**Differenza %**: {perc_diff:.2f}%")
            if perc_diff <= soglia_max:
                st.success("✅ Scambio VALIDO!")
            else:
                st.error("❌ Scambio NON valido (fuori soglia)")

    except Exception as e:
        st.error(f"Errore nel caricamento o calcolo: {e}")
