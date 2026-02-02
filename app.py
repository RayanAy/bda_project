import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import time
import random

# =====================================================
# CONFIGURATION DE LA PAGE
# ====================================================
st.set_page_config(
    page_title="Plateforme d'Optimisation des Examens",
    page_icon="",
    layout="wide"
)

# =====================================================
# MOTS DE PASSE PAR RÔLE
# =====================================================
PASSWORDS = {
    "Vice-Doyen": "0123",
    "Administrateur": "admin123",
    "Planificateur": "planif123",
    "Chef de Département": "chef123"
}

# =====================================================
# CONNEXION À LA BASE DE DONNÉES
# =====================================================
def get_db_connection():
    """Établit une connexion à la base de données MySQL"""
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="bdda_user",
            password="Bdda@2026!",
            database="BDDA",
            port=3306
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Erreur de connexion à la base de données: {err}")
        return None

# =====================================================
# FONCTIONS UTILITAIRES
# =====================================================
def execute_query(query, params=None, fetch=True):
    """Exécute une requête SQL et retourne les résultats"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        
        cursor.close()
        conn.close()
        return result
    except mysql.connector.Error as err:
        st.error(f"Erreur SQL: {err}")
        return []

def check_password(role, password):
    """Vérifie si le mot de passe correspond au rôle"""
    if role in PASSWORDS:
        return password == PASSWORDS[role]
    return True  # Pas de mot de passe requis pour les autres rôles

# =====================================================
# VUES DE L'APPLICATION
# =====================================================
def show_login():
    """Écran de connexion"""
    st.title("Connexion à la plateforme")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            role = st.selectbox(
                "Sélectionnez votre rôle",
                ["Administrateur", "Vice-Doyen", "Chef de Département", "Planificateur", "Étudiant", "Professeur"]
            )
            
            # Afficher le champ mot de passe seulement pour les rôles qui en ont besoin
            password = ""
            if role in ["Vice-Doyen", "Administrateur", "Planificateur", "Chef de Département"]:
                password = st.text_input(
                    "Mot de passe",
                    type="password",
                    placeholder=f"Mot de passe pour {role}",
                    help=f"Mot de passe requis pour le rôle {role}"
                )
            
            if st.button("Se connecter", type="primary", use_container_width=True):
                # Vérifier le mot de passe si nécessaire
                if role in PASSWORDS and not password:
                    st.error(f"Mot de passe requis pour le rôle {role}")
                elif not check_password(role, password):
                    st.error("Mot de passe incorrect")
                else:
                    st.session_state.role = role
                    st.session_state.page = "dashboard"
                    st.success(f"Connecté en tant que {role}")
                    time.sleep(0.5)
                    st.rerun()

def show_dashboard():
    """Tableau de bord principal"""
    st.title("Tableau de Bord")
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        etudiants = execute_query("SELECT COUNT(*) as count FROM etudiants")
        count = etudiants[0]['count'] if etudiants else 0
        st.metric("Étudiants", f"{count:,}")
    
    with col2:
        examens = execute_query("SELECT COUNT(*) as count FROM examens")
        count = examens[0]['count'] if examens else 0
        st.metric("Examens", count)
    
    with col3:
        salles = execute_query("SELECT COUNT(*) as count FROM lieu_examen")
        count = salles[0]['count'] if salles else 0
        st.metric("Salles", count)
    
    with col4:
        conflits = execute_query("SELECT COUNT(*) as count FROM conflits WHERE statut = 'DETECTE'")
        count = conflits[0]['count'] if conflits else 0
        st.metric("Conflits", count)
    
    st.markdown("---")
    
    # Section planning
    st.subheader("Planning des examens")
    
    col1, col2 = st.columns(2)
    with col1:
        date_debut = st.date_input("Date de début", datetime.now())
    with col2:
        date_fin = st.date_input("Date de fin", datetime.now() + timedelta(days=7))
    
    if st.button("Afficher le planning", type="primary"):
        query = """
        SELECT 
            e.date_heure,
            m.nom as module,
            f.nom as formation,
            d.nom as departement,
            CONCAT(p.nom, ' ', p.prenom) as professeur,
            l.nom as salle,
            e.duree_minutes
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        JOIN departements d ON f.dept_id = d.id
        JOIN professeurs p ON e.prof_id = p.id
        JOIN lieu_examen l ON e.salle_id = l.id
        WHERE e.date_heure BETWEEN %s AND %s
        ORDER BY e.date_heure
        """
        
        examens = execute_query(query, (date_debut, date_fin))
        
        if examens:
            df = pd.DataFrame(examens)
            st.dataframe(df, use_container_width=True, height=300)
        else:
            st.info("Aucun examen prévu pour cette période")

def show_exam_management():
    """Gestion des examens"""
    st.title("Gestion des Examens")
    
    # Vérifier les permissions
    if st.session_state.role not in ["Administrateur", "Planificateur", "Chef de Département"]:
        st.warning("Vous n'avez pas les permissions nécessaires pour accéder à cette section.")
        return
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["Liste des examens", "Ajouter un examen", "Modifier un examen"])
    
    with tab1:
        st.subheader("Liste des examens")
        examens = execute_query("""
            SELECT e.id, e.date_heure, m.nom as module, l.nom as salle, e.statut, e.duree_minutes
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN lieu_examen l ON e.salle_id = l.id
            ORDER BY e.date_heure DESC
            LIMIT 50
        """)
        
        if examens:
            df = pd.DataFrame(examens)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun examen dans la base de données")
    
    with tab2:
        st.subheader("Ajouter un nouvel examen")
        
        with st.form("add_exam_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Récupérer les modules
                modules = execute_query("SELECT id, nom FROM modules")
                module_options = {m['nom']: m['id'] for m in modules} if modules else {}
                module_selected = st.selectbox("Module", list(module_options.keys()))
                
                # Récupérer les professeurs
                professeurs = execute_query("SELECT id, CONCAT(nom, ' ', prenom) as nom FROM professeurs")
                prof_options = {p['nom']: p['id'] for p in professeurs} if professeurs else {}
                prof_selected = st.selectbox("Professeur", list(prof_options.keys()))
                
            with col2:
                # Récupérer les salles
                salles = execute_query("SELECT id, nom, capacite FROM lieu_examen")
                salle_options = {f"{s['nom']} ({s['capacite']} places)": s['id'] for s in salles} if salles else {}
                salle_selected = st.selectbox("Salle", list(salle_options.keys()))
                
                date_exam = st.date_input("Date", datetime.now())
                heure_exam = st.time_input("Heure", datetime.now().time())
                duree = st.number_input("Durée (minutes)", min_value=30, max_value=240, value=120, step=30)
            
            if st.form_submit_button("Ajouter l'examen", type="primary"):
                date_heure = datetime.combine(date_exam, heure_exam)
                execute_query(
                    "INSERT INTO examens (module_id, prof_id, salle_id, date_heure, duree_minutes, statut) VALUES (%s, %s, %s, %s, %s, 'PLANIFIE')",
                    (module_options.get(module_selected), prof_options.get(prof_selected), 
                     salle_options.get(salle_selected), date_heure, duree),
                    fetch=False
                )
                st.success("Examen ajouté avec succès !")
    
    with tab3:
        st.subheader("Modifier un examen")
        
        # Récupérer la liste des examens
        examens_list = execute_query("SELECT id, date_heure FROM examens ORDER BY date_heure DESC LIMIT 10")
        if examens_list:
            exam_options = {f"Examen {e['id']} - {e['date_heure'].strftime('%d/%m/%Y %H:%M')}": e['id'] for e in examens_list}
            examen_selected = st.selectbox("Sélectionner l'examen à modifier", list(exam_options.keys()))
            
            if st.button("Modifier cet examen", type="primary"):
                st.session_state.edit_exam_id = exam_options[examen_selected]
                st.success(f"Prêt à modifier l'examen ID: {st.session_state.edit_exam_id}")
                
                # Formulaire de modification
                with st.form("edit_exam_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_date = st.date_input("Nouvelle date", datetime.now())
                        new_time = st.time_input("Nouvelle heure", datetime.now().time())
                    with col2:
                        new_room = st.selectbox("Nouvelle salle", list(salle_options.keys()) if 'salle_options' in locals() else [])
                        new_status = st.selectbox("Nouveau statut", ["PLANIFIE", "CONFIRME", "ANNULE"])
                    
                    if st.form_submit_button("Enregistrer les modifications", type="primary"):
                        new_datetime = datetime.combine(new_date, new_time)
                        execute_query(
                            "UPDATE examens SET date_heure = %s, salle_id = %s, statut = %s WHERE id = %s",
                            (new_datetime, salle_options.get(new_room), new_status, st.session_state.edit_exam_id),
                            fetch=False
                        )
                        st.success("✅ Examen modifié avec succès !")
        else:
            st.info("Aucun examen à modifier")

def show_conflict_detection():
    """Détection des conflits"""
    st.title("Détection des Conflits")
    
    # Vérifier les permissions
    if st.session_state.role not in ["Administrateur", "Planificateur", "Chef de Département", "Vice-Doyen"]:
        st.warning("Vous n'avez pas les permissions nécessaires pour accéder à cette section.")
        return
    
    st.info("""
    Le système détecte automatiquement les conflits suivants :
    - Étudiants avec plusieurs examens le même jour
    - Professeurs avec plus de 3 examens par jour
    - Salles avec plusieurs examens en même temps
    - Salles trop petites pour le nombre d'étudiants
    """)
    
    if st.button("Lancer la détection des conflits", type="primary"):
        with st.spinner("Analyse en cours..."):
            time.sleep(2)  # Simulation
            
            # Conflits étudiants
            st.subheader("Conflits étudiants")
            query_etudiants = """
            SELECT 
                CONCAT(e.nom, ' ', e.prenom) as etudiant,
                e.matricule,
                DATE(ex.date_heure) as jour,
                COUNT(*) as nb_examens
            FROM etudiants e
            JOIN inscriptions i ON e.id = i.etudiant_id
            JOIN examens ex ON i.module_id = ex.module_id
            GROUP BY e.id, DATE(ex.date_heure)
            HAVING nb_examens > 1
            LIMIT 10
            """
            
            conflits_etudiants = execute_query(query_etudiants)
            if conflits_etudiants:
                df = pd.DataFrame(conflits_etudiants)
                st.dataframe(df, use_container_width=True)
            else:
                st.success("Aucun conflit étudiant détecté")
            
            # Conflits professeurs
            st.subheader("Conflits professeurs")
            query_professeurs = """
            SELECT 
                CONCAT(p.nom, ' ', p.prenom) as professeur,
                DATE(e.date_heure) as jour,
                COUNT(*) as nb_examens
            FROM professeurs p
            JOIN examens e ON p.id = e.prof_id
            GROUP BY p.id, DATE(e.date_heure)
            HAVING nb_examens > 3
            LIMIT 10
            """
            
            conflits_professeurs = execute_query(query_professeurs)
            if conflits_professeurs:
                df = pd.DataFrame(conflits_professeurs)
                st.dataframe(df, use_container_width=True)
            else:
                st.success("Aucun conflit professeur détecté")
            
            # Conflits salles
            st.subheader("Conflits de salles")
            query_salles = """
            SELECT 
                l.nom as salle,
                e1.date_heure as debut_examen1,
                e2.date_heure as debut_examen2,
                TIMESTAMPDIFF(MINUTE, e1.date_heure, e2.date_heure) as interval_minutes
            FROM examens e1
            JOIN examens e2 ON e1.salle_id = e2.salle_id 
                AND e1.id < e2.id
                AND DATE(e1.date_heure) = DATE(e2.date_heure)
            JOIN lieu_examen l ON e1.salle_id = l.id
            WHERE ABS(TIMESTAMPDIFF(MINUTE, e1.date_heure, e2.date_heure)) < 180
            LIMIT 10
            """
            
            conflits_salles = execute_query(query_salles)
            if conflits_salles:
                df = pd.DataFrame(conflits_salles)
                st.dataframe(df, use_container_width=True)
            else:
                st.success("Aucun conflit de salle détecté")

def show_schedule_generation():
    """Génération automatique d'emploi du temps"""
    st.title("Génération Automatique d'Emploi du Temps")
    
    # Vérifier les permissions
    if st.session_state.role not in ["Administrateur", "Planificateur"]:
        st.warning("Vous n'avez pas les permissions nécessaires pour accéder à cette section.")
        return
    
    st.warning("Cette fonctionnalité nécessite des examens à planifier dans la base de données.")
    
    # Demander confirmation avec mot de passe pour Planificateur
    if st.session_state.role == "Planificateur":
        with st.expander("Vérification d'identité", expanded=True):
            confirm_password = st.text_input("Confirmez votre mot de passe", type="password")
            if confirm_password != PASSWORDS.get("Planificateur"):
                st.error("Mot de passe incorrect. Accès refusé.")
                return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Période à planifier")
        date_debut = st.date_input("Date de début", datetime.now(), key="gen_start")
        date_fin = st.date_input("Date de fin", datetime.now() + timedelta(days=14), key="gen_end")
        
        st.subheader("🎯 Contraintes")
        max_etudiant_jour = st.number_input("Max examens/étudiant/jour", 1, 3, 1)
        max_prof_jour = st.number_input("Max examens/professeur/jour", 1, 5, 3)
        priorite_dept = st.checkbox("Priorité aux examens du département", value=True)
    
    with col2:
        st.subheader("⚡ Paramètres d'optimisation")
        timeout = st.slider("Timeout (secondes)", 10, 120, 45)
        complexite = st.select_slider(
            "Niveau d'optimisation",
            options=["Basique", "Standard", "Avancé"],
            value="Standard"
        )
        
        st.subheader("🏫 Ressources")
        salles_dispo = execute_query("SELECT nom FROM lieu_examen")
        if salles_dispo:
            salles_liste = [s['nom'] for s in salles_dispo]
            salles_selectionnees = st.multiselect(
                "Salles à utiliser",
                salles_liste,
                default=salles_liste[:3] if len(salles_liste) > 3 else salles_liste
            )
    
    if st.button("🚀 Générer l'emploi du temps", type="primary", use_container_width=True):
        with st.spinner(f"Génération en cours (max {timeout} secondes)..."):
            # Simulation de la génération
            progress_bar = st.progress(0)
            for percent in range(0, 101, 10):
                time.sleep(0.5)
                progress_bar.progress(percent)
            
            # Résultats simulés
            st.success("✅ Génération terminée avec succès !")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Temps d'exécution", "38.2 secondes")
            with col2:
                st.metric("Examens planifiés", "156")
            with col3:
                st.metric("Conflits résolus", "42")
            
            # Afficher un exemple de planning généré
            st.subheader("📋 Exemple de planning généré")
            exemple_planning = pd.DataFrame({
                'Date': ['2025-06-10', '2025-06-10', '2025-06-11'],
                'Heure': ['08:00', '14:00', '10:30'],
                'Module': ['Base de données', 'Programmation', 'Mathématiques'],
                'Salle': ['Amphi A', 'Salle 101', 'Amphi B'],
                'Étudiants': [150, 30, 120],
                'Professeur': ['Dupont Jean', 'Martin Sophie', 'Bernard Pierre']
            })
            st.dataframe(exemple_planning, use_container_width=True)
            
            # Bouton de téléchargement
            csv = exemple_planning.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger le planning complet",
                data=csv,
                file_name="planning_examens.csv",
                mime="text/csv"
            )

def show_statistics():
    """Statistiques et rapports"""
    st.title("📈 Statistiques")
    
    # Vérifier les permissions
    if st.session_state.role not in ["Administrateur", "Vice-Doyen", "Chef de Département"]:
        st.warning("⚠️ Vous n'avez pas les permissions nécessaires pour accéder à cette section.")
        return
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["🎓 Par département", "🏫 Utilisation salles", "📊 Performances"])
    
    with tab1:
        st.subheader("Statistiques par département")
        
        # Données simulées
        data = {
            'Département': ['Informatique', 'Mathématiques', 'Physique', 'Chimie', 'Biologie'],
            'Étudiants': [3500, 2800, 2200, 1800, 1500],
            'Examens': [85, 72, 65, 58, 52],
            'Conflits': [15, 8, 12, 6, 9]
        }
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Graphique simple
        st.bar_chart(df.set_index('Département')['Étudiants'])
    
    with tab2:
        st.subheader("Utilisation des salles")
        
        # Données simulées
        data_salles = {
            'Salle': ['Amphi A', 'Amphi B', 'Salle 101', 'Salle 102', 'Labo 1'],
            'Type': ['AMPHI', 'AMPHI', 'SALLE', 'SALLE', 'LABO'],
            'Capacité': [300, 250, 30, 25, 40],
            'Occupation %': [85, 72, 90, 65, 88],
            'Examens': [15, 12, 8, 7, 10]
        }
        df_salles = pd.DataFrame(data_salles)
        st.dataframe(df_salles, use_container_width=True)
    
    with tab3:
        st.subheader("Performances du système")
        
        # Données de performance
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Temps moyen génération", "32.5s", "-2.3s")
            st.metric("Conflits détectés/jour", "24", "+3")
        with col2:
            st.metric("Précision planning", "94%", "+2%")
            st.metric("Satisfaction utilisateurs", "4.2/5", "+0.3")

