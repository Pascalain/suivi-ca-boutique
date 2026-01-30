import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Mon Pilotage CA - Mobile", layout="wide")

# --- CONNEXION GOOGLE SHEETS ---
url = "https://docs.google.com/spreadsheets/d/1_I18zdvUHy_Qu_-kOisx8p20fR9KP7ytO8eDXcPywho/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des données
df = conn.read(spreadsheet=url, ttl="0")

# --- SÉCURITÉ ---
if "password" not in st.session_state:
    st.session_state["password"] = ""

if st.session_state["password"] != "Boutique2025":
    st.title("🔐 Accès Restreint")
    pwd = st.text_input("Entrez le mot de passe :", type="password")
    if st.button("Se connecter"):
        st.session_state["password"] = pwd
        st.rerun()
    st.stop()

# --- LOGIQUE DES MOIS (VOTRE VERSION INITIALE) ---
def semaine_en_mois_multi(s, annee):
    if annee == 2026:
        if s <= 5: return "Janvier"
        if s <= 9: return "Février"
        if s <= 13: return "Mars"
        if s <= 18: return "Avril"
        if s <= 22: return "Mai"
        if s <= 26: return "Juin"
        if s <= 31: return "Juillet"
        if s <= 35: return "Août"
        if s <= 40: return "Septembre"
        if s <= 44: return "Octobre"
        if s <= 48: return "Novembre"
        return "Décembre"
    else: # 2024 / 2025
        if s <= 5: return "Janvier"
        if s <= 9: return "Février"
        if s <= 13: return "Mars"
        if s <= 17: return "Avril"
        if s <= 21: return "Mai"
        if s <= 26: return "Juin"
        if s <= 30: return "Juillet"
        if s <= 35: return "Août"
        if s <= 39: return "Septembre"
        if s <= 44: return "Octobre"
        if s <= 48: return "Novembre"
        return "Décembre"

# --- FILTRES ---
st.sidebar.header("🔍 FILTRES")
pv = st.sidebar.selectbox("Point de Vente", ["Les Halles", "Le Magasin"])
prod = st.sidebar.selectbox("Produit", ["Pascalain", "Tripes & Cie"])
semaine_recherche = st.sidebar.number_input("🔎 Semaine", 1, 53, value=datetime.now().isocalendar()[1])

# --- CALCULS ---
df_filtre = df[(df['PointDeVente'] == pv) & (df['Produit'] == prod)].copy() if not df.empty else pd.DataFrame()

st.title(f"📊 Suivi CA : {pv}")

if not df_filtre.empty:
    # Indicateurs (KPI)
    dernier_ca = df_filtre.sort_values(['Annee', 'Semaine']).iloc[-1]['CA']
    st.metric(label=f"Dernier CA saisi ({prod})", value=f"{dernier_ca:,.2f} €")

    # Graphique
    fig = px.line(df_filtre.sort_values(["Annee", "Semaine"]), x="Semaine", y="CA", color="Annee", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # Tableau Récapitulatif Mensuel (La version que vous aimiez)
    st.subheader("🗓️ Récapitulatif Mensuel")
    df_filtre['Mois'] = df_filtre.apply(lambda x: semaine_en_mois_multi(x['Semaine'], x['Annee']), axis=1)
    ordre_mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    recap = df_filtre.groupby(['Mois', 'Annee'])['CA'].sum().unstack().fillna(0)
    recap = recap.reindex(ordre_mois).dropna(how='all')
    st.table(recap.style.format("{:.2f} €"))
else:
    st.info("Aucune donnée disponible.")

st.divider()

# --- FORMULAIRE DE SAISIE ---
with st.expander("➕ SAISIR UN CHIFFRE"):
    with st.form("Saisie", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        s_i = c1.number_input("Semaine", 1, 53, value=semaine_recherche)
        a_i = c2.selectbox("Année", [2024, 2025, 2026], index=1)
        ca_i = c3.number_input("Montant (€)", min_value=0.0)
        
        if st.form_submit_button("Enregistrer"):
            new_data = pd.DataFrame([{"Semaine": int(s_i), "Annee": int(a_i), "PointDeVente": pv, "Produit": prod, "CA": float(ca_i)}])
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(spreadsheet=url, data=updated_df)
            st.success("Enregistré !")
            st.cache_data.clear()
            st.rerun()

# --- SUPPRESSION ---
if not df.empty:
    with st.expander("🗑️ SUPPRIMER LA DERNIÈRE LIGNE"):
        if st.button("Confirmer la suppression définitive"):
            df_final = df.drop(df.index[-1])
            conn.update(spreadsheet=url, data=df_final)
            st.warning("Dernière ligne supprimée.")
            st.cache_data.clear()
            st.rerun()
