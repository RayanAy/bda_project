import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta

# ===============================
# CONFIG PAGE
# ===============================
st.set_page_config(page_title="Plateforme Optimisation Examens", layout="wide")
st.write("✅ APP STARTED OK")

# ===============================
# DB CONNECTION
# ===============================
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="sql7.freesqldatabase.com",
            user="sql7816114",
            password="uHDuktK7C1",
            database="sql7816114",
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
    if fetch:
        result = cursor.fetchall()
    else:
        conn.commit()
        result = None
    cursor.close()
    conn.close()
    return result

# ===============================
# AUTH
# ===============================
PASSWORDS = {
    "Administrateur": "admin123",
    "Vice-Doyen": "0123",
    "Chef de Département": "chef123",
    "Planificateur": "planif123"
}

def check_password(role, pwd):
    return PASSWORDS.get(role) == pwd

# ===============================
# LOGIN
# ===============================
def login():
    st.title("🔐 Connexion")
    role = st.selectbox(
        "Rôle",
        ["Administrateur", "Vice-Doyen", "Doyen", "Chef de Département", "Planificateur", "Étudiant", "Professeur"]
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

# ===============================
# DASHBOARD (Consultation générale)
# ===============================
def dashboard():
    st.title("📊 Tableau de bord général")
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

# ===============================
# PLANNING
# ===============================
# ===============================
# PLANNING (TOUS LES EXAMENS)
# ===============================
def planning():
    st.title("🗓️ Planning des examens")

    role = st.session_state.role
    user_id = st.text_input("Votre matricule / ID") if role in ["Étudiant", "Professeur"] else None

    if st.button("Afficher le planning"):
        query = """
        SELECT e.id, m.nom AS module, CONCAT(p.nom) AS prof, l.nom AS salle, e.date_heure, e.duree_minutes
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN professeurs p ON e.prof_id = p.id
        JOIN lieu_examen l ON e.salle_id = l.id
        """

        params = []

        # Étudiant voit seulement ses examens
        if role == "Étudiant" and user_id:
            query += " WHERE e.module_id IN (SELECT module_id FROM inscriptions WHERE etudiant_id=%s)"
            params.append(user_id)

        # Professeur voit seulement ses surveillances
        elif role == "Professeur" and user_id:
            query += " WHERE e.prof_id=%s"
            params.append(user_id)

        query += " ORDER BY e.date_heure"
        data = execute_query(query, tuple(params))
        st.dataframe(pd.DataFrame(data), use_container_width=True)


# ===============================
# AJOUT EXAMEN (Planificateur uniquement)
# ===============================
def ajouter_examen():
    if st.session_state.role != "Planificateur":
        st.warning("❌ Accès réservé au Planificateur")
        return

    st.title("➕ Ajouter un examen")
    modules = execute_query("SELECT id, nom FROM modules")
    profs = execute_query("SELECT id, nom FROM professeurs")
    salles = execute_query("SELECT id, nom, capacite FROM lieu_examen")

    module = st.selectbox("Module", [m['nom'] for m in modules])
    prof = st.selectbox("Professeur", [p['nom'] for p in profs])
    salle = st.selectbox("Salle", [f"{s['nom']} ({s['capacite']} places)" for s in salles])
    date_exam = st.date_input("Date")
    heure_exam = st.time_input("Heure")
    duree = st.number_input("Durée (minutes)", min_value=30, max_value=240, value=120, step=30)

    if st.button("Ajouter l'examen"):
        dt = datetime.combine(date_exam, heure_exam)
        # Vérification capacité salle
        nb_etudiants = execute_query("SELECT COUNT(*) AS c FROM inscriptions WHERE module_id=%s",
                                    (modules[[m['nom'] for m in modules].index(module)]['id'],))[0]['c']
        salle_cap = salles[[s['nom'] for s in salles].index(salle.split(" (")[0])]['capacite']
        if nb_etudiants > salle_cap:
            st.error("❌ Capacité salle insuffisante")
            return

        # Vérification max 3 examens/jour prof
        prof_id = profs[[p['nom'] for p in profs].index(prof)]['id']
        prof_jour = execute_query("SELECT COUNT(*) AS c FROM examens WHERE prof_id=%s AND DATE(date_heure)=%s",
                                  (prof_id, dt.date()))[0]['c']
        if prof_jour >= 3:
            st.error("❌ Professeur déjà assigné à 3 examens ce jour")
            return

        # Vérification max 1 examen/jour étudiants
        conflicts = execute_query("""
            SELECT COUNT(*) AS c
            FROM examens e
            JOIN inscriptions i ON e.module_id=i.module_id
            WHERE i.etudiant_id IN (SELECT etudiant_id FROM inscriptions WHERE module_id=%s)
            AND DATE(e.date_heure)=%s
        """, (modules[[m['nom'] for m in modules].index(module)]['id'], dt.date()))[0]['c']
        if conflicts > 0:
            st.error("❌ Certains étudiants ont déjà un examen ce jour")
            return

        # Ajout
        execute_query("""
            INSERT INTO examens (module_id, prof_id, salle_id, date_heure, duree_minutes)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            modules[[m['nom'] for m in modules].index(module)]['id'],
            prof_id,
            salles[[s['nom'] for s in salles].index(salle.split(" (")[0])]['id'],
            dt,
            duree
        ), fetch=False)
        st.success("✅ Examen ajouté avec succès !")

# ===============================
# MAIN
# ===============================
def main():
    if "role" not in st.session_state:
        st.session_state.role = None
        st.session_state.page = "login"

    with st.sidebar:
        st.title("📚 BDDA")
        if st.session_state.role:
            st.success(f"Rôle : {st.session_state.role}")
            pages = ["Dashboard", "Planning"]
            if st.session_state.role == "Planificateur":
                pages.append("Ajouter examen")
            page = st.selectbox("Navigation", pages)
            if st.button("Déconnexion"):
                st.session_state.clear()
                st.rerun()
            st.session_state.page = page.lower()
        else:
            st.info("Veuillez vous connecter")

    # Pages
    if st.session_state.page == "login":
        login()
    elif st.session_state.page == "dashboard":
        dashboard()
    elif st.session_state.page == "planning":
        planning()
    elif st.session_state.page == "ajouter examen":
        ajouter_examen()

if __name__ == "__main__":
    main()
