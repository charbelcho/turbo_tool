import pandas as pd
import streamlit as st
import db_functions
from app import PAGE_USER_MANAGEMEMT


class Profile:
    SUPER_USER = "Super User"
    ADMIN = "Admin"
    USER = "User"
    WRITE = "Write"
    VIEW = "View"


def after_speichern(successful):
    if successful:
        st.success('Die Daten wurden erfolgreich gespeichert')
        st.session_state.user = db_functions.select(table='user', connect_to='user')
    else:
        st.error('Fehler beim Speichern der Daten')


if 'user' not in st.session_state:
    st.session_state.user = db_functions.select(table='user', connect_to='user')


st.title(PAGE_USER_MANAGEMEMT)

user_df = st.data_editor(
    data=st.session_state.user,
    column_config={
        "profil": st.column_config.SelectboxColumn(
            options=[Profile.ADMIN, Profile.USER, Profile.WRITE, Profile.VIEW]
        )
    },
    disabled=['user_index'],
    num_rows='dynamic',
    # on_change=changer,
    key='user_editor'
)


speichern = st.button(f'Speichern', use_container_width=True)
if speichern:
    if not (bool(st.session_state.user_editor['edited_rows']) or len(
            st.session_state.user_editor['added_rows']) == 0 or len(
            st.session_state.user_editor['deleted_rows']) == 0):
        st.info('Daten unverändert.')
    else:
        if bool(st.session_state.user_editor['edited_rows']) or len(st.session_state.user_editor['deleted_rows']) > 0:
            update_successful = db_functions.update(table='user', data=user_df, connect_to='user')
            after_speichern(update_successful)

        if len(st.session_state.user_editor['added_rows']) > 0:
            insert_df = pd.DataFrame(st.session_state.user_editor['added_rows'])
            insert_successful = db_functions.insert(table='user', data=insert_df, connect_to='user')
            after_speichern(insert_successful)
