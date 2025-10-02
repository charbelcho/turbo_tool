import streamlit as st

from app import PAGE_LOGIN

st.title(PAGE_LOGIN)

if 'password' not in st.session_state:
    st.session_state.password = ''

def printer():
    print(st.session_state.password)

with st.form("login_form"):
    e_mail = st.text_input(label="E-Mail-Adresse", key='email')

    passwort = st.text_input(label="Passwort", type='password', key='password')
    if len(st.session_state.password) < 8:
        st.markdown('Passwort muss mindestens 8 Zeichen lang sein')

    # Every form must have a submit button.
    submitted = st.form_submit_button("Einloggen")
    if submitted:
        st.write("slider")