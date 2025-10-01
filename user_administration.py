import duckdb
import pandas as pd
import streamlit as st
import db_functions
import main
from app import PAGE_USER_MANAGEMEMT


class Profile:
    SUPER_USER = "Super User"
    ADMIN = "Admin"
    USER = "User"
    WRITE = "Write"
    VIEW = "View"

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

#if not bool(st.session_state.user_editor['edited_rows']) and not len(st.session_state.user_editor['added_rows']) == 0 and not len(st.session_state.user_editor['deleted_rows']) == 0:
speichern = st.button(f'Speichern', use_container_width=True)
if speichern:
    print(st.session_state.user_editor)
    print(pd.DataFrame(st.session_state.user_editor['edited_rows']))
    if bool(st.session_state.user_editor['edited_rows']):
        update_df = pd.DataFrame(st.session_state.user_editor['edited_rows']).transpose()
        for i, row in update_df.iterrows():
            orig_row = st.session_state.user.iloc[i]
            if not row.equals(orig_row):
                break

    if len(st.session_state.user_editor['added_rows']) > 0:
        insert_df = pd.DataFrame(st.session_state.user_editor['added_rows'])
        insert_successful = db_functions.insert(table='user', data=insert_df, connect_to='user')

        #print(user_df)
        ##insert_successful = db_functions.insert(table='user', data=user_df, connect_to='user')
        if insert_successful:
            st.success('Die Daten wurden erfolgreich gespeichert')

            st.session_state.user = db_functions.select(table='user', connect_to='user')
            #st.rerun()
        ##else:
            ##st.error('Fehler beim Speichern der Daten')


