import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Logiciel de Pilotage", layout="wide")

# --- CONNEXION ---
# Utilisation de la connexion officielle pour permettre l'écriture
url = "https://docs.google.com/spreadsheets/d/1_I18zdvUHy_Qu_-kOisx8p20fR9KP7ytO8eDXcPywho/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url, ttl="0")

# --- MOT DE PASSE ---
if "password" not in st.session_state:
    st.session_state["password"] = ""
if st.session_state["password"] != "Boutique2025":
    pwd = st.text_input("Mot de passe sécurisé :", type="password")
    if st.button("Accéder à l'interface"):
        st.session_state["password"] = pwd
        st.rerun()
    st.stop()

# --- LOGIQUE DES MOIS 2024 ---
def semaine_en_mois(s):
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

# --- INTERFACE ---
st.title("🚀 Pilotage des Ventes")

# Barre latérale dynamique
if not df.empty:
    liste_magasins = sorted(df['PointDeVente'].unique().tolist())
else:
    liste_magasins = ["Aucun magasin trouvé"]

pv = st.sidebar.selectbox("Sélectionner le magasin", liste_magasins)
prod = st.sidebar.selectbox("Gamme de produit", ["Pascalain", "Tripes & Cie"])

# --- ONGLETS PRINCIPAUX ---
tab_stats, tab_saisie, tab_admin = st.tabs(["📈 Statistiques", "➕ Saisie CA", "⚙️ Gestion Magasins"])

with tab_stats:
    if not df.empty:
        df_filtre = df[(df['PointDeVente'] == pv) & (df['Produit'] == prod)]
        if not df_filtre.empty:
            # Vos graphiques et calculs habituels ici...
            st.info(f"Analyse en cours pour {pv} / {prod}")
            # ... (on remettra ici le code des graphiques que vous aviez)
        else:
            st.warning("Aucune donnée pour ce magasin.")

with tab_saisie:
    st.subheader("Enregistrer un nouveau chiffre")
    with st.form("form_ca"):
        col1, col2 = st.columns(2)
        sem = col1.number_input("Semaine", 1, 53, value=1)
        ann = col2.selectbox("Année", [2024, 2025, 2026])
        montant = st.number_input("CA réalisé (€)", min_value=0.0)
        
        if st.form_submit_button("Valider l'enregistrement"):
            nouvelle_ligne = pd.DataFrame([{
                "PointDeVente": pv, "Produit": prod, "Semaine": sem, 
                "Annee": ann, "CA": montant
            }])
            df_final = pd.concat([df, nouvelle_ligne], ignore_index=True)
            conn.update(spreadsheet=url, data=df_final)
            st.success("Données synchronisées !")

with tab_admin:
    st.subheader("Ajouter un nouveau point de vente")
    with st.form("form_pv"):
        nouveau_nom = st.text_input("Nom du nouveau magasin (ex: Limoges Centre)")
        if st.form_submit_button("Créer le magasin"):
            if nouveau_nom and nouveau_nom not in liste_magasins:
                # On crée une ligne "fantôme" avec un CA de 0 pour initialiser le magasin
                init_ligne = pd.DataFrame([{
                    "PointDeVente": nouveau_nom, "Produit": "Pascalain", 
                    "Semaine": 1, "Annee": 2025, "CA": 0
                }])
                df_final = pd.concat([df, init_ligne], ignore_index=True)
                conn.update(spreadsheet=url, data=df_final)
                st.success(f"Le magasin {nouveau_nom} a été ajouté ! Rafraîchissez la page.")
            else:
                st.error("Nom invalide ou déjà existant.")
