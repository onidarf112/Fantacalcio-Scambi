import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import percentileofscore
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Fantacalcio - Scambi Avanzati ", layout="wide")
st.title("⚽ Fantacalcio - Tool Scambi Avanzati by Onidarf")

# Sidebar per configurazioni
st.sidebar.header("⚙️ Configurazioni")
soglia_max = st.sidebar.slider("🎯 Soglia Massima (%) Differenza", 0.0, 50.0, 10.0, step=0.5)

# Pesi personalizzabili
st.sidebar.subheader("📊 Pesi Formula Punteggio")
peso_fvm = st.sidebar.slider("Peso FVM M", 0.0, 1.0, 0.30, step=0.05)
peso_fm = st.sidebar.slider("Peso Fm", 0.0, 1.0, 0.25, step=0.05)
peso_qta = st.sidebar.slider("Peso Qt.A", 0.0, 1.0, 0.20, step=0.05)
peso_pres = st.sidebar.slider("Peso Presenze", 0.0, 1.0, 0.15, step=0.05)
peso_bonus = st.sidebar.slider("Peso Bonus/Malus", 0.0, 1.0, 0.10, step=0.05)

# Configurazione scale per ruolo
st.sidebar.subheader("⚖️ Scale Punteggio per Ruolo")
scala_por = st.sidebar.slider("Scala Portieri", 80, 150, 120, step=5)
scala_dif = st.sidebar.slider("Scala Difensori", 100, 170, 140, step=5)
scala_cen = st.sidebar.slider("Scala Centrocampisti", 120, 190, 160, step=5)
scala_att = st.sidebar.slider("Scala Attaccanti", 140, 200, 180, step=5)

# Normalizzazione pesi
totale_pesi = peso_fvm + peso_fm + peso_qta + peso_pres + peso_bonus
if totale_pesi != 1.0:
    st.sidebar.warning(f"⚠️ Totale pesi: {totale_pesi:.2f} (dovrebbe essere 1.0)")

# Caricamento file
st.header("📁 Caricamento Dati")
col1, col2 = st.columns(2)
with col1:
    file_quot = st.file_uploader("Carica Quotazioni (.xlsx)", type="xlsx")
with col2:
    file_stat = st.file_uploader("Carica Statistiche (.xlsx)", type="xlsx")

