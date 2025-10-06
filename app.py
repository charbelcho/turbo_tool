import numpy as np
import pandas as pd
import streamlit as st

import db_functions
from argon2 import PasswordHasher

from user import User

ph = PasswordHasher()

st.set_page_config(
    page_title="Turbo Tool",
    page_icon="📊",
    layout="wide",  # <<--- das macht es breit
    initial_sidebar_state="expanded"  # optional
)

db_functions.create_user_table()
db_functions.create_in_table()
db_functions.create_out_table()
db_functions.create_cols_map_in_table()
db_functions.create_cols_map_out_table()




def require_login():
    if not st.session_state.logged_in:
        st.warning("Bitte zuerst einloggen.")
        st.switch_page("startseite.py")


def validate_mail_password(email, passwort):
    users = db_functions.select_where(table='user', col_value={'email': email}, connect_to='user')
    if users.empty:
        msg = "Kein Benutzer mit dieser Mail vergeben"
        return False, msg, None
    else:
        try:
            ph.verify(users.iloc[0]['password'], passwort)
            msg = "✅ Passwort korrekt"
            return True, msg, User(users.iloc[0])
        except Exception:
            msg = "❌ Falsches Passwort"
            return False, msg, None


def validate_registration(email, vorname, nachname, passwort, passwort_wiederholen):
    users = db_functions.select_where(table='user', col_value={'email': email}, connect_to='user')
    if not users.empty:
        msg = "Bereits ein Benutzer mit dieser Mail vergeben"
        return False, msg
    elif len(passwort) < 8:
        msg = "Passwort muss mindestens 8 Zeichen lang sein"
        return False, msg
    elif passwort != passwort_wiederholen:
        msg = "Passwörter stimmen nicht überein"
        return False, msg
    elif not '@' in email:
        msg = "Dies ist keine gültige E-Mail"
        return False, msg
    else:
        try:
            users_db = db_functions.statement("select count(*) as count from user", connect_to='user')
            d = {'vorname': [vorname], 'nachname': [nachname], 'email': [email], 'password': [ph.hash(passwort)],
                 'profil': ['Admin' if users_db.iloc[0]['count'] == 0 else 'User']}
            data = pd.DataFrame(data=d)
            registration_successful = db_functions.insert(table='user', data=data, connect_to='user')
            if registration_successful:
                msg = "✅ Registrierung erfolgreich"
                return True, msg
        except Exception:
            msg = "❌ Fehler bei Registrierung"
            return False, msg


def validate_edit_passwort(email, passwort, passwort_wiederholen):
    if not 'logged_in' in st.session_state:
        msg = 'Kein User eingeloggt'
        return False, msg
    elif len(passwort) < 8:
        msg = "Passwort muss mindestens 8 Zeichen lang sein"
        return False, msg
    elif passwort != passwort_wiederholen:
        msg = "Passwörter stimmen nicht überein"
        return False, msg
    else:
        try:
            user_data = db_functions.select_where(table='user', col_value={'email': email}, cols=['user_index'],
                                                  connect_to='user')
            user_index = user_data.iloc[0]['user_index'] if not user_data.empty else np.nan
            pwd_change_successful = db_functions.update_where(
                table='user',
                cols_update={'password': ph.hash(passwort)},
                col_search_value={'user_index': user_index},
                connect_to='user')
            if pwd_change_successful:
                msg = "✅ Passwort geändert"
                return True, msg
        except Exception:
            msg = "❌ Passwort konnte nicht geändert werden"
            return False, msg


@st.dialog("Login")
def login():
    email = st.text_input(label="E-Mail", key='email')
    passwort = st.text_input(label="Passwort", type='password', key='password')

    if st.button("Einloggen"):
        login_successful, msg, user = validate_mail_password(email, passwort)
        if login_successful:
            st.success(msg)
            st.session_state.logged_in = True
            st.session_state.logged_in_user = user
            st.switch_page('home.py')
            st.rerun()
        else:
            st.error(msg)
            st.session_state.logged_in = False


@st.dialog("Registrieren")
def register():
    email = st.text_input(label="E-Mail", key='email')
    vorname = st.text_input(label="Vorname", key='vorname')
    nachname = st.text_input(label="Nachname", key='nachname')
    passwort = st.text_input(label="Passwort", type='password', key='password')
    passwort_wiederholen = st.text_input(label="Passwort wiederholen", type='password', key='password_wiederholen')
    if st.button("Registrieren"):
        register_successful, msg = validate_registration(email, vorname, nachname, passwort, passwort_wiederholen)
        if register_successful:
            st.success(msg)
            st.switch_page('home.py')
            st.rerun()
        else:
            st.error(msg)


@st.dialog("Passwort ändern")
def change_pwd():
    st.session_state.change_pwd_email = st.session_state.logged_in_user.email
    email = st.text_input(label="E-Mail", key='change_pwd_email', disabled=True, )
    passwort = st.text_input(label="Neues Passwort", type='password', key='password')
    passwort_wiederholen = st.text_input(label="Passwort wiederholen", type='password', key='password_wiederholen')
    if st.button("Passwort ändern"):
        pwd_change_successful, msg = validate_edit_passwort(email, passwort, passwort_wiederholen)
        if pwd_change_successful:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

def logout():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False


sideb = st.sidebar

if not st.session_state.logged_in:
    login_button = sideb.button("Einloggen")
    if login_button:
        login()

    register_button = sideb.button("Registrieren")
    if register_button:
        register()

if st.session_state.logged_in:
    logout_button = sideb.button("Ausloggen")
    if logout_button:
        logout()

    change_pwd_button = sideb.button("Passwort ändern")
    if change_pwd_button:
        change_pwd()


# Page Titel

PAGE_STARTSEITE = "Startseite"
PAGE_TURBO_TOOL = "Turbo Tool"
PAGE_COLS_MAPPING = "Cols Mapping"
PAGE_DATEN_LOESCHEN = "Daten löschen"
PAGE_USER_MANAGEMEMT = "User-Management"

pages = {
    "": [
        st.Page("startseite.py", title=PAGE_STARTSEITE),
        st.Page("home.py", title=PAGE_TURBO_TOOL),
        # st.Page("cols_mapping.py", title="Cols Mapping"),
        st.Page("delete_daten.py", title=PAGE_DATEN_LOESCHEN),
        st.Page("user_administration.py", title=PAGE_USER_MANAGEMEMT),
    ]
}

pg = st.navigation(pages)
pg.run()
