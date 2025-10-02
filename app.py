
import streamlit as st

import db_functions

st.set_page_config(
    page_title="Turbo Tool",
    page_icon="📊",
    layout="wide",   # <<--- das macht es breit
    initial_sidebar_state="expanded"  # optional
)



db_functions.create_user_table()
db_functions.create_in_table()
db_functions.create_out_table()
db_functions.create_cols_map_in_table()
db_functions.create_cols_map_out_table()

#Page Titel

PAGE_LOGIN = "Login"
PAGE_TURBO_TOOL = "Turbo Tool"
PAGE_COLS_MAPPING = "Cols Mapping"
PAGE_DATEN_LOESCHEN = "Daten löschen"
PAGE_USER_MANAGEMEMT = "User-Management"

pages = {
    "": [
        st.Page("login.py", title=PAGE_LOGIN),
        st.Page("home.py", title=PAGE_TURBO_TOOL),
        #st.Page("cols_mapping.py", title="Cols Mapping"),
        st.Page("delete_daten.py", title=PAGE_DATEN_LOESCHEN),
        st.Page("user_administration.py", title=PAGE_USER_MANAGEMEMT),
    ]
}

if 'password' not in st.session_state:
    st.session_state.password = ''

def changer():
    print(st.session_state.password)

@st.dialog("Login")
def login():
    e_mail = st.text_input(label="E-Mail", key='email')

    passwort = st.text_input(label="Passwort", type='password', on_change=changer, key='password')
    if len(st.session_state.password) < 8:
        st.markdown('Passwort muss mindestens 8 Zeichen lang sein')
    if st.button("Einloggen"):
        st.rerun()

sideb = st.sidebar
login_button = sideb.button("Einloggen")
if login_button:
    login()


pg = st.navigation(pages)
pg.run()
