import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi CA - Boutique", layout="wide")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")

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

# --- DÉCOUPAGE PRÉCIS DES SEMAINES ---
def semaine_en_mois(s, annee):
    if annee == 2024:
        if s <= 4: return "Janvier"
        if s <= 8: return "Février"
        if s <= 13: return "Mars"
        if s <= 17: return "Avril"
        if s <= 22: return "Mai"
        if s <= 26: return "Juin"
        if s <= 30: return "Juillet"
        if s <= 35: return "Août"
        if s <= 39: return "Septembre"
        if s <= 43: return "Octobre"
        if s <= 48: return "Novembre"
        return "Décembre"
    elif annee == 2026:
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
    else: # 2025
        if s <= 5: return "Janvier"
        if s <= 9: return "Février"
        if s <= 13: return "Mars"
        if s <= 17: return "Avril"
        if s <= 22: return "Mai"
        if s <= 26: return "Juin"
        if s <= 31: return "Juillet"
        if s <= 35: return "Août"
        if s <= 39: return "Septembre"
        if s <= 44: return "Octobre"
        if s <= 48: return "Novembre"
        return "Décembre"

# --- RÉCUPÉRATION MAGASINS ---
if not df.empty and 'PointDeVente' in df.columns:
    liste_magasins = sorted(df['PointDeVente'].unique().tolist())
else:
    liste_magasins = ["Les Halles", "Le Magasin"]

# --- BARRE LATÉRALE ---
st.sidebar.markdown("### 🔍 FILTRES")
pv = st.sidebar.selectbox("Choisir le Point de Vente", liste_magasins)
prod = st.sidebar.selectbox("Produit", ["Pascalain", "Tripes & Cie"])
semaine_analyse = st.sidebar.number_input("🔎 Semaine à analyser", 1, 53, value=datetime.now().isocalendar()[1])

st.sidebar.markdown("### 📅 COMPARAISON")
annee_n = st.sidebar.selectbox("Année en cours (N)", [2024, 2025, 2026], index=2)
annee_n1 = st.sidebar.selectbox("Comparer avec (N-1)", [2024, 2025, 2026], index=1)

# --- TITRE PRINCIPAL ---
st.title(f"📊 Suivi CA : {pv}")

