
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tool Scambi Fantacalcio - Excel", layout="wide")
st.title("⚽ Tool Scambi Fantacalcio - Carica Quotazioni e Statistiche Excel")

st.subheader("📥 Carica i due file Excel:")
file_quot = st.file_uploader("1️⃣ Carica il file delle Quotazioni", type=["xlsx"])
file_stat = st.file_uploader("2️⃣ Carica il file delle Statistiche", type=["xlsx"])

if file_quot and file_stat:
    try:
        df_quot = pd.read_excel(file_quot, sheet_name="Tutti")
        df_stat = pd.read_excel(file_stat, sheet_name="Tutti")

        # Pulisci colonne
        df_quot.columns = df_quot.columns.str.strip()
        df_stat.columns = df_stat.columns.str.strip()

        # Seleziona solo le colonne necessarie
        df_quot = df_quot[["Nome", "Ruolo", "Squadra", "Qt.A", "FVM M"]]
        df_stat = df_stat[["Nome", "Ruolo", "Squadra", "FM", "Gol"]]

        # Merge
        df = pd.merge(df_quot, df_stat, on=["Nome", "Ruolo", "Squadra"], how="inner")

        # Calcolo dei percentili per ruolo
        df["Perc_QtA"] = df.groupby("Ruolo")["Qt.A"].rank(pct=True) * 100
        df["Perc_FVM"] = df.groupby("Ruolo")["FVM M"].rank(pct=True) * 100
        df["Perc_FM"] = df.groupby("Ruolo")["FM"].rank(pct=True) * 100
        df["Perc_Gol"] = df.groupby("Ruolo")["Gol"].rank(pct=True) * 100
        df["Perc_Ruolo"] = df.groupby("Ruolo")["FM"].rank(pct=True) * 100

        # Punteggio finale combinato
        df["Punteggio"] = (
            0.4 * df["Perc_FM"] +
            0.3 * df["Perc_QtA"] +
            0.2 * df["Perc_FVM"] +
            0.1 * df["Perc_Gol"] +
            0.1 * df["Perc_Ruolo"]
        )

        st.success("✅ Dati combinati con successo!")

        giocatori = df["Nome"].tolist()
        col1, col2 = st.columns(2)
        squadra_a = []
        squadra_b = []

        with col1:
            st.subheader("🟦 Squadra A")
            for i in range(7):
                nome = st.selectbox(f"A{i+1}", [""] + giocatori, key=f"a_{i}")
                if nome:
                    punteggio = df[df["Nome"] == nome]["Punteggio"].values[0]
                    squadra_a.append(punteggio)

        with col2:
            st.subheader("🟥 Squadra B")
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

            soglia = 0.07
            if diff <= soglia:
                st.success("✅ Scambio VALIDO!")
            else:
                st.error("❌ Scambio NON valido!")

    except Exception as e:
        st.error(f"Errore durante la lettura o unione dei file: {e}")
else:
    st.warning("⬆️ Carica entrambi i file per iniziare.")
