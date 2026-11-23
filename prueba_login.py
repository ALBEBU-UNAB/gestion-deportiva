
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from usuarios import solicitar_inicio_sesion, mostrar_sesion

st.set_page_config(page_title="Prueba de inicio de sesión")

config = st.secrets["mysql"]

url = URL.create(
    "mysql+pymysql",
    username=config["user"],
    password=config["password"],
    host=config["host"],
    port=int(config["port"]),
    database=config["database"]
)

engine = create_engine(url, pool_pre_ping=True)

usuario = solicitar_inicio_sesion(engine)

st.success("Inicio de sesión correcto")
mostrar_sesion(usuario)

st.write("Usuario autenticado:", usuario["nombre_usuario"])
st.write("Roles:", ", ".join(usuario["roles"]))