if not df.empty:
    df_filtre = df[(df['PointDeVente'] == pv) & (df['Produit'] == prod)].copy()
    
    if not df_filtre.empty:
        # KPI
        ca_n = df_filtre[(df_filtre['Annee'] == annee_n) & (df_filtre['Semaine'] == semaine_analyse)]['CA'].sum()
        ca_n1 = df_filtre[(df_filtre['Annee'] == annee_n1) & (df_filtre['Semaine'] == semaine_analyse)]['CA'].sum()
        ecart_kpi = ca_n - ca_n1
        evol_kpi = (ecart_kpi / ca_n1 * 100) if ca_n1 != 0 else 0

        st.write(f"Comparaison Semaine {semaine_analyse} : **{annee_n} vs {annee_n1}**")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"CA {annee_n}", f"{ca_n:,.2f} €")
        c2.metric(f"CA {annee_n1}", f"{ca_n1:,.2f} €")
        c3.metric("Écart (€)", f"{ecart_kpi:,.2f} €", delta=f"{ecart_kpi:,.2f} €")
        c4.metric("Évolution (%)", f"{evol_kpi:.2f} %", delta=f"{evol_kpi:.2f} %")

        # GRAPHIQUE
        df_graph = df_filtre[df_filtre['Annee'].isin([annee_n, annee_n1])]
        fig = px.line(df_graph.sort_values(["Annee", "Semaine"]), 
                     x="Semaine", y="CA", color="Annee", markers=True,
                     color_discrete_map={annee_n1: "silver", annee_n: "#0077b6"})
        st.plotly_chart(fig, use_container_width=True)

        # TABLEAU MENSUEL
        st.subheader(f"🗓️ Récapitulatif Mensuel : {annee_n} vs {annee_n1}")
        df_temp = df_filtre.copy()
        df_temp['Mois'] = df_temp.apply(lambda x: semaine_en_mois(x['Semaine'], x['Annee']), axis=1)
        recap = df_temp.groupby(['Mois', 'Annee'])['CA'].sum().unstack().fillna(0)
        if annee_n not in recap.columns: recap[annee_n] = 0.0
        if annee_n1 not in recap.columns: recap[annee_n1] = 0.0
        recap['Écart'] = recap[annee_n] - recap[annee_n1]
        recap['Evol %'] = (recap['Écart'] / recap[annee_n1] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        ordre_mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        recap = recap[[annee_n1, annee_n, 'Écart', 'Evol %']]
        recap = recap.reindex(ordre_mois).dropna(how='all')
        st.table(recap.style.format("{:.2f}"))

st.divider()

# --- ONGLETS ---
tab1, tab2, tab3 = st.tabs(["➕ Saisir", "🗑️ Supprimer", "🏪 Nouveau Magasin"])

with tab1:
   with tab1:
    # On initialise les mémoires de saisie si elles n'existent pas
    if "last_semaine" not in st.session_state:
        st.session_state.last_semaine = semaine_analyse
    if "last_annee" not in st.session_state:
        st.session_state.last_annee = annee_n

    with st.form("saisie_ca", clear_on_submit=False): # clear_on_submit=False pour garder les chiffres
        col1, col2, col3 = st.columns(3)
        
        # On utilise les valeurs gardées en mémoire
        s_i = col1.number_input("Semaine", 1, 53, value=st.session_state.last_semaine)
        a_i = col2.selectbox("Année de saisie", [2024, 2025, 2026], 
                             index=[2024, 2025, 2026].index(st.session_state.last_annee))
        ca_i = col3.number_input("Montant (€)", min_value=0.0)
        
        if st.form_submit_button("Enregistrer le chiffre"):
            # Enregistrement
            new_line = pd.DataFrame([{"Semaine": int(s_i), "Annee": int(a_i), "PointDeVente": pv, "Produit": prod, "CA": float(ca_i)}])
            df_updated = pd.concat([df, new_line], ignore_index=True)
            conn.update(data=df_updated)
            
            # ON GARDE EN MÉMOIRE ce qu'on vient de saisir avant de relancer
            st.session_state.last_semaine = int(s_i)
            st.session_state.last_annee = int(a_i)
            
            st.success(f"✅ Semaine {s_i} ({a_i}) enregistrée !")
            st.cache_data.clear()
            st.rerun()

with tab2:
    st.subheader("🗑️ Supprimer une saisie spécifique")
    col_s1, col_s2 = st.columns(2)
    s_del = col_s1.number_input("Semaine de l'erreur", 1, 53, value=semaine_analyse, key="s_del")
    a_del = col_s2.selectbox("Année de l'erreur", [2024, 2025, 2026], index=2, key="a_del")
    
    # On cherche les lignes correspondantes dans le DF global (df)
    lignes_trouvees = df[
        (df['PointDeVente'] == pv) & 
        (df['Produit'] == prod) & 
        (df['Semaine'] == s_del) & 
        (df['Annee'] == a_del)
    ]
    
    if not lignes_trouvees.empty:
        st.write("Saisies trouvées pour cette période :")
        for idx, row in lignes_trouvees.iterrows():
            col_info, col_btn = st.columns([3, 1])
            col_info.write(f"📍 {row['PointDeVente']} | 📦 {row['Produit']} | 📅 Sem {row['Semaine']} - {row['Annee']} | 💰 **{row['CA']} €**")
            if col_btn.button("Supprimer", key=f"btn_{idx}"):
                df_final = df.drop(idx)
                conn.update(data=df_final)
                st.success("Ligne supprimée !")
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("Aucune donnée trouvée pour cette semaine/année sur ce magasin.")

with tab3:
    with st.form("nouveau_pdv"):
        nouveau_nom = st.text_input("Nom du nouveau magasin")
        if st.form_submit_button("Créer le magasin"):
            if nouveau_nom and nouveau_nom not in liste_magasins:
                init_ligne = pd.DataFrame([{"Semaine": 1, "Annee": 2024, "PointDeVente": nouveau_nom, "Produit": "Pascalain", "CA": 0.0}])
                df_final = pd.concat([df, init_ligne], ignore_index=True)
                conn.update(data=df_final)
                st.success(f"Magasin '{nouveau_nom}' créé !")
                st.cache_data.clear()
                st.rerun()
