
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tool Scambi Fantacalcio", layout="wide")

st.title("⚽ Tool Scambi Fantacalcio 2024/25")

# Upload del file delle quotazioni
uploaded_file = st.file_uploader("📂 Carica il file Excel con il foglio 'Tutti'", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Tutti", header=1)
        df = df[["Nome", "Qt.A", "FVM M"]].dropna()
        df["Qt.A"] = pd.to_numeric(df["Qt.A"], errors="coerce")
        df["FVM M"] = pd.to_numeric(df["FVM M"], errors="coerce")
        df = df.dropna()

        # Calcolo dei percentili
        df["Perc Qt.A"] = df["Qt.A"].rank(pct=True) * 100
        df["Perc FVM"] = df["FVM M"].rank(pct=True) * 100
        df["Punteggio"] = 0.7 * df["Perc Qt.A"] + 0.3 * df["Perc FVM"]

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

            soglia = st.slider("🎯 Soglia massima (%)", 0.0, 50.0, 10.0, step=0.5) / 100

            if diff <= soglia:
                st.success("✅ Scambio VALIDO!")
            else:
                st.error("❌ Scambio NON valido!")

    except Exception as e:
        st.error(f"Errore nella lettura del file: {e}")
else:
    st.info("🔄 Carica il file Excel settimanale per iniziare.")
