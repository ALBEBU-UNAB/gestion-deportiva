import runpy
from pathlib import Path
import streamlit as st

original = Path(__file__).with_name("app_original.py")

if not original.is_file():
    st.error("No se encontró app_original.py")
    st.stop()

runpy.run_path(str(original), run_name="__main__")