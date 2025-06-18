
import streamlit as st
import pandas as pd
import numpy as np

def calcola_punteggio_eventi(row):
    return (
        row.get("Gol", 0) * 3 +
        row.get("Assist", 0) * 1 +
        row.get("Ammonizioni", 0) * -0.5 +
        row.get("Espulsioni", 0) * -1 +
        row.get("Rigori Segnati", 0) * 3 +
        row.get("Rigori Sbagliati", 0) * -3 +
        row.get("Porta Inviolata", 0) * 1 +
        row.get("Rigori Parati", 0) * 3
    )

def zscore(series):
    mean = series.mean()
    std = series.std()
    return (series - mean) / std if std != 0 else series * 0

def calcola_punteggi_finali(df_quotazioni, df_statistiche):
    df = pd.merge(df_quotazioni, df_statistiche, on="Nome", how="inner")
    df["Punteggio_Eventi"] = df.apply(calcola_punteggio_eventi, axis=1)
    df["Z_FM"] = zscore(df["FM"])
    df["Z_QtA"] = zscore(df["QtA"])
    df["Z_FVM"] = zscore(df["FVM M"])
    df["Z_Eventi"] = zscore(df["Punteggio_Eventi"])
    df["Z_Presenze"] = zscore(df["Presenze"])
    df["Punteggio"] = (
        0.35 * df["Z_FM"] +
        0.20 * df["Z_QtA"] +
        0.20 * df["Z_FVM"] +
        0.15 * df["Z_Eventi"] +
        0.10 * df["Z_Presenze"]
    ) * 30 + 75
    return df

st.title("⚽ Tool Scambi Fantacalcio - Nuovo Sistema")

quot_file = st.file_uploader("Carica file Quotazioni", type="xlsx")
stat_file = st.file_uploader("Carica file Statistiche", type="xlsx")

if quot_file and stat_file:
    df_quot = pd.read_excel(quot_file, sheet_name="Tutti", skiprows=1)
    df_stat = pd.read_excel(stat_file, sheet_name="Tutti", skiprows=1)

    df_quot = df_quot.rename(columns={"RM": "Ruolo"})
    df_stat = df_stat.rename(columns={"Rm": "Ruolo"})

    df_quot = df_quot[["Nome", "Ruolo", "Squadra", "QtA", "FVM M"]]
    df_stat = df_stat[["Nome", "Ruolo", "Squadra", "FM", "Gol", "Assist", "Ammonizioni", "Espulsioni", "Rigori Segnati", "Rigori Sbagliati", "Porta Inviolata", "Rigori Parati", "Presenze"]]

    df_finale = calcola_punteggi_finali(df_quot, df_stat)

    st.subheader("🎯 Imposta la soglia massima di differenza (%)")
    soglia = st.slider("Soglia di validità dello scambio", 1, 50, 7)

    giocatori = df_finale["Nome"].tolist()
    col1, col2 = st.columns(2)

    squadra_a = []
    squadra_b = []

    with col1:
        st.subheader("🟦 Squadra A")
        for i in range(3):
            nome = st.selectbox(f"A{i+1}", [""] + giocatori, key=f"a_{i}")
            if nome:
                valore = df_finale[df_finale["Nome"] == nome]["Punteggio"].values[0]
                squadra_a.append(valore)

    with col2:
        st.subheader("🟥 Squadra B")
        for i in range(3):
            nome = st.selectbox(f"B{i+1}", [""] + giocatori, key=f"b_{i}")
            if nome:
                valore = df_finale[df_finale["Nome"] == nome]["Punteggio"].values[0]
                squadra_b.append(valore)

    if squadra_a and squadra_b:
        somma_a = sum(squadra_a)
        somma_b = sum(squadra_b)
        diff = abs(somma_a - somma_b) / max(somma_a, somma_b) * 100

        st.markdown("---")
        st.metric("Totale Squadra A", f"{somma_a:.2f}")
        st.metric("Totale Squadra B", f"{somma_b:.2f}")
        st.metric("Differenza %", f"{diff:.2f}%")

        if diff <= soglia:
            st.success("✅ Scambio VALIDO!")
        else:
            st.error("❌ Scambio NON valido!")
