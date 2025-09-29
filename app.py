
import streamlit as st

import db_functions

st.set_page_config(
    page_title="Turbo Tool",
    page_icon="📊",
    layout="wide",   # <<--- das macht es breit
    initial_sidebar_state="expanded"  # optional
)

db_functions.create_in_table()
db_functions.create_out_table()
db_functions.create_cols_map_in_table()
db_functions.create_cols_map_out_table()

pages = {
    "": [
        st.Page("home.py", title="Turbo Tool"),
        #st.Page("cols_mapping.py", title="Cols Mapping"),
        st.Page("delete_daten.py", title="Daten löschen"),
    ]
}

pg = st.navigation(pages)
pg.run()