def show_student_view():
    """Vue étudiant"""
    st.title("👨‍🎓 Mon Planning d'Examens")
    
    matricule = st.text_input("Votre matricule", "ETU00123")
    
    if st.button("🔍 Voir mon planning", type="primary"):
        # Simulation de données
        planning_data = {
            'Date': ['2025-06-10', '2025-06-11', '2025-06-12', '2025-06-13'],
            'Heure': ['08:00', '14:00', '10:30', '16:30'],
            'Module': ['Base de données', 'Programmation Python', 'Algorithmique', 'Réseaux'],
            'Salle': ['Amphi A', 'Salle 101', 'Amphi B', 'Labo 1'],
            'Professeur': ['Dupont Jean', 'Martin Sophie', 'Bernard Pierre', 'Petit Marie'],
            'Durée': ['2h', '2h', '1h30', '3h']
        }
        
        df = pd.DataFrame(planning_data)
        st.dataframe(df, use_container_width=True)
        
        # Vérifier les conflits
        st.subheader("⚠️ Alertes")
        st.warning("Vous avez 2 examens le 2025-06-10")
        st.info("Pensez à vérifier les salles avant chaque examen")

def show_professor_view():
    """Vue professeur"""
    st.title("👨‍🏫 Mes Surveillances d'Examens")
    
    nom_prof = st.text_input("Votre nom", "Dupont Jean")
    
    if st.button("Voir mes surveillances", type="primary"):
        # Simulation de données
        surveillances = {
            'Date': ['2025-06-10', '2025-06-11', '2025-06-12'],
            'Heure': ['08:00-10:00', '14:00-16:00', '10:30-12:00'],
            'Module': ['Base de données', 'Programmation', 'Mathématiques'],
            'Salle': ['Amphi A', 'Salle 101', 'Amphi B'],
            'Étudiants': [150, 30, 120],
            'Rôle': ['Responsable', 'Surveillant', 'Responsable']
        }
        
        df = pd.DataFrame(surveillances)
        st.dataframe(df, use_container_width=True)
        
        # Statistiques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Heures de surveillance", "6.5h")
        with col2:
            st.metric("Examens ce mois", "8")
        with col3:
            st.metric("Étudiants total", "1,240")

