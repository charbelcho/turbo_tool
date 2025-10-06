import pandas as pd
import streamlit as st

import db_functions
from app import PAGE_USER_MANAGEMEMT, require_login


require_login()


class Profile:
    SUPER_USER = "Super User"
    ADMIN = "Admin"
    USER = "User"
    WRITE = "Write"
    VIEW = "View"


def after_speichern(successful):
    if successful:
        st.success('Die Daten wurden erfolgreich gespeichert')
        user_data = db_functions.select(table='user', connect_to='user')
        if not user_data.empty:
            user_data.drop(columns=['password'])
        st.session_state.user = user_data
    else:
        st.error('Fehler beim Speichern der Daten')


if 'user' not in st.session_state:
    user_data = db_functions.select(table='user', connect_to='user')
    if not user_data.empty:
        user_data.drop(columns=['password'])
    st.session_state.user = user_data


st.title(PAGE_USER_MANAGEMEMT)

if 'logged_in_user' in st.session_state:
    if st.session_state.logged_in_user.profil == 'Admin':
        user_df = st.data_editor(
            data=st.session_state.user,
            column_config={
                "profil": st.column_config.SelectboxColumn(
                    options=[Profile.ADMIN, Profile.USER, Profile.WRITE, Profile.VIEW]
                )
            },
            disabled=['user_index', 'password'],
            num_rows='dynamic',
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
    else:
        st.dataframe(st.session_state.user)
