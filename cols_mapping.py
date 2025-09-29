import streamlit as st
import db_functions

st.title("Cols Mapping")

container = st.container(border=True)
col1, col2 = container.columns(2)

col1.write('Mapping In-Datei -> Datenbank')
cols_map_in_df = col1.data_editor(
    data=db_functions.select('cols_map_in'),
    num_rows='dynamic',
)

gespeichert_cols_map_in = col1.button('Speicher In-Mapping')
if gespeichert_cols_map_in:
    erfolgreich, msg = db_functions.speichern_in_db(cols_map_in_df, 'cols_map_in')
    st.success(msg) if erfolgreich else st.error(msg)

col2.write('Mapping Datenbank -> Out-Datei')
cols_map_out_df = col2.data_editor(
    data=db_functions.select('cols_map_out'),
    num_rows='dynamic',
    column_config=st.column_config.NumberColumn("spalte_position", format="%d"),
    key=['spalte_position'])

gespeichert_cols_map_out = col2.button('Speicher Out-Mapping')
if gespeichert_cols_map_out:
    erfolgreich, msg = db_functions.speichern_in_db(cols_map_out_df, 'cols_map_out')
    st.success(msg) if erfolgreich else st.error(msg)
