'''
import streamlit as st 
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta

# =====================================================
# CONFIG PAGE
# =====================================================
st.set_page_config(
    page_title="Plateforme d'Optimisation des Examens",
    layout="wide"
)

st.write("✅ APP STARTED OK")

# =====================================================
# CONNEXION DB (CLOUD FREESQL)
# =====================================================
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="sql7.freesqldatabase.com",
            user="sql7816017",
            password="7Ml48zfqWV",
            database="sql7816017",  # <-- utiliser la base FreeSQL réelle
            port=3306
        )
    except mysql.connector.Error as e:
        st.error(f"❌ Erreur DB : {e}")
        return None



def execute_query(query, params=None, fetch=True):
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    result = cursor.fetchall() if fetch else conn.commit()
    cursor.close()
    conn.close()
    return result or []

# =====================================================
# AUTH
# =====================================================
PASSWORDS = {
    "Administrateur": "admin123",
    "Vice-Doyen": "0123",
    "Chef de Département": "chef123",
    "Planificateur": "planif123"
}

def check_password(role, pwd):
    return PASSWORDS.get(role) == pwd

# =====================================================
# LOGIN
# =====================================================
def login():
    st.title("🔐 Connexion")
    role = st.selectbox(
        "Rôle",
        ["Administrateur", "Vice-Doyen", "Chef de Département", "Planificateur", "Étudiant", "Professeur"]
    )
    pwd = ""
    if role in PASSWORDS:
        pwd = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if role in PASSWORDS and not check_password(role, pwd):
            st.error("Mot de passe incorrect")
        else:
            st.session_state.role = role
            st.session_state.page = "dashboard"
            st.success(f"Connecté en tant que {role}")
            st.rerun()

# =====================================================
# DASHBOARD
# =====================================================
def dashboard():
    st.title("📊 Tableau de bord")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        c = execute_query("SELECT COUNT(*) AS c FROM etudiants")
        st.metric("Étudiants", c[0]["c"])

    with col2:
        c = execute_query("SELECT COUNT(*) AS c FROM examens")
        st.metric("Examens", c[0]["c"])

    with col3:
        c = execute_query("SELECT COUNT(*) AS c FROM professeurs")
        st.metric("Professeurs", c[0]["c"])

    with col4:
        c = execute_query("SELECT COUNT(*) AS c FROM conflits WHERE statut='DETECTE'")
        st.metric("Conflits actifs", c[0]["c"])

# =====================================================
# PLANNING
# =====================================================
def planning():
    st.title("🗓️ Planning des examens")
    d1 = st.date_input("Date début", datetime.now())
    d2 = st.date_input("Date fin", datetime.now() + timedelta(days=7))
    if st.button("Afficher"):
        q = """
        SELECT *
        FROM planning_examens
        WHERE date_heure BETWEEN %s AND %s
        ORDER BY date_heure
        """
        data = execute_query(q, (d1, d2))
        st.dataframe(pd.DataFrame(data), use_container_width=True)

# =====================================================
# CONFLITS
# =====================================================
def conflits():
    st.title("⚠️ Conflits détectés")
    q = """
    SELECT c.type, c.description, c.severite, e.date_heure
    FROM conflits c
    JOIN examens e ON c.examen_id = e.id
    WHERE c.statut='DETECTE'
    """
    st.dataframe(pd.DataFrame(execute_query(q)), use_container_width=True)

# =====================================================
# MAIN
# =====================================================
def main():
    if "role" not in st.session_state:
        st.session_state.role = None
        st.session_state.page = "login"

    with st.sidebar:
        st.title("📚 BDDA")
        if st.session_state.role:
            st.success(st.session_state.role)
            page = st.selectbox(
                "Navigation",
                ["Dashboard", "Planning", "Conflits"]
            )
            if st.button("Déconnexion"):
                st.session_state.clear()
                st.rerun()
            st.session_state.page = page.lower()
        else:
            st.info("Veuillez vous connecter")

    if st.session_state.page == "login":
        login()
    elif st.session_state.page == "dashboard":
        dashboard()
    elif st.session_state.page == "planning":
        planning()
    elif st.session_state.page == "conflits":
        conflits()

if __name__ == "__main__":
    main()
'''
# ==============================
# Imports
# ==============================
import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import time
import random

# ==============================
# Configuration de la page
# ==============================
st.set_page_config(
    page_title="Plateforme d'Optimisation des Examens",
    layout="wide"
)
st.write("✅ APP STARTED OK")

# ==============================
# Mots de passe par rôle
# ==============================
PASSWORDS = {
    "Vice-Doyen": "0123",
    "Administrateur": "admin123",
    "Planificateur": "planif123",
    "Chef de Département": "chef123"
}

# ==============================
# Connexion à la base de données FreeSQL
# ==============================
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="sql7.freesqldatabase.com",
            user="sql7816017",
            password="7Ml48zfqWV",
            database="sql7816017",
            port=3306
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"❌ Erreur DB: {err}")
        return None

def execute_query(query, params=None, fetch=True):
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
        st.error(f"❌ Erreur SQL: {err}")
        return []