if file_quot and file_stat:
    try:
        # Lettura dati
        df_quot = pd.read_excel(file_quot, header=1)
        df_stat = pd.read_excel(file_stat, header=1)
        df = pd.merge(df_quot, df_stat, on="Nome", how="inner", suffixes=("_quot", "_stat"))
        df["R"] = df["R_stat"]
        df["Squadra"] = df["Squadra_quot"]

        
        # Controllo colonne
        colonne_necessarie = ["FVM M", "Fm", "Qt.A", "Pv", "Gf", "Ass", "Amm", "Esp", "Rp", "Rc", "R"]
        colonne_mancanti = [col for col in colonne_necessarie if col not in df.columns]
        if colonne_mancanti:
            st.error(f"Colonne mancanti: {', '.join(colonne_mancanti)}")
            st.stop()
        
        # Calcolo percentili
        df["Perc_FVM_M"] = df["FVM M"].rank(pct=True)
        df["Perc_FM"] = df["Fm"].rank(pct=True)
        df["Perc_QTA"] = df["Qt.A"].rank(pct=True)
        df["Perc_Pres"] = df["Pv"].rank(pct=True)
        
        # Sistema Bonus/Malus migliorato e bilanciato per ruolo
        def calcola_bonus_ruolo(row):
            ruolo = row["R"]
            if ruolo == "Por":  # Portiere
                return (
                    10 * row["Gf"] +     # Gol portiere rarissimi = massimo bonus
                    3 * row["Ass"] +     # Assist portiere rari
                    8 * row["Rp"] +      # Rigori parati = specialità portieri
                    -1 * row["Amm"] +    # Ammonizioni meno gravi per portieri
                    -6 * row["Esp"]      # Espulsioni molto gravi
                )
            elif ruolo == "Dif":  # Difensore  
                return (
                    5 * row["Gf"] +      # Gol difensore molto preziosi
                    3 * row["Ass"] +     # Assist difensore importanti
                    1 * row["Rp"] +      # Rigori meno comuni
                    0.5 * row["Rc"] +    # Rigori calciati rari
                    -1.5 * row["Amm"] +  # Ammonizioni più accettabili
                    -4 * row["Esp"]      # Espulsioni gravi
                )
            elif ruolo == "Cen":  # Centrocampista
                return (
                    3.5 * row["Gf"] +    # Gol centrocampista buoni
                    4 * row["Ass"] +     # Assist = specialità centrocampisti
                    3 * row["Rp"] +      # Rigori importanti
                    2 * row["Rc"] +      # Rigori calciati frequenti
                    -1.5 * row["Amm"] +  # Ammonizioni nella media
                    -3 * row["Esp"]      # Espulsioni problematiche
                )
            else:  # Attaccante (Att)
                return (
                    2.5 * row["Gf"] +    # Gol = dovere degli attaccanti
                    2.5 * row["Ass"] +   # Assist comunque utili
                    4 * row["Rp"] +      # Rigori molto importanti per attaccanti
                    2 * row["Rc"] +      # Rigori calciati frequenti
                    -2 * row["Amm"] +    # Ammonizioni più pesanti
                    -3 * row["Esp"]      # Espulsioni problematiche
                )
        
        df["BonusRaw"] = df.apply(calcola_bonus_ruolo, axis=1)
        
        # Normalizzazione bonus per ruolo
        df["BonusNorm"] = 0
        for ruolo in df["R"].unique():
            mask = df["R"] == ruolo
            bonus_ruolo = df.loc[mask, "BonusRaw"]
            if bonus_ruolo.max() != bonus_ruolo.min():
                df.loc[mask, "BonusNorm"] = (bonus_ruolo - bonus_ruolo.min()) / (bonus_ruolo.max() - bonus_ruolo.min())
        
        # Fattore continuità (presenze/partite totali della stagione)
        partite_stagione = 25  # Assumendo 25 giornate giocate
        df["ContinuitaFactor"] = np.minimum(df["Pv"] / partite_stagione, 1.0)
        
        # Formula punteggio finale con scala ottimizzata (0-200)
        punteggio_base = (
            peso_fvm * df["Perc_FVM_M"] +
            peso_fm * df["Perc_FM"] +
            peso_qta * df["Perc_QTA"] +
            peso_pres * df["Perc_Pres"] +
            peso_bonus * df["BonusNorm"]
        )
        
        # Scala dinamica per ruolo con valori configurabili
        df["Punteggio"] = 0
        scale_ruolo = {"Por": scala_por, "Dif": scala_dif, "Cen": scala_cen, "Att": scala_att}
        
        for ruolo in df["R"].unique():
            mask = df["R"] == ruolo
            scala_ruolo = scale_ruolo.get(ruolo, 150)  # Default 150 se ruolo non trovato
            
            df.loc[mask, "Punteggio"] = (
                punteggio_base[mask] * scala_ruolo * 
                df.loc[mask, "ContinuitaFactor"]
            )
        
        # Tabs per diverse sezioni
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏆 Classifica", "🔄 Scambi", "📈 Analisi", "🎯 Raccomandazioni", "📊 Statistiche"])
        
        with tab1:
            st.subheader("🏆 Top 100 Migliori Punteggi")
            
            # Filtri
            col1, col2, col3 = st.columns(3)
            with col1:
                ruoli_selezionati = st.multiselect("Filtra per Ruolo", df["R"].unique(), default=df["R"].unique())
            with col2:
                squadre_selezionate = st.multiselect("Filtra per Squadra", df["Squadra"].unique(), default=df["Squadra"].unique())
            with col3:
                min_presenze = st.slider("Presenze minime", 0, int(df["Pv"].max()), 0)
            
            # Applicazione filtri
            df_filtrato = df[
                (df["R"].isin(ruoli_selezionati)) &
                (df["Squadra"].isin(squadre_selezionate)) &
                (df["Pv"] >= min_presenze)
            ]
            
            top_100 = df_filtrato.nlargest(100, "Punteggio")[
                ["Nome", "R", "Squadra", "Punteggio", "FVM M", "Fm", "Qt.A", "Pv", "ContinuitaFactor"]
            ]
            top_100_display = top_100.copy()
            top_100_display["Punteggio"] = top_100_display["Punteggio"].round(2)
            top_100_display["ContinuitaFactor"] = top_100_display["ContinuitaFactor"].round(3)
            top_100_display.index = range(1, len(top_100_display) + 1)
            
            st.dataframe(top_100_display, use_container_width=True)
        
        with tab2:
            st.subheader("🔄 Simulatore Scambi")
            
            # Scelta giocatori
            nomi_giocatori = df["Nome"].sort_values().tolist()
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔵 Squadra A")
                squadra_a = []
                for i in range(7):
                    giocatore = st.selectbox(f"A{i+1}", [""] + nomi_giocatori, key=f"A{i}")
                    if giocatore:
                        squadra_a.append(giocatore)
            
            with col2:
                st.subheader("🔴 Squadra B")
                squadra_b = []
                for i in range(7):
                    giocatore = st.selectbox(f"B{i+1}", [""] + nomi_giocatori, key=f"B{i}")
                    if giocatore:
                        squadra_b.append(giocatore)
            
            if squadra_a and squadra_b:
                # Calcoli scambio
                df_a = df[df["Nome"].isin(squadra_a)]
                df_b = df[df["Nome"].isin(squadra_b)]
                
                tot_a = df_a["Punteggio"].sum()
                tot_b = df_b["Punteggio"].sum()
                diff = abs(tot_a - tot_b)
                media = (tot_a + tot_b) / 2
                perc_diff = (diff / media) * 100 if media != 0 else 0
                
                # Risultati
                st.subheader("📊 Risultato dello Scambio")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Totale Squadra A", f"{tot_a:.2f}")
                    st.metric("Media FVM Squadra A", f"{df_a['FVM M'].mean():.2f}")
                
                with col2:
                    st.metric("Totale Squadra B", f"{tot_b:.2f}")
                    st.metric("Media FVM Squadra B", f"{df_b['FVM M'].mean():.2f}")
                
                with col3:
                    st.metric("Differenza %", f"{perc_diff:.2f}%")
                    if perc_diff <= soglia_max:
                        st.success("✅ Scambio VALIDO")
                    else:
                        st.error("❌ Scambio NON valido")
                
                # Dettaglio giocatori
                st.subheader("👥 Dettaglio Giocatori")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Squadra A:**")
                    st.dataframe(df_a[["Nome", "R", "Punteggio", "FVM M", "Fm"]].round(2))
                
                with col2:
                    st.write("**Squadra B:**")
                    st.dataframe(df_b[["Nome", "R", "Punteggio", "FVM M", "Fm"]].round(2))
        
        with tab3:
            st.subheader("📈 Analisi Avanzata")
            
            # Grafico distribuzione punteggi per ruolo
            fig_ruolo = px.box(df, x="R", y="Punteggio", title="Distribuzione Punteggi per Ruolo")
            st.plotly_chart(fig_ruolo, use_container_width=True)
            
            # Correlazione tra metriche
            col1, col2 = st.columns(2)
            with col1:
                fig_corr1 = px.scatter(df, x="FVM M", y="Punteggio", color="R", 
                                     title="Punteggio vs FVM M", hover_data=["Nome"])
                st.plotly_chart(fig_corr1, use_container_width=True)
            
            with col2:
                fig_corr2 = px.scatter(df, x="Fm", y="Punteggio", color="R",
                                     title="Punteggio vs Media Voto", hover_data=["Nome"])
                st.plotly_chart(fig_corr2, use_container_width=True)
        
        with tab4:
            st.subheader("🎯 Raccomandazioni Intelligenti")
            
            # Giocatori sottovalutati (alto punteggio, basso FVM)
            df["Rapporto_Valore"] = df["Punteggio"] / df["FVM M"]
            sottovalutati = df.nlargest(20, "Rapporto_Valore")[["Nome", "R", "Squadra", "Punteggio", "FVM M", "Rapporto_Valore"]]
            
            st.write("**🔍 Top 20 Giocatori Sottovalutati (Miglior rapporto Punteggio/Prezzo):**")
            st.dataframe(sottovalutati.round(3))
        
        with tab5:
            st.subheader("📊 Statistiche Avanzate")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Totale Giocatori", len(df))
                st.metric("Media Punteggio", f"{df['Punteggio'].mean():.2f}")
            
            with col2:
                st.metric("Punteggio Massimo", f"{df['Punteggio'].max():.2f}")
                st.metric("Punteggio Minimo", f"{df['Punteggio'].min():.2f}")
            
            with col3:
                giocatore_top = df.loc[df['Punteggio'].idxmax(), 'Nome']
                st.metric("Miglior Giocatore", giocatore_top)
                st.metric("Squadre Totali", df['Squadra'].nunique())
            
            with col4:
                st.metric("Portieri", len(df[df['R'] == 'Por']))
                st.metric("Giocatori Movimento", len(df[df['R'] != 'Por']))
            
            # Statistiche per ruolo
            st.write("**Statistiche per Ruolo:**")
            stats_ruolo = df.groupby('R').agg({
                'Punteggio': ['count', 'mean', 'std', 'min', 'max'],
                'FVM M': 'mean',
                'Fm': 'mean'
            }).round(2)
            st.dataframe(stats_ruolo)
            
    except Exception as e:
        st.error(f"Errore durante l'elaborazione: {e}")
        st.write("Controlla che i file abbiano il formato corretto e tutte le colonne necessarie.")

