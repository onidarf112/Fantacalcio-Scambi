import streamlit as st
import pandas as pd
from scipy.stats import percentileofscore, zscore

st.set_page_config(page_title="Tool Scambi Fantacalcio - Multiscambio", layout="wide")
st.title("🌟 Tool Scambi Fantacalcio - Modalità Multi Scambio (1 vs 1 fino a 7 vs 7)")

st.markdown("""
Carica i file Excel con le **quotazioni** e le **statistiche** aggiornate.
""")

file_quot = st.file_uploader("🗂️ Carica file quotazioni", type=[".xlsx"])
file_stat = st.file_uploader("📂 Carica file statistiche", type=[".xlsx"])

soglia = st.slider("🔹 Soglia di validità (%)", min_value=0.0, max_value=50.0, value=10.0, step=0.5)

if file_quot and file_stat:
    try:
        df_quot = pd.read_excel(file_quot, header=1)
        df_stat = pd.read_excel(file_stat, header=1)

        # Normalizza nomi colonne
        df_quot.columns = df_quot.columns.str.strip().str.upper()
        df_stat.columns = df_stat.columns.str.strip().str.upper()

        # Merge su NOME
        df = pd.merge(df_quot, df_stat, on="NOME", how="inner")

        # Conversione colonne numeriche
        for col in ["QTA", "FVM M", "FM", "GOL", "ASSIST", "AMMONIZIONI", "ESPULSIONI", "RIGORI SEGNATI", "RIGORI SBAGLIATI", "PORTA INVIOLATA", "RIGORI PARATI", "PRESENZE"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Calcolo z-score per bonus
        df["BONUS_Z"] = (
            5 * zscore(df["GOL"].fillna(0)) +
            2 * zscore(df["ASSIST"].fillna(0)) +
            -1 * zscore(df["AMMONIZIONI"].fillna(0)) +
            -2 * zscore(df["ESPULSIONI"].fillna(0)) +
            4 * zscore(df["RIGORI SEGNATI"].fillna(0)) +
            1 * zscore(df["RIGORI PARATI"].fillna(0))
        )

        # Calcolo punteggio per ruolo
        def calcola_punteggio(row):
            ruolo = row["RUOLO"].upper()
            perc_fvm = row["FVM M"] / df["FVM M"].max()
            perc_fm = row["FM"] / df["FM"].max()
            perc_qta = row["QTA"] / df["QTA"].max()
            perc_pres = row["PRESENZE"] / df["PRESENZE"].max()
            bonus = row["BONUS_Z"]

            if ruolo == "P":
                return 0.6 * perc_pres + 0.3 * bonus + 0.1 * perc_fvm
            elif ruolo in ["D", "DD", "DS"]:
                return 0.3 * perc_fvm + 0.25 * perc_fm + 0.2 * perc_pres + 0.25 * bonus
            elif ruolo in ["C", "CC", "CD", "CS"]:
                return 0.25 * perc_fvm + 0.25 * perc_fm + 0.25 * perc_pres + 0.25 * bonus
            else:
                return 0.2 * perc_fvm + 0.3 * perc_fm + 0.4 * (row["GOL"] / df["GOL"].max()) + 0.1 * perc_pres

        df["PUNTEGGIO"] = df.apply(calcola_punteggio, axis=1) * 150

        # Giocatori disponibili
        giocatori = df["NOME"].sort_values().unique()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔹 Squadra A")
            squadra_a = [st.selectbox(f"A{i+1}", giocatori, key=f"a{i}", index=0) for i in range(7)]

        with col2:
            st.subheader("🔹 Squadra B")
            squadra_b = [st.selectbox(f"B{i+1}", giocatori, key=f"b{i}", index=0) for i in range(7)]

        # Filtra non vuoti
        giocatori_a = [g for g in squadra_a if g]
        giocatori_b = [g for g in squadra_b if g]

        if giocatori_a and giocatori_b:
            punteggio_a = df[df["NOME"].isin(giocatori_a)]["PUNTEGGIO"].sum()
            punteggio_b = df[df["NOME"].isin(giocatori_b)]["PUNTEGGIO"].sum()

            differenza = abs(punteggio_a - punteggio_b)
            diff_perc = (differenza / max(punteggio_a, punteggio_b)) * 100

            st.markdown("""
            ### 🎓 Risultato Confronto
            """)
            col3, col4, col5 = st.columns(3)
            col3.metric("Totale Squadra A", f"{punteggio_a:.2f}")
            col4.metric("Totale Squadra B", f"{punteggio_b:.2f}")
            col5.metric("Differenza %", f"{diff_perc:.2f}%")

            if diff_perc <= soglia:
                st.success("✅ Scambio VALIDO!")
            else:
                st.error("❌ Scambio NON valido")

        # 🔝 Visualizza top 20 per punteggio
        st.subheader("🏅 Top 20 Giocatori per Punteggio Totale")
        top_20 = df.sort_values(by="PUNTEGGIO", ascending=False).head(20)
        st.dataframe(top_20[["NOME", "SQUADRA", "RUOLO", "PUNTEGGIO"]].reset_index(drop=True), use_container_width=True)

    except Exception as e:
        st.error(f"Errore nel caricamento o calcolo: {e}")
else:
    st.warning("🔹 Carica entrambi i file per procedere.")
