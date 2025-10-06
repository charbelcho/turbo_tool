import streamlit as st

from app import PAGE_STARTSEITE


st.title(PAGE_STARTSEITE)

st.write("""
Anleitung

Nach der Registrierung und dem Login zur Seite Turbo Tool navigieren.

Dort dann die Auswahl treffen für welche Kalenderwoche die Preise hochgeladen werden soll. Wenn die Verarbeitung ohne 
Fehler durchläuft, dann wird das Ergebnis automatisch gedownloaded. 
""")
