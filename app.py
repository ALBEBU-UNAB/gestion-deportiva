"""Puerta de entrada con autenticación para la aplicación original.

Antes de usarla, cambia el nombre del app.py anterior a app_original.py.
"""
import runpy
from pathlib import Path

import streamlit as st
from sqlalchemy import create_engine, URL

from usuarios import solicitar_inicio_sesion, mostrar_sesion


@st.cache_resource
def conexion_autenticacion():
    cfg = st.secrets['mysql']
    url = URL.create(
        'mysql+pymysql',
        username=cfg['user'],
        password=cfg['password'],
        host=cfg.get('host', '127.0.0.1'),
        port=int(cfg.get('port', 3306)),
        database=cfg['database'],
    )
    return create_engine(url, pool_pre_ping=True)


usuario = solicitar_inicio_sesion(conexion_autenticacion())
mostrar_sesion(usuario)

# La aplicación original conserva sus consultas, CRUD, inscripciones y Dashboard.
# Se restringen las secciones para los operadores interceptando el radio de navegación.
original = Path(__file__).with_name('app_original.py')
if not original.is_file():
    st.error('Falta app_original.py. Renombra tu antiguo app.py a app_original.py.')
    st.stop()

if 'administrador' not in usuario['roles']:
    if 'operador' not in usuario['roles']:
        st.error('Esta cuenta no tiene un rol autorizado.')
        st.stop()

    radio_original = st.sidebar.radio

    def radio_con_permisos(label, options, *args, **kwargs):
        # Permitir únicamente CRUD e inscripciones en la navegación principal.
        opciones = list(options)
        if 'CRUD Participantes' in opciones and 'Inscripciones' in opciones:
            permitidas = ['CRUD Participantes', 'Inscripciones']
            kwargs.pop('index', None)
            return radio_original(label, permitidas, *args, **kwargs)
        return radio_original(label, options, *args, **kwargs)

    st.sidebar.radio = radio_con_permisos

runpy.run_path(str(original), run_name='__main__')
