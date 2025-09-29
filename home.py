import streamlit as st
import datetime as dt
import db_functions
import utils
import main


def check_if_input_exists():
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0
    else:
        st.session_state.uploader_key += 1
    already_in_db = db_functions.select_where('in_prices',
                                              {'jahr': st.session_state.jahr_hochladen_value, 'kalenderwoche': st.session_state.kalenderwoche_hochladen_value})
    if not already_in_db.empty:
        st.session_state.upload_exists = True
        st.error(f"Bereits Daten für KW: {st.session_state.kalenderwoche_hochladen_value}, Jahr: {st.session_state.jahr_hochladen_value} hochgeladen")
    else:
        st.session_state.upload_exists = False
        st.success(f"Noch keine Daten für KW: {st.session_state.kalenderwoche_hochladen_value}, Jahr: {st.session_state.jahr_hochladen_value} hochgeladen")

# Initialize session state
if 'jahr_anzeigen_value' not in st.session_state:
    st.session_state.jahr_anzeigen_value = dt.datetime.today().year
if 'jahr_anzeigen_values' not in st.session_state:
    st.session_state.jahr_anzeigen_values = utils.get_jahre(5)

if 'kalenderwoche_anzeigen_value' not in st.session_state:
    st.session_state.kalenderwoche_anzeigen_value = utils.get_current_kalenderwoche() - 1
if 'kalenderwoche_anzeigen_values' not in st.session_state:
    st.session_state.kalenderwoche_anzeigen_values = utils.get_kalenderwochen(
        utils.get_max_kw(utils.get_current_jahr()))

if 'in_oder_out' not in st.session_state:
    st.session_state.in_oder_out = 'Output'

if 'jahr_hochladen_value' not in st.session_state:
    st.session_state.jahr_hochladen_value = dt.datetime.today().year
if 'jahr_hochladen_values' not in st.session_state:
    st.session_state.jahr_hochladen_values = utils.get_jahre(5)

if 'kalenderwoche_hochladen_value' not in st.session_state:
    st.session_state.kalenderwoche_hochladen_value = utils.get_current_kalenderwoche()
if 'kalenderwoche_hochladen_values' not in st.session_state:
    st.session_state.kalenderwoche_hochladen_values = utils.get_kalenderwochen(
        utils.get_max_kw(utils.get_current_jahr()))

if 'upload_exists' not in st.session_state:
    check_if_input_exists()


st.title('Turbo Tool')

container = st.container(border=True)
container.write('Daten anzeigen:')

col1, col2, col3, col4, col5 = container.columns(5)

jahr_anzeigen = col1.selectbox(
    "Jahr",
    st.session_state.jahr_anzeigen_values,
    key='jahr_anzeigen_value'
)

kalenderwoche_anzeigen = col2.selectbox(
    "KW",
    st.session_state.kalenderwoche_anzeigen_values,
    key='kalenderwoche_anzeigen_value'
)

in_oder_out = col3.selectbox(
    "Daten",
    ('Output', 'Input'),
    key='in_oder_out'
)

daten_anzeigen = col4.button(f'Daten für KW {st.session_state.kalenderwoche_anzeigen_value if st.session_state.kalenderwoche_anzeigen_value else "__"} anzeigen',
                             use_container_width=True)
if daten_anzeigen:
    st.session_state.data_anzeigen = main.daten_fuer_kw_anzeigen(
        st.session_state.kalenderwoche_anzeigen_value, st.session_state.jahr_anzeigen_value,
        from_in_table=True if st.session_state.in_oder_out == 'Input' else False)

    st.dataframe(st.session_state.data_anzeigen)

if st.session_state.in_oder_out == 'Output':
    if main.write_excel(st.session_state.kalenderwoche_anzeigen_value, st.session_state.jahr_anzeigen_value) is not None:
        downloaden = col5.download_button(
            label=f'Download Excel für KW {st.session_state.kalenderwoche_anzeigen_value if st.session_state.kalenderwoche_anzeigen_value else "__"}',
            data=main.write_excel(st.session_state.kalenderwoche_anzeigen_value, st.session_state.jahr_anzeigen_value),
            file_name="data.xlsx",
            on_click='ignore',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            icon=":material/download:",
            use_container_width=True)

container2 = st.container(border=True)
container2.write('Daten hochladen für:')

col6, col7, col8 = container2.columns(3)


jahr_hochladen = col6.selectbox(
    "Jahr (Upload)",
    st.session_state.jahr_hochladen_values,
    key='jahr_hochladen_value',
    on_change=check_if_input_exists
)

kalenderwoche_hochladen = col7.selectbox(
    "KW (Upload)",
    st.session_state.kalenderwoche_hochladen_values,
    key='kalenderwoche_hochladen_value',
    on_change=check_if_input_exists
)

if not st.session_state.upload_exists:
    file = col8.file_uploader('Datei hochladen', type='csv', key=f"uploader_{st.session_state.uploader_key}")

    if file:
        st.components.v1.html(
                main.process(
                    file,
                    st.session_state.kalenderwoche_hochladen_value,
                    st.session_state.jahr_hochladen_value
                ), height=0, width=0)

