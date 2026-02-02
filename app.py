import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import time

# =====================================================
# CONFIG PAGE
# =====================================================
st.set_page_config(
    page_title="Plateforme d'Optimisation des Examens",
    layout="wide"
)

st.write("✅ APP STARTED OK")

# =====================================================
# CONNEXION DB (LOCAL / CLOUD AUTO)
# =====================================================
def get_db_connection():
    try:
        if "DB_HOST" in st.secrets:
            return mysql.connector.connect(
                host=st.secrets["DB_HOST"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASSWORD"],
                database=st.secrets["DB_NAME"],
                port=st.secrets["DB_PORT"]
            )
        else:
            return mysql.connector.connect(
                host="127.0.0.1",
                user="bdda_user",
                password="Bdda@2026!",
                database="BDDA",
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
        c = execute_query("SELECT COUNT(*) c FROM etudiants")
        st.metric("Étudiants", c[0]["c"])

    with col2:
        c = execute_query("SELECT COUNT(*) c FROM examens")
        st.metric("Examens", c[0]["c"])

    with col3:
        c = execute_query("SELECT COUNT(*) c FROM professeurs")
        st.metric("Professeurs", c[0]["c"])

    with col4:
        c = execute_query("SELECT COUNT(*) c FROM conflits WHERE statut='DETECTE'")
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
        SELECT e.date_heure, m.nom module, f.nom formation, l.nom salle, e.duree_minutes
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        JOIN lieu_examen l ON e.salle_id = l.id
        WHERE e.date_heure BETWEEN %s AND %s
        ORDER BY e.date_heure
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