def check_password(role, password):
    if role in PASSWORDS:
        return password == PASSWORDS[role]
    return True

# ==============================
# Fonctions principales
# ==============================

def show_login():
    st.title("🔐 Connexion")
    role = st.selectbox(
        "Sélectionnez votre rôle",
        ["Administrateur", "Vice-Doyen", "Chef de Département", "Planificateur", "Étudiant", "Professeur"]
    )
    password = ""
    if role in PASSWORDS:
        password = st.text_input("Mot de passe", type="password", placeholder=f"Mot de passe pour {role}")
    if st.button("Se connecter", type="primary"):
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

# -------- Dashboard --------
def show_dashboard():
    st.title("📊 Tableau de bord")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        etudiants = execute_query("SELECT COUNT(*) as count FROM etudiants")
        count = etudiants[0]['count'] if etudiants else 0
        st.metric("Étudiants", count)
    with col2:
        examens = execute_query("SELECT COUNT(*) as count FROM examens")
        count = examens[0]['count'] if examens else 0
        st.metric("Examens", count)
    with col3:
        profs = execute_query("SELECT COUNT(*) as count FROM professeurs")
        count = profs[0]['count'] if profs else 0
        st.metric("Professeurs", count)
    with col4:
        conflits = execute_query("SELECT COUNT(*) as count FROM conflits WHERE statut='DETECTE'")
        count = conflits[0]['count'] if conflits else 0
        st.metric("Conflits actifs", count)

