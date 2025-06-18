
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Tool Scambi Fantacalcio - Debug", layout="wide")
st.title("⚽ Tool Scambi Fantacalcio - Dati da Fantacalcio.it (con debug)")

@st.cache_data
def scarica_dati():
    url_quot = "https://www.fantacalcio.it/quotazioni-fantacalcio"
    resp = requests.get(url_quot, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.content, "html.parser")
    rows = soup.select("table.quotazioni tbody tr")
    quot_data = []
    for r in rows:
        cols = r.find_all("td")
        if len(cols) >= 6:
            try:
                nome = cols[1].text.strip()
                ruolo = cols[0].text.strip()
                squadra = cols[2].text.strip()
                qta = float(cols[3].text.strip().replace(",", "."))
                fvm = float(cols[5].text.strip().replace(",", "."))
                quot_data.append((nome, ruolo, squadra, qta, fvm))
            except:
                continue
    df_quot = pd.DataFrame(quot_data, columns=["Nome", "Ruolo", "Squadra", "Qt.A", "FVM M"])

    url_stat = "https://www.fantacalcio.it/statistiche-serie-a"
    resp2 = requests.get(url_stat, headers={"User-Agent": "Mozilla/5.0"})
    soup2 = BeautifulSoup(resp2.content, "html.parser")
    rows2 = soup2.select("table.statistiche tbody tr")
    stat_data = []
    for r in rows2:
        cols = r.find_all("td")
        if len(cols) >= 11:
            try:
                nome = cols[1].text.strip()
                ruolo = cols[0].text.strip()
                squadra = cols[2].text.strip()
                fm = float(cols[7].text.strip().replace(",", "."))
                gol = int(cols[4].text.strip())
                stat_data.append((nome, ruolo, squadra, fm, gol))
            except:
                continue
    df_stats = pd.DataFrame(stat_data, columns=["Nome", "Ruolo", "Squadra", "FM", "Gol"])

    df = pd.merge(df_quot, df_stats, on=["Nome", "Ruolo", "Squadra"], how="inner")
    df["Perc_FM"] = df.groupby("Ruolo")["FM"].rank(pct=True) * 100
    df["Perc_QtA"] = df.groupby("Ruolo")["Qt.A"].rank(pct=True) * 100
    df["Perc_FVM"] = df.groupby("Ruolo")["FVM M"].rank(pct=True) * 100
    df["Perc_Gol"] = df.groupby("Ruolo")["Gol"].rank(pct=True) * 100
    df["Perc_Ruolo"] = df.groupby("Ruolo")["FM"].rank(pct=True) * 100
    df["Punteggio"] = (
        0.4 * df["Perc_FM"] +
        0.3 * df["Perc_QtA"] +
        0.2 * df["Perc_FVM"] +
        0.1 * df["Perc_Gol"] +
        0.1 * df["Perc_Ruolo"]
    )
    return df

if "df" not in st.session_state:
    st.session_state.df = None

if st.button("🔄 Scarica dati aggiornati da Fantacalcio.it"):
    st.session_state.df = scarica_dati()
    st.success("✅ Dati aggiornati con successo!")

if st.session_state.df is not None:
    df = st.session_state.df

    st.subheader("🔍 Debug: anteprima dati scaricati")
    st.write(df.head())
    st.write("Numero giocatori disponibili:", len(df))

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

        soglia = 0.07
        if diff <= soglia:
            st.success("✅ Scambio VALIDO!")
        else:
            st.error("❌ Scambio NON valido!")
else:
    st.info("⬆️ Premi il pulsante per scaricare le quotazioni + statistiche aggiornate.")
