
import streamlit as st
import pandas as pd


st.set_page_config(page_title="Tool Scambi Fantacalcio - Esteso", layout="wide")
st.title("⚽ Tool Scambi Fantacalcio - Excel (Esteso)")

st.subheader("📥 Carica i due file Excel:")
file_quot = st.file_uploader("1️⃣ Carica il file delle Quotazioni", type=["xlsx"])
file_stat = st.file_uploader("2️⃣ Carica il file delle Statistiche", type=["xlsx"])

# Variabili di sessione per il reset
if "reset" not in st.session_state:
    st.session_state.reset = False

if file_quot and file_stat:
    try:
        df_quot = pd.read_excel(file_quot, sheet_name="Tutti", skiprows=1)
        df_stat = pd.read_excel(file_stat, sheet_name="Tutti", skiprows=1)

        df_quot = df_quot.rename(columns={"RM": "Ruolo"})
        df_stat = df_stat.rename(columns={"Rm": "Ruolo"})

        df_quot = df_quot[["Nome", "Ruolo", "Squadra", "Qt.A", "FVM M"]]
        df_stat = df_stat[["Nome", "Ruolo", "Squadra", "Fm", "Gf"]]

        df = pd.merge(df_quot, df_stat, on=["Nome", "Ruolo", "Squadra"], how="inner")

        df["Perc_QtA"] = df.groupby("Ruolo")["Qt.A"].rank(pct=True) * 100
        df["Perc_FVM"] = df.groupby("Ruolo")["FVM M"].rank(pct=True) * 100
        df["Perc_FM"] = df.groupby("Ruolo")["Fm"].rank(pct=True) * 100
        df["Perc_Gol"] = df.groupby("Ruolo")["Gf"].rank(pct=True) * 100
        df["Perc_Ruolo"] = df.groupby("Ruolo")["Fm"].rank(pct=True) * 100

        df["Punteggio"] = (
            0.4 * df["Perc_FM"] +
            0.3 * df["Perc_QtA"] +
            0.2 * df["Perc_FVM"] +
            0.1 * df["Perc_Gol"] +
            0.1 * df["Perc_Ruolo"]
        )

        st.success("✅ Dati combinati correttamente!")

        st.sidebar.subheader("⚙️ Impostazioni")
        soglia = st.sidebar.slider("🎯 Soglia validità (%)", 1, 50, 7, 1) / 100
        filtro_mantra = st.sidebar.multiselect("📌 Filtra per ruolo (Mantra)", options=sorted(df["Ruolo"].unique()), default=sorted(df["Ruolo"].unique()))

        df_filtrato = df[df["Ruolo"].isin(filtro_mantra)].copy()
        giocatori = df_filtrato["Nome"].tolist()

        st.subheader("🏆 Top 20 giocatori per punteggio")
        st.dataframe(df_filtrato.sort_values("Punteggio", ascending=False)[["Nome", "Ruolo", "Squadra", "Punteggio"]].head(20), use_container_width=True)

        # Pulsante Reset
        if st.button("🔁 Reset giocatori"):
            for i in range(7):
                st.session_state[f"a_{i}"] = ""
                st.session_state[f"b_{i}"] = ""
            st.session_state.reset = True
            st.experimental_rerun()

        col1, col2 = st.columns(2)
        squadra_a = []
        squadra_b = []
        labels_a = []
        labels_b = []

        with col1:
            st.subheader("🟦 Squadra A")
            for i in range(7):
                nome = st.selectbox(f"A{i+1}", [""] + giocatori, key=f"a_{i}")
                if nome:
                    punteggio = df_filtrato[df_filtrato["Nome"] == nome]["Punteggio"].values[0]
                    squadra_a.append(punteggio)
                    labels_a.append(nome)

        with col2:
            st.subheader("🟥 Squadra B")
            for i in range(7):
                nome = st.selectbox(f"B{i+1}", [""] + giocatori, key=f"b_{i}")
                if nome:
                    punteggio = df_filtrato[df_filtrato["Nome"] == nome]["Punteggio"].values[0]
                    squadra_b.append(punteggio)
                    labels_b.append(nome)

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

            if diff <= soglia:
                st.success("✅ Scambio VALIDO!")
            else:
                st.error("❌ Scambio NON valido!")

    except Exception as e:
        st.error(f"Errore durante la lettura o unione dei file: {e}")
else:
    st.warning("⬆️ Carica entrambi i file per iniziare.")
