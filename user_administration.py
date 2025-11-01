
import time
from collections import defaultdict

import pandas as pd
import streamlit as st

import db_functions
from app import PAGE_USER_MANAGEMEMT, require_login


require_login()


class Profile:
    SUPER_USER = "Super User"
    ADMIN = "Admin"
    USER = "User"


def load_user():
    user_data = db_functions.select(table='user').sort_values(by='user_id')
    user_data = user_data.loc[user_data['user_id'] > 0]
    st.session_state.orig_user_df = user_data
    if not user_data.empty:
        user_data = user_data.drop(columns=['password'])
        user_data.insert(0, "", [False for i in range(user_data.shape[0])])
    st.session_state.user = user_data


load_user()

def identify_rows_cols_to_update(original_df, update_df, key_col) -> dict:
    original_df = original_df.loc[original_df[key_col].isin(update_df[key_col])]
    update_df = update_df.loc[update_df[key_col].isin(original_df[key_col])]
    original_df = original_df.sort_values(by=key_col, ascending=True).set_index(key_col)
    update_df = update_df.sort_values(by=key_col, ascending=True).set_index(key_col)
    original_df, update_df = original_df.align(update_df, join="outer", axis=1)

    mask = original_df != update_df
    diffs = []
    for row, col in zip(*mask.to_numpy().nonzero()):
        diffs.append({
            key_col: row,
            "column": update_df.columns[col],
            "new_value": update_df.iat[row, col]
        })
    grouped = defaultdict(dict)
    for change in diffs:
        grouped[change[key_col]][change["column"]] = change["new_value"]
    return grouped


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
            disabled=['user_id', 'password'],
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
                if not user_df.loc[user_df['user_id'] == user_df['user_id'].min()].iloc[0]['freigeschaltet']:
                    user_df.loc[user_df['user_id'] == user_df['user_id'].min(), 'freigeschaltet'] = True
                merged_user_df = pd.merge(st.session_state.orig_user_df, user_df,
                                          how='inner',
                                          on='user_id',
                                          suffixes=('', '_gui'))
                merged_user_df = merged_user_df[
                    ['user_id', 'vorname_gui', 'nachname_gui', 'email_gui', 'password', 'profil_gui', 'freigeschaltet_gui']]
                merged_user_df.columns = [c.replace("_gui", "") for c in merged_user_df.columns]

                identified_rows_to_update = identify_rows_cols_to_update(st.session_state.orig_user_df, merged_user_df,
                                                                         'user_id')
                update_successful = db_functions.update(table='user', key_col='user_id', values_to_update=identified_rows_to_update)
                after_speichern(update_successful)

        alle_freischalten = col2.button('Alle freischalten', use_container_width=True)
        if alle_freischalten:
            merged_user_df = pd.merge(st.session_state.orig_user_df, user_df,
                                      how='inner',
                                      on='user_id',
                                      suffixes=('', '_gui'))
            merged_user_df = merged_user_df[
                ['user_id', 'vorname_gui', 'nachname_gui', 'email_gui', 'password', 'profil_gui',
                 'freigeschaltet_gui']]
            merged_user_df['freigeschaltet_gui'] = 'true'
            merged_user_df.columns = [c.replace("_gui", "") for c in merged_user_df.columns]

            identified_rows_to_update = identify_rows_cols_to_update(st.session_state.orig_user_df, merged_user_df, 'user_id')
            update_successful = db_functions.update(table='user', key_col='user_id', values_to_update=identified_rows_to_update)
            after_speichern(update_successful)

        auswahl_loeschen = col3.button('Ausgewählte löschen', use_container_width=True)
        if auswahl_loeschen:
            if user_df.loc[user_df[""]].empty:
                st.info("Keine User ausgewählt")
            else:
                user_indezes = user_df.loc[user_df[""]]['user_id'].to_list()
                delete_succesful = db_functions.delete_where_in('user', 'user_id', user_indezes)
                if delete_succesful:
                    st.success("User erfolgreich gelöscht")
                else:
                    st.error("Fehler beim löschen")

            load_user()
            time.sleep(2)
            st.rerun()


        alle_loeschen = col4.button('Alle löschen', use_container_width=True)
        if alle_loeschen:
            delete_succesful = db_functions.delete_greater('user', {'user_id': 0})
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
            st.switch_page('startseite.py')

    else:
        st.dataframe(st.session_state.user)
