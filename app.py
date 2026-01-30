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

# --- LOGIQUE DES MOIS ---
def semaine_en_mois(s, annee):
    # Logique adaptée pour correspondre à vos données
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

# --- BARRE LATÉRALE ---
st.sidebar.markdown("### 🔍 FILTRES")
pv = st.sidebar.selectbox("Choisir le Point de Vente", ["Les Halles", "Le Magasin"])
prod = st.sidebar.selectbox("Produit", ["Pascalain", "Tripes & Cie"])
semaine_analyse = st.sidebar.number_input("🔎 Semaine à analyser", 1, 53, value=1)

# --- TITRE PRINCIPAL ---
st.title(f"📊 Suivi CA : {pv}")

if not df.empty:
    df_filtre = df[(df['PointDeVente'] == pv) & (df['Produit'] == prod)].copy()
    
    if not df_filtre.empty:
        # --- INDICATEURS (KPI) ---
        ca_2025 = df_filtre[(df_filtre['Annee'] == 2025) & (df_filtre['Semaine'] == semaine_analyse)]['CA'].sum()
        ca_2024 = df_filtre[(df_filtre['Annee'] == 2024) & (df_filtre['Semaine'] == semaine_analyse)]['CA'].sum()
        ecart_kpi = ca_2025 - ca_2024
        evol_kpi = (ecart_kpi / ca_2024 * 100) if ca_2024 != 0 else 0

        st.write(f"Comparaison Semaine {semaine_analyse} : **2025 vs 2024**")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CA 2025", f"{ca_2025:,.2f} €")
        c2.metric("CA 2024", f"{ca_2024:,.2f} €")
        c3.metric("Écart (€)", f"{ecart_kpi:,.2f} €", delta=f"{ecart_kpi:,.2f} €")
        c4.metric("Évolution (%)", f"{evol_kpi:.2f} %", delta=f"{evol_kpi:.2f} %")

        # --- GRAPHIQUE ---
        fig = px.line(df_filtre.sort_values(["Annee", "Semaine"]), 
                     x="Semaine", y="CA", color="Annee", markers=True,
                     color_discrete_map={2024: "silver", 2025: "#0077b6"})
        st.plotly_chart(fig, use_container_width=True)

        # --- TABLEAU RÉCAPITULATIF MENSUEL DÉTAILLÉ ---
        st.subheader("🗓️ Récapitulatif Mensuel")
        df_filtre['Mois'] = df_filtre.apply(lambda x: semaine_en_mois(x['Semaine'], x['Annee']), axis=1)
        
        # Groupement par mois et année
        recap = df_filtre.groupby(['Mois', 'Annee'])['CA'].sum().unstack().fillna(0)
        
        # S'assurer que 2024 et 2025 existent
        for an in [2024, 2025]:
            if an not in recap.columns: recap[an] = 0.0
            
        # Calcul des colonnes Ecart et Evolution
        recap['Écart 2025/2024'] = recap[2025] - recap[2024]
        recap['Evol %'] = (recap['Écart 2025/2024'] / recap[2024] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        
        # Tri par mois
        ordre_mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        recap = recap.reindex(ordre_mois).dropna(how='all')
        
        # Affichage du tableau formaté
        st.table(recap.style.format({
            2024: "{:.2f} €", 
            2025: "{:.2f} €", 
            'Écart 2025/2024': "{:.2f} €", 
            'Evol %': "{:.2f} %"
        }))

st.divider()

# --- ONGLETS DE SAISIE ET GESTION ---
t1, t2, t3 = st.tabs(["➕ Saisir", "🗑️ Supprimer", "🏪 Magasin"])

with t1:
    with st.form("saisie_ca", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        s_i = col1.number_input("Semaine", 1, 53, value=semaine_analyse)
        a_i = col2.selectbox("Année", [2024, 2025, 2026], index=1)
        ca_i = col3.number_input("Montant (€)", min_value=0.0)
        if st.form_submit_button("Enregistrer"):
            new_line = pd.DataFrame([{"Semaine": int(s_i), "Annee": int(a_i), "PointDeVente": pv, "Produit": prod, "CA": float(ca_i)}])
            df_updated = pd.concat([df, new_line], ignore_index=True)
            conn.update(spreadsheet=url, data=df_updated)
            st.success("Donnée enregistrée dans le Cloud !")
            st.cache_data.clear()
            st.rerun()

with t2:
    st.write("Gestion de la base de données")
    if st.button("❌ Supprimer la dernière ligne enregistrée"):
        df_final = df.drop(df.index[-1])
        conn.update(spreadsheet=url, data=df_final)
        st.warning("Ligne supprimée.")
        st.cache_data.clear()
        st.rerun()