# -------- Gestion des examens --------
def show_exam_management():
    st.title("📝 Gestion des examens")
    if st.session_state.role not in ["Administrateur", "Planificateur", "Chef de Département"]:
        st.warning("Vous n'avez pas les permissions nécessaires.")
        return

    tab1, tab2, tab3 = st.tabs(["Liste des examens", "Ajouter un examen", "Modifier un examen"])

    # Liste des examens
    with tab1:
        examens = execute_query("""
            SELECT e.id, e.date_heure, m.nom as module, l.nom as salle, e.statut, e.duree_minutes 
            FROM examens e 
            JOIN modules m ON e.module_id = m.id 
            JOIN lieu_examen l ON e.salle_id = l.id 
            ORDER BY e.date_heure DESC LIMIT 50
        """)
        if examens:
            df = pd.DataFrame(examens)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun examen dans la base de données")

    # Ajouter un examen
    with tab2:
        st.subheader("Ajouter un nouvel examen")
        with st.form("add_exam_form"):
            col1, col2 = st.columns(2)
            with col1:
                modules = execute_query("SELECT id, nom FROM modules")
                module_options = {m['nom']: m['id'] for m in modules} if modules else {}
                module_selected = st.selectbox("Module", list(module_options.keys()))
                profs = execute_query("SELECT id, CONCAT(nom,' ',prenom) as nom FROM professeurs")
                prof_options = {p['nom']: p['id'] for p in profs} if profs else {}
                prof_selected = st.selectbox("Professeur", list(prof_options.keys()))
            with col2:
                salles = execute_query("SELECT id, nom, capacite FROM lieu_examen")
                salle_options = {f"{s['nom']} ({s['capacite']} places)": s['id'] for s in salles} if salles else {}
                salle_selected = st.selectbox("Salle", list(salle_options.keys()))
                date_exam = st.date_input("Date", datetime.now())
                heure_exam = st.time_input("Heure", datetime.now().time())
                duree = st.number_input("Durée (minutes)", min_value=30, max_value=240, value=120, step=30)

            if st.form_submit_button("Ajouter l'examen"):
                date_heure = datetime.combine(date_exam, heure_exam)
                execute_query(
                    "INSERT INTO examens (module_id, prof_id, salle_id, date_heure, duree_minutes, statut) VALUES (%s,%s,%s,%s,%s,'PLANIFIE')",
                    (module_options.get(module_selected), prof_options.get(prof_selected), salle_options.get(salle_selected), date_heure, duree),
                    fetch=False
                )
                st.success("Examen ajouté avec succès !")

    # Modifier un examen
    with tab3:
        st.subheader("Modifier un examen")
        examens_list = execute_query("SELECT id, date_heure FROM examens ORDER BY date_heure DESC LIMIT 10")
        if examens_list:
            exam_options = {f"Examen {e['id']} - {e['date_heure'].strftime('%d/%m/%Y %H:%M')}": e['id'] for e in examens_list}
            examen_selected = st.selectbox("Sélectionner l'examen à modifier", list(exam_options.keys()))
            if st.button("Modifier cet examen"):
                st.session_state.edit_exam_id = exam_options[examen_selected]
                st.success(f"Prêt à modifier l'examen ID: {st.session_state.edit_exam_id}")
            with st.form("edit_exam_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_date = st.date_input("Nouvelle date", datetime.now())
                    new_time = st.time_input("Nouvelle heure", datetime.now().time())
                with col2:
                    new_room = st.selectbox("Nouvelle salle", list(salle_options.keys()) if 'salle_options' in locals() else [])
                    new_status = st.selectbox("Nouveau statut", ["PLANIFIE", "CONFIRME", "ANNULE"])
                if st.form_submit_button("Enregistrer modifications"):
                    new_datetime = datetime.combine(new_date, new_time)
                    execute_query(
                        "UPDATE examens SET date_heure=%s, salle_id=%s, statut=%s WHERE id=%s",
                        (new_datetime, salle_options.get(new_room), new_status, st.session_state.edit_exam_id),
                        fetch=False
                    )
                    st.success("✅ Examen modifié avec succès !")
        else:
            st.info("Aucun examen à modifier")

# -------- Détection des conflits --------
def show_conflict_detection():
    st.title("⚠️ Détection des conflits")
    if st.session_state.role not in ["Administrateur", "Planificateur", "Chef de Département", "Vice-Doyen"]:
        st.warning("Vous n'avez pas les permissions nécessaires.")
        return

    if st.button("Lancer la détection des conflits"):
        with st.spinner("Analyse en cours..."):
            time.sleep(1)  # Simulation

        st.subheader("Conflits étudiants")
        query_etudiants = """
            SELECT CONCAT(e.nom,' ',e.prenom) as etudiant, e.matricule, DATE(ex.date_heure) as jour, COUNT(*) as nb_examens
            FROM etudiants e
            JOIN inscriptions i ON e.id = i.etudiant_id
            JOIN examens ex ON i.module_id = ex.module_id
            GROUP BY e.id, DATE(ex.date_heure)
            HAVING nb_examens > 1 LIMIT 10
        """
        conflits_etudiants = execute_query(query_etudiants)
        if conflits_etudiants:
            st.dataframe(pd.DataFrame(conflits_etudiants), use_container_width=True)
        else:
            st.success("Aucun conflit étudiant détecté")

        st.subheader("Conflits professeurs")
        query_professeurs = """
            SELECT CONCAT(p.nom,' ',p.prenom) as professeur, DATE(e.date_heure) as jour, COUNT(*) as nb_examens
            FROM professeurs p
            JOIN examens e ON p.id = e.prof_id
            GROUP BY p.id, DATE(e.date_heure)
            HAVING nb_examens > 3 LIMIT 10
        """
        conflits_profs = execute_query(query_professeurs)
        if conflits_profs:
            st.dataframe(pd.DataFrame(conflits_profs), use_container_width=True)
        else:
            st.success("Aucun conflit professeur détecté")

        st.subheader("Conflits salles")
        query_salles = """
            SELECT l.nom as salle, e1.date_heure as debut1, e2.date_heure as debut2, TIMESTAMPDIFF(MINUTE,e1.date_heure,e2.date_heure) as interval_min
            FROM examens e1
            JOIN examens e2 ON e1.salle_id = e2.salle_id AND e1.id<e2.id AND DATE(e1.date_heure)=DATE(e2.date_heure)
            JOIN lieu_examen l ON e1.salle_id=l.id
            WHERE ABS(TIMESTAMPDIFF(MINUTE,e1.date_heure,e2.date_heure))<180 LIMIT 10
        """
        conflits_salles = execute_query(query_salles)
        if conflits_salles:
            st.dataframe(pd.DataFrame(conflits_salles), use_container_width=True)
        else:
            st.success("Aucun conflit de salle détecté")

# -------- Les autres fonctions (planning, schedule, statistics, student_view, professor_view, admin_panel) --------
# Tu peux copier les fonctions de ton code actuel sans modification
# Elles suivent exactement le même modèle que show_dashboard, show_exam_management, show_conflict_detection

# ==============================
# Navigation principale
# ==============================
def main():
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'page' not in st.session_state:
        st.session_state.page = "login"

    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3067/3067256.png", width=100)
        st.title("📚 Examens")
        if st.session_state.role:
            st.success(f"Connecté en tant que : {st.session_state.role}")
            pages = {
                "Administrateur": ["📊 Tableau de bord","📝 Gestion examens","⚠️ Détection conflits","⚙️ Génération EDT","📈 Statistiques","🛠️ Administration"],
                "Vice-Doyen": ["📊 Tableau de bord","⚠️ Détection conflits","📈 Statistiques"],
                "Chef de Département": ["📊 Tableau de bord","📝 Gestion examens","⚠️ Détection conflits","📈 Statistiques"],
                "Planificateur": ["📊 Tableau de bord","📝 Gestion examens","⚠️ Détection conflits","⚙️ Génération EDT"],
                "Étudiant": ["👨‍🎓 Mon planning"],
                "Professeur": ["👨‍🏫 Mes surveillances"]
            }
            selected_page = st.selectbox("Navigation", pages.get(st.session_state.role, []))
            if st.button("Déconnexion"):
                st.session_state.clear()
                st.rerun()
            st.session_state.page = selected_page
        else:
            st.info("Veuillez vous connecter")

    # Afficher la page
    if st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "exam_management":
        show_exam_management()
    elif st.session_state.page == "conflict_detection":
        show_conflict_detection()
    # elif ... ajoute ici toutes les autres pages comme schedule_generation, statistics, student_view, professor_view, admin_panel

# ==============================
# Lancement de l'application
# ==============================
if __name__ == "__main__":
    main()


