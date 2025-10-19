import time

import duckdb
import pandas as pd
import streamlit as st

import db_functions
import main
from app import PAGE_DATEN_LOESCHEN, require_login


#require_login()

def select_distinct(table: str, cols: list) -> pd.DataFrame:
    with duckdb.connect("file.db") as con:
        return con.sql(f"""SELECT distinct {','.join(cols)} FROM {table}""").df()


if 'daten' not in st.session_state or st.session_state.daten.empty:
    df = select_distinct('in_prices', ['jahr', 'kalenderwoche'])
    df = df.sort_values(['jahr', 'kalenderwoche'], ascending=[False, False])
    if not df.empty:
        st.session_state.daten = db_functions.select_distinct('in_prices', ['jahr', 'kalenderwoche']).sort_values(
            ['jahr', 'kalenderwoche'], ascending=[False, False])
        st.session_state.daten['delete'] = False
    else:
        st.session_state.daten = pd.DataFrame()

if 'jahr_delete' not in st.session_state:
    if not st.session_state.daten.empty:
        jahr_df = st.session_state.daten.drop_duplicates(subset=['jahr'])['jahr']
        if not jahr_df.empty:
            jahr_df = jahr_df.iloc[0]
        st.session_state.jahr_delete = jahr_df

if 'jahr_delete_values' not in st.session_state:
    if not st.session_state.daten.empty:
        st.session_state.jahr_delete_values = st.session_state.daten['jahr'].drop_duplicates().tolist()

if 'kalenderwoche_delete' not in st.session_state:
    if not st.session_state.daten.empty:
        kw_df = st.session_state.daten.drop_duplicates(subset=['kalenderwoche'])['kalenderwoche']
        if not kw_df.empty:
            kw_df = kw_df.iloc[0]
            st.session_state.kalenderwoche_delete = kw_df

if 'kalenderwoche_delete_values' not in st.session_state:
    if not st.session_state.daten.empty:
        st.session_state.kalenderwoche_delete_values = st.session_state.daten['kalenderwoche'].drop_duplicates().tolist()
    else:
        st.session_state.kalenderwoche_delete_values = []

if 'in_oder_out' not in st.session_state:
    st.session_state.in_oder_out = 'Output'

st.title(PAGE_DATEN_LOESCHEN)

container = st.container(border=True)
col1, col2 = container.columns(2)

col1.write('Daten' if not st.session_state.daten.empty else 'Keine Daten vorhanden')


if not st.session_state.daten.empty:
    delete_df = col1.data_editor(
        data=st.session_state.daten,
        column_config={
            "delete": st.column_config.CheckboxColumn(
                help="Delete Data from KW",
                default=False,
            )
        },
        disabled=['jahr', 'kalenderwoche'],
        hide_index=True,
        key='editor'
    )

    daten_loeschen = col2.button(f'Ausgewählte Daten löschen', use_container_width=True)
    if daten_loeschen:
        selected_df = delete_df.loc[delete_df['delete']]
        delete_from_in_prices = db_functions.delete_where_data_df('in_prices', selected_df[['jahr', 'kalenderwoche']])
        delete_from_out_prices = db_functions.delete_where_data_df('out_prices', selected_df[['jahr', 'kalenderwoche']])
        if delete_from_in_prices and delete_from_out_prices:
            st.success('Die Daten wurden erfolgreich gelöscht')
        else:
            st.error('Fehler beim Löschen der Daten')
        st.session_state.daten = db_functions.select_distinct('in_prices', ['jahr', 'kalenderwoche']).sort_values(
            ['jahr', 'kalenderwoche'], ascending=[False, False])
        st.session_state.daten['delete'] = False
        time.sleep(1)
        st.rerun()

    alle_daten_loeschen = col2.button(f'Alle Daten löschen', use_container_width=True)
    if alle_daten_loeschen:
        delete_from_in_prices = db_functions.delete('in_prices')
        delete_from_out_prices = db_functions.delete('out_prices')
        if delete_from_in_prices and delete_from_out_prices:
            st.success('Die Daten wurden erfolgreich gelöscht')
        else:
            st.error('Fehler beim Löschen der Daten')
        st.session_state.daten = db_functions.select_distinct('in_prices', ['jahr', 'kalenderwoche']).sort_values(
            ['jahr', 'kalenderwoche'], ascending=[False, False])
        st.session_state.daten['delete'] = False
        time.sleep(1)
        st.rerun()


    container2 = st.container(border=True)
    col3, col4, col5, col6 = container2.columns(4)

    jahr = col3.selectbox(
        "Jahr",
        st.session_state.jahr_delete_values,
        key='jahr'
    )

    kalenderwoche = col4.selectbox(
        "KW",
        st.session_state.kalenderwoche_delete_values,
        key='kalenderwoche'
    )

    in_oder_out = col5.selectbox(
        "Daten",
        ('Output', 'Input'),
        key='in_oder_out'
    )

    daten_anzeigen = col6.button(
        f'Daten für KW {st.session_state.kalenderwoche if st.session_state.kalenderwoche else "__"} anzeigen',
        use_container_width=True)
    if daten_anzeigen:
        st.session_state.data_anzeigen = main.daten_fuer_kw_anzeigen(
            st.session_state.kalenderwoche, st.session_state.jahr,
            from_in_table=True if st.session_state.in_oder_out == 'Input' else False)

        st.dataframe(st.session_state.data_anzeigen)
