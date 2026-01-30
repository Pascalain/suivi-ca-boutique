import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi CA - Les Halles", layout="wide")

# --- CONNEXION GOOGLE SHEETS ---
url = "https://docs.google.com/spreadsheets/d/1_I18zdvUHy_Qu_-kOisx8p20fR9KP7ytO8eDXcPywho/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url, ttl="0")

# --- SÉCURITÉ ---
if "password" not in st.session_state:
    st.session_state["password"] = ""
if st.session_state["password"] != "Boutique2025":
    st.title("🔐 Accès Restreint")
    pwd = st.text_input("Mot de passe :", type="password")
    if st.button("Se connecter"):
        st.session_state["password"] = pwd
        st.rerun()
    st.stop()

# --- BARRE LATÉRALE (FILTRES) ---
st.sidebar.markdown("### 🔍 FILTRES")
pv = st.sidebar.selectbox("Choisir le Point de Vente", ["Les Halles", "Le Magasin"])
prod = st.sidebar.selectbox("Produit", ["Pascalain", "Tripes & Cie"])
semaine_analyse = st.sidebar.number_input("🔎 Semaine à analyser", 1, 53, value=1)

# --- TITRE PRINCIPAL ---
st.title(f"📊 Suivi CA : {pv}")

if not df.empty:
    df_filtre = df[(df['PointDeVente'] == pv) & (df['Produit'] == prod)].copy()
    
    if not df_filtre.empty:
        # --- CALCULS INDICATEURS (KPI) ---
        # On cherche les données pour la semaine choisie
        ca_2025 = df_filtre[(df_filtre['Annee'] == 2025) & (df_filtre['Semaine'] == semaine_analyse)]['CA'].sum()
        ca_2024 = df_filtre[(df_filtre['Annee'] == 2024) & (df_filtre['Semaine'] == semaine_analyse)]['CA'].sum()
        ecart = ca_2025 - ca_2024
        evolution = (ecart / ca_2024 * 100) if ca_2024 != 0 else 0

        st.write(f"**Comparaison Semaine {semaine_analyse} : 2025 vs 2024**")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("CA 2025", f"{ca_2025:,.2f} €")
        col2.metric("CA 2024", f"{ca_2024:,.2f} €")
        col3.metric("Écart (€)", f"{ecart:,.2f} €", delta=f"{ecart:,.2f} €")
        col4.metric("Évolution (%)", f"{evolution:.2f} %", delta=f"{evolution:.2f} %")

        # --- GRAPHIQUE ---
        fig = px.line(df_filtre.sort_values(["Annee", "Semaine"]), 
                     x="Semaine", y="CA", color="Annee", markers=True,
                     color_discrete_map={2024: "grey", 2025: "#0077b6"})
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- LES ONGLETS (TABS) COMME SUR VOTRE PHOTO ---
tab1, tab2, tab3 = st.tabs(["➕ Saisir", "🗑️ Supprimer", "🏪 Magasin"])

with tab1:
    with st.form("form_saisie", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        s_i = c1.number_input("Semaine", 1, 53, value=semaine_analyse)
        a_i = col2.selectbox("Année", [2024, 2025, 2026], index=1)
        ca_i = c3.number_input("Montant (€)", min_value=0.0)
        if st.form_submit_button("Enregistrer"):
            new_line = pd.DataFrame([{"Semaine": int(s_i), "Annee": int(a_i), "PointDeVente": pv, "Produit": prod, "CA": float(ca_i)}])
            df_updated = pd.concat([df, new_line], ignore_index=True)
            conn.update(spreadsheet=url, data=df_updated)
            st.success("Donnée enregistrée !")
            st.cache_data.clear()
            st.rerun()

with tab2:
    st.write("Supprimer la dernière entrée pour ce magasin.")
    if st.button("Confirmer la suppression"):
        df_final = df.drop(df.index[-1])
        conn.update(spreadsheet=url, data=df_final)
        st.warning("Ligne supprimée.")
        st.cache_data.clear()
        st.rerun()

with tab3:
    st.write("Configuration des points de vente.")
    st.info("Cette section est en cours de développement.")