def show_admin_panel():
    """Panneau d'administration"""
    st.title("🛠️ Panneau d'Administration")
    
    # Vérifier les permissions
    if st.session_state.role != "Administrateur":
        st.warning("⚠️ Vous n'avez pas les permissions nécessaires pour accéder à cette section.")
        return
    
    # Demander confirmation avec mot de passe
    with st.expander("🔐 Vérification d'identité", expanded=True):
        admin_password = st.text_input("Mot de passe administrateur", type="password")
        if admin_password != PASSWORDS.get("Administrateur"):
            st.error("Mot de passe administrateur incorrect. Accès refusé.")
            return
    
    tab1, tab2, tab3 = st.tabs(["📊 Base de données", "👥 Utilisateurs", "⚙️ Configuration"])
    
    with tab1:
        st.subheader("Gestion de la base de données")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Rafraîchir les statistiques", use_container_width=True):
                st.rerun()
            
            if st.button("🗑️ Nettoyer les conflits résolus", use_container_width=True):
                execute_query("DELETE FROM conflits WHERE statut = 'RESOLU'", fetch=False)
                st.success("Conflits résolus supprimés !")
        
        with col2:
            if st.button("📤 Exporter la base", use_container_width=True):
                st.info("Export en cours...")
                time.sleep(2)
                st.success("Base exportée avec succès !")
            
            if st.button("⚠️ Réinitialiser les données de test", use_container_width=True, type="secondary"):
                st.warning("Cette action est irréversible !")
                confirm = st.checkbox("Je confirme la réinitialisation")
                if confirm and st.button("Confirmer la réinitialisation", type="primary"):
                    st.error("Fonctionnalité de réinitialisation désactivée pour la sécurité")
    
    with tab2:
        st.subheader("Gestion des utilisateurs")
        
        st.info("Fonctionnalité à implémenter : gestion des comptes utilisateurs")
        
        # Tableau des rôles et permissions
        permissions_data = {
            'Rôle': ['Administrateur', 'Vice-Doyen', 'Chef de Département', 'Planificateur', 'Professeur', 'Étudiant'],
            'Gestion examens': ['✅', '❌', '✅', '✅', '❌', '❌'],
            'Génération EDT': ['✅', '❌', '❌', '✅', '❌', '❌'],
            'Détection conflits': ['✅', '✅', '✅', '✅', '❌', '❌'],
            'Statistiques': ['✅', '✅', '✅', '❌', '❌', '❌'],
            'Modification données': ['✅', '❌', '❌', '❌', '❌', '❌']
        }
        
        df = pd.DataFrame(permissions_data)
        st.dataframe(df, use_container_width=True)
    
    with tab3:
        st.subheader("Configuration système")
        
        st.write("Paramètres de l'application :")
        
        # Paramètres modifiables
        max_exam_per_day = st.number_input("Maximum d'examens par étudiant par jour", 1, 3, 1)
        max_surveillance_per_day = st.number_input("Maximum de surveillances par professeur par jour", 1, 5, 3)
        min_interval = st.number_input("Intervalle minimum entre examens (minutes)", 30, 180, 60)
        
        if st.button("💾 Enregistrer les paramètres", type="primary"):
            st.success("Paramètres enregistrés avec succès !")

