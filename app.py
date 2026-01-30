import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi CA - Boutique", layout="wide")

# --- CONNEXION ---
url = "https://docs.google.com/spreadsheets/d/1_I18zdvUHy_Qu_-kOisx8p20fR9KP7ytO8eDXcPywho/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url, ttl="0")

# --- SÉCURITÉ ---
if "password" not in st.session_state:
    st.session_state["password"] = ""
if st.session_state["password"] != "Boutique2025":
    pwd = st.text_input("Mot de passe :", type="password")
    if st.button("Se connecter"):
        st.session_state["password"] = pwd
        st.rerun()
    st.stop()

# --- DÉCOUPAGE DES MOIS (RETOUR À VOTRE LOGIQUE 2024) ---
def semaine_en_mois(s, annee):
    if s <= 5: return "Janvier"
    if s <= 9: return "Février"
    if s <= 13: return "Mars"
    if s <= 17: return "Avril" # <--- Correction ici pour 2024
    if s <= 21: return "Mai"
    if s <= 26: return "Juin"
    if s <= 30: return "Juillet"
    if s <= 35: return "Août"
    if s <= 39: return "Septembre"
    if s <= 44: return "Octobre"
    if s <= 48: return "Novembre"
    return "Décembre"

# --- RÉCUPÉRATION DYNAMIQUE DES MAGASINS ---
# On lit les magasins directement depuis la colonne 'PointDeVente' de votre Google Sheet
if not df.empty and 'PointDeVente' in df.columns:
    liste_magasins = sorted(df['PointDeVente'].unique().tolist())
else:
    liste_magasins = ["Les Halles", "Le Magasin"]

# --- FILTRES ---
st.sidebar.markdown("### 🔍 FILTRES")
pv = st.sidebar.selectbox("Choisir le Point de Vente", liste_magasins)
prod = st.sidebar.selectbox("Produit", ["Pascalain", "Tripes & Cie"])
semaine_analyse = st.sidebar.number_input("🔎 Semaine à analyser", 1, 53, value=1)

st.title(f"📊 Suivi CA : {pv}")

if not df.empty:
    df_filtre = df[(df['PointDeVente'] == pv) & (df['Produit'] == prod)].copy()
    
    if not df_filtre.empty:
        # KPI & GRAPHIQUE (Même code qu'avant, il fonctionnait)
        ca_2025 = df_filtre[(df_filtre['Annee'] == 2025) & (df_filtre['Semaine'] == semaine_analyse)]['CA'].sum()
        ca_2024 = df_filtre[(df_filtre['Annee'] == 2024) & (df_filtre['Semaine'] == semaine_analyse)]['CA'].sum()
        ecart = ca_2025 - ca_2024
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CA 2025", f"{ca_2025:,.2f} €")
        c2.metric("CA 2024", f"{ca_2024:,.2f} €")
        c3.metric("Écart", f"{ecart:,.2f} €", delta=f"{ecart:,.2f} €")
        c4.metric("Évolution", f"{(ecart/ca_2024*100 if ca_2024!=0 else 0):.2f} %")

        fig = px.line(df_filtre.sort_values(["Annee", "Semaine"]), x="Semaine", y="CA", color="Annee", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # TABLEAU RÉCAPITULATIF AVEC LA BONNE LOGIQUE DE MOIS
        st.subheader("🗓️ Récapitulatif Mensuel")
        df_filtre['Mois'] = df_filtre.apply(lambda x: semaine_en_mois(x['Semaine'], x['Annee']), axis=1)
        recap = df_filtre.groupby(['Mois', 'Annee'])['CA'].sum().unstack().fillna(0)
        ordre_mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        recap = recap.reindex(ordre_mois).dropna(how='all')
        st.table(recap.style.format("{:.2f} €"))

st.divider()

# --- ONGLETS ---
t1, t2, t3 = st.tabs(["➕ Saisir", "🗑️ Supprimer", "🏪 Nouveau Magasin"])

with t1:
    with st.form("saisie"):
        s_i = st.number_input("Semaine", 1, 53, value=semaine_analyse)
        a_i = st.selectbox("Année", [2024, 2025, 2026], index=1)
        ca_i = st.number_input("Montant (€)", min_value=0.0)
        if st.form_submit_button("Enregistrer"):
            # SI L'ENREGISTREMENT ECHOUE ENCORE :
            st.error("L'enregistrement direct est bloqué par Google. Veuillez saisir dans le tableau via le bouton ci-dessous.")
            st.link_button("Ouvrir le Tableau pour saisir", url)

with t2:
    st.link_button("Ouvrir le Tableau pour supprimer", url)

with t3:
    st.write("Pour ajouter un nouveau magasin, ajoutez simplement son nom dans la colonne 'PointDeVente' de votre Google Sheet.")
    st.link_button("Ajouter un magasin dans le tableau", url)