else:
    with st.expander("🔍 Dettaglio Sistema Punteggio per Ruolo"):
        st.write("""
        **📊 Sistema di Punteggio Ruolo-Specifico:**
        
        **🥅 PORTIERI (Scala: 80-150)**
        - Gol: x10 (rarissimi, massimo valore)
        - Assist: x3 (rari ma preziosi)  
        - Rigori Parati: x8 (specialità del ruolo)
        - Ammonizioni: -1 (meno gravi)
        - Espulsioni: -6 (molto gravi)
        
        **🛡️ DIFENSORI (Scala: 100-170)**
        - Gol: x5 (molto preziosi)
        - Assist: x3 (importanti)
        - Rigori: x1 (meno comuni)
        - Ammonizioni: -1.5 (più accettabili)
        - Espulsioni: -4 (gravi)
        
        **⚽ CENTROCAMPISTI (Scala: 120-190)**
        - Gol: x3.5 (buoni)
        - Assist: x4 (specialità del ruolo)
        - Rigori Parati/Segnati: x3 (importanti)
        - Rigori Calciati: x2 (frequenti)
        - Ammonizioni: -1.5 (nella media)
        
        **🎯 ATTACCANTI (Scala: 140-200)**
        - Gol: x2.5 (dovere del ruolo)
        - Assist: x2.5 (comunque utili)
        - Rigori Parati/Segnati: x4 (molto importanti)
        - Rigori Calciati: x2 (frequenti)
        - Ammonizioni: -2 (più pesanti)
        
        **💡 La scala diversa per ruolo riflette:**
        - Portieri: Meno variabilità nelle prestazioni
        - Attaccanti: Massima variabilità e impatto
        - Centrocampisti: Alta variabilità per polivalenza
        - Difensori: Variabilità media ma bonus alti per gol
        """)
        
        # Mostra distribuzione attuale
        if 'df' in locals():
            st.write("**📈 Distribuzione Punteggi Attuali:**")
            for ruolo in sorted(df["R"].unique()):
                df_ruolo = df[df["R"] == ruolo]
                st.write(f"**{ruolo}**: Media {df_ruolo['Punteggio'].mean():.1f}, "
                       f"Min {df_ruolo['Punteggio'].min():.1f}, "
                       f"Max {df_ruolo['Punteggio'].max():.1f}")
    
    st.info("👆 Carica entrambi i file per iniziare l'analisi!")

# Istruzioni
with st.expander("📋 Istruzioni d'uso"):
    st.write("""
    **Come usare il tool:**
    
    1. **Carica i file Excel** delle quotazioni e statistiche
    2. **Configura i pesi** nella sidebar per personalizzare la formula
    3. **Esplora le diverse tab:**
       - 🏆 **Classifica**: Top giocatori con filtri avanzati
       - 🔄 **Scambi**: Simula scambi tra squadre
       - 📈 **Analisi**: Grafici e correlazioni
       - 🎯 **Raccomandazioni**: Giocatori sottovalutati
       - 📊 **Statistiche**: Dati aggregati per ruolo
    
    **Caratteristiche del sistema:**
    - ✅ Punteggi specifici per ruolo
    - ✅ Fattore continuità basato sulle presenze
    - ✅ Analisi sottovalutati
    - ✅ Grafici interattivi
    - ✅ Filtri avanzati
    """)
