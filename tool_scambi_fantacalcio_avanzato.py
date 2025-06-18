import streamlit as st
import pandas as pd
from scipy.stats import percentileofscore

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
import streamlit as st
import pandas as pd
from scipy.stats import percentileofscore

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
        df_quot = pd.read_excel(file_quot)
        df_stat = pd.read_excel(file_stat)

        # Normalizza nomi colonne
        df_quot.columns = df_quot.columns.str.strip().str.upper()
        df_stat.columns = df_stat.columns.str.strip().str.upper()

        # Merge su NOME
        df = pd.merge(df_quot, df_stat, on="NOME", how="inner")

        # Conversione colonne numeriche
        for col in ["QTA", "FVM M", "FM", "GOL", "ASSIST", "AMMONIZIONI", "ESPULSIONI", "RIGORI SEGNATI", "RIGORI SBAGLIATI", "PORTA INVIOLATA", "RIGORI PARATI", "PRESENZE"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Calcolo punteggio personalizzato
        df["PUNTEGGIO_BASE"] = (
            0.4 * df["FM"] +
            0.4 * df["QTA"] +
            0.2 * df["FVM M"]
        )
        df["BONUS_MALUS"] = (
            df["GOL"] * 3 + df["ASSIST"] * 1 - df["AMMONIZIONI"] * 0.5 -
            df["ESPULSIONI"] * 1 + df["RIGORI SEGNATI"] * 3 -
            df["RIGORI SBAGLIATI"] * 3 + df["PORTA INVIOLATA"] * 1 + df["RIGORI PARATI"] * 3
        )
        df["PRESENZA_WEIGHT"] = df["PRESENZE"] / df["PRESENZE"].max()

        df["PUNTEGGIO"] = (df["PUNTEGGIO_BASE"] + df["BONUS_MALUS"]) * df["PRESENZA_WEIGHT"]

        # Percentili
        df["PERC_PUNT"] = df["PUNTEGGIO"].apply(lambda x: percentileofscore(df["PUNTEGGIO"], x))

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
        st.dataframe(top_20[["Nome", "SQUADRA", "RUOLO", "PUNTEGGIO"]].reset_index(drop=True), use_container_width=True)

    except Exception as e:
        st.error(f"Errore nel caricamento o calcolo: {e}")
else:
    st.warning("🔹 Carica entrambi i file per procedere.")


        # Normalizza nomi colonne
        df_quot.columns = df_quot.columns.str.strip().str.upper()
        df_stat.columns = df_stat.columns.str.strip().str.upper()

        # Merge su NOME
        df = pd.merge(df_quot, df_stat, on="NOME", how="inner")

        # Conversione colonne numeriche
        for col in ["QTA", "FVM M", "FM", "GOL", "ASSIST", "AMMONIZIONI", "ESPULSIONI", "RIGORI SEGNATI", "RIGORI SBAGLIATI", "PORTA INVIOLATA", "RIGORI PARATI", "PRESENZE"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Calcolo punteggio personalizzato
        df["PUNTEGGIO_BASE"] = (
            0.4 * df["FM"] +
            0.4 * df["QTA"] +
            0.2 * df["FVM M"]
        )
        df["BONUS_MALUS"] = (
            df["GOL"] * 3 + df["ASSIST"] * 1 - df["AMMONIZIONI"] * 0.5 -
            df["ESPULSIONI"] * 1 + df["RIGORI SEGNATI"] * 3 -
            df["RIGORI SBAGLIATI"] * 3 + df["PORTA INVIOLATA"] * 1 + df["RIGORI PARATI"] * 3
        )
        df["PRESENZA_WEIGHT"] = df["PRESENZE"] / df["PRESENZE"].max()

        df["PUNTEGGIO"] = (df["PUNTEGGIO_BASE"] + df["BONUS_MALUS"]) * df["PRESENZA_WEIGHT"]

        # Percentili
        df["PERC_PUNT"] = df["PUNTEGGIO"].apply(lambda x: percentileofscore(df["PUNTEGGIO"], x))

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
        st.dataframe(top_20[["Nome", "SQUADRA", "RUOLO", "PUNTEGGIO"]].reset_index(drop=True), use_container_width=True)

    except Exception as e:
        st.error(f"Errore nel caricamento o calcolo: {e}")
else:
    st.warning("🔹 Carica entrambi i file per procedere.")