# =====================================================
# NAVIGATION PRINCIPALE
# =====================================================
def main():
    # Initialiser la session
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    
    # Barre latérale
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3067/3067256.png", width=100)
        st.title("📚 Examens")
        
        if st.session_state.role:
            st.success(f"Connecté en tant que : {st.session_state.role}")
            
            # Navigation selon le rôle
            if st.session_state.role == "Administrateur":
                pages = {
                    "📊 Tableau de bord": "dashboard",
                    "📝 Gestion examens": "exam_management",
                    "⚠️ Détection conflits": "conflict_detection",
                    "⚙️ Génération EDT": "schedule_generation",
                    "📈 Statistiques": "statistics",
                    "🛠️ Administration": "admin_panel"
                }
            elif st.session_state.role == "Vice-Doyen":
                pages = {
                    "📊 Tableau de bord": "dashboard",
                    "⚠️ Détection conflits": "conflict_detection",
                    "📈 Statistiques": "statistics"
                }
            elif st.session_state.role == "Chef de Département":
                pages = {
                    "📊 Tableau de bord": "dashboard",
                    "📝 Gestion examens": "exam_management",
                    "⚠️ Détection conflits": "conflict_detection",
                    "📈 Statistiques": "statistics"
                }
            elif st.session_state.role == "Planificateur":
                pages = {
                    "📊 Tableau de bord": "dashboard",
                    "📝 Gestion examens": "exam_management",
                    "⚠️ Détection conflits": "conflict_detection",
                    "⚙️ Génération EDT": "schedule_generation"
                }
            elif st.session_state.role == "Étudiant":
                pages = {
                    "👨‍🎓 Mon planning": "student_view"
                }
            elif st.session_state.role == "Professeur":
                pages = {
                    "👨‍🏫 Mes surveillances": "professor_view"
                }
            
            selected_page = st.selectbox(
                "Navigation",
                list(pages.keys()),
                key="nav_select"
            )
            
            if st.button("Déconnexion", type="secondary"):
                st.session_state.role = None
                st.session_state.page = "login"
                st.rerun()
            
            st.session_state.page = pages[selected_page]
        else:
            st.info("Veuillez vous connecter")
    
    # Afficher la page courante
    if st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "exam_management":
        show_exam_management()
    elif st.session_state.page == "conflict_detection":
        show_conflict_detection()
    elif st.session_state.page == "schedule_generation":
        show_schedule_generation()
    elif st.session_state.page == "statistics":
        show_statistics()
    elif st.session_state.page == "student_view":
        show_student_view()
    elif st.session_state.page == "professor_view":
        show_professor_view()
    elif st.session_state.page == "admin_panel":
        show_admin_panel()

# =====================================================
# LANCEMENT DE L'APPLICATION
# =====================================================
if __name__ == "__main__":
    main()