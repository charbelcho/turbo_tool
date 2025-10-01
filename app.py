
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

PAGE_TURBO_TOOL = "Turbo Tool"
PAGE_COLS_MAPPING = "Cols Mapping"
PAGE_DATEN_LOESCHEN = "Daten löschen"
PAGE_USER_MANAGEMEMT = "User-Management"

pages = {
    "": [
        st.Page("home.py", title=PAGE_TURBO_TOOL),
        #st.Page("cols_mapping.py", title="Cols Mapping"),
        st.Page("delete_daten.py", title=PAGE_DATEN_LOESCHEN),
        st.Page("user_administration.py", title=PAGE_USER_MANAGEMEMT),
    ]
}

pg = st.navigation(pages)
pg.run()
