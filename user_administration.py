import os
import time

import pandas as pd
import streamlit as st

import db_functions
from app import PAGE_USER_MANAGEMEMT, require_login


#require_login()


class Profile:
    SUPER_USER = "Super User"
    ADMIN = "Admin"
    USER = "User"


def load_user():
    user_data = db_functions.select(table='user', connect_to='user')
    user_data = user_data.loc[user_data['user_index'] > 0]
    st.session_state.orig_user_df = user_data
    if not user_data.empty:
        user_data = user_data.drop(columns=['password'])
        user_data.insert(0, "", [False for i in range(user_data.shape[0])])
    st.session_state.user = user_data


load_user()


def after_speichern(successful):
    if successful:
        st.success('Die Daten wurden erfolgreich gespeichert')
        load_user()
    else:
        st.error('Fehler beim Speichern der Daten')


st.title(PAGE_USER_MANAGEMEMT)

if 'logged_in_user' in st.session_state:
    if st.session_state.logged_in_user.profil == Profile.ADMIN or st.session_state.logged_in_user.profil == Profile.SUPER_USER:
        user_df = st.data_editor(
            data=st.session_state.user,
            column_config={
                "profil": st.column_config.SelectboxColumn(
                    options=[Profile.ADMIN, Profile.USER]
                )
            },
            disabled=['user_index', 'password'],
            hide_index=True,
            num_rows='fixed',
            key='user_editor'
        )

        col1, col2, col3, col4 = st.columns(4)
        speichern = col1.button(f'Speichern', use_container_width=True)
        if speichern:
            if not ((user_df['profil'] == Profile.ADMIN) & (user_df['freigeschaltet'])).any():
                st.info('Du musst mindestens einen Admin bestimmen und diesen freischalten')
            if (not bool(st.session_state.user_editor['edited_rows']) and len(
                    st.session_state.user_editor['added_rows']) == 0 and len(
                st.session_state.user_editor['deleted_rows']) == 0):
                st.info('Daten unverändert.')
            else:
                if not user_df.loc[user_df['user_index'] == 1].iloc[0]['freigeschaltet']:
                    user_df.loc[user_df['user_index'] == 1, 'freigeschaltet'] = True
                merged_user_df = pd.merge(st.session_state.orig_user_df, user_df,
                                          how='inner',
                                          on='user_index',
                                          suffixes=('', '_gui'))
                merged_user_df = merged_user_df[
                    ['user_index', 'vorname_gui', 'nachname_gui', 'email_gui', 'password', 'profil_gui', 'freigeschaltet_gui']]
                merged_user_df.columns = [c.replace("_gui", "") for c in merged_user_df.columns]
                super_user = db_functions.select_where(table='user', col_value={'user_index': 0}, connect_to='user')
                merged_user_df = pd.concat([super_user, merged_user_df])
                update_successful = db_functions.update(table='user', data=merged_user_df, connect_to='user')
                after_speichern(update_successful)

        alle_freischalten = col2.button('Alle freischalten', use_container_width=True)
        if alle_freischalten:
            merged_user_df = pd.merge(st.session_state.orig_user_df, user_df,
                                      how='inner',
                                      on='user_index',
                                      suffixes=('', '_gui'))
            merged_user_df = merged_user_df[
                ['user_index', 'vorname_gui', 'nachname_gui', 'email_gui', 'password', 'profil_gui',
                 'freigeschaltet_gui']]
            merged_user_df['freigeschaltet_gui'] = True
            merged_user_df.columns = [c.replace("_gui", "") for c in merged_user_df.columns]
            super_user = db_functions.select_where('user', {'user_index': 0}, 'user')
            merged_user_df = pd.concat([super_user, merged_user_df])
            update_successful = db_functions.update(table='user', data=merged_user_df, connect_to='user')
            after_speichern(update_successful)

        auswahl_loeschen = col3.button('Ausgewählte löschen', use_container_width=True)
        if auswahl_loeschen:
            if user_df.loc[user_df[""]].empty:
                st.info("Keine User ausgewählt")
            else:
                user_indezes = user_df.loc[user_df[""]]['user_index'].to_list()
                delete_succesful = db_functions.delete_where_in('user', 'user_index', user_indezes, 'user')
                if delete_succesful:
                    st.success("User erfolgreich gelöscht")
                else:
                    st.error("Fehler beim löschen")

            load_user()
            time.sleep(2)
            st.rerun()


        alle_loeschen = col4.button('Alle löschen', use_container_width=True)
        if alle_loeschen:
            os.remove('./user.db')
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
            st.switch_page('startseite.py')

    else:
        st.dataframe(st.session_state.user)
