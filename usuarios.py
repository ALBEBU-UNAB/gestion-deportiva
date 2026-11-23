import streamlit as st
from sqlalchemy import text
from werkzeug.security import check_password_hash


def autenticar(engine, nombre_usuario, contrasena):
    with engine.connect() as conn:
        filas = conn.execute(text('''
            SELECT u.id_usuario, u.nombre_usuario, u.password_hash, u.activo,
                   r.nombre AS rol
            FROM usuario_sistema AS u
            JOIN usuario_rol AS ur ON ur.id_usuario = u.id_usuario
            JOIN rol AS r ON r.id_rol = ur.id_rol
            WHERE u.nombre_usuario = :usuario
        '''), {'usuario': nombre_usuario}).mappings().all()
    if not filas or not filas[0]['activo']:
        return None
    hash_guardado = filas[0]['password_hash']
    if hash_guardado == 'PENDIENTE_CONFIGURAR_HASH':
        return None
    try:
        if not check_password_hash(hash_guardado, contrasena):
            return None
    except (ValueError, TypeError):
        return None
    return {
        'id_usuario': filas[0]['id_usuario'],
        'nombre_usuario': filas[0]['nombre_usuario'],
        'roles': sorted({fila['rol'] for fila in filas}),
    }


def solicitar_inicio_sesion(engine):
    if 'usuario_autenticado' in st.session_state:
        return st.session_state['usuario_autenticado']
    st.title('Gestión Deportiva')
    st.subheader('Inicio de sesión')
    with st.form('form_login'):
        nombre = st.text_input('Usuario')
        contrasena = st.text_input('Contraseña', type='password')
        entrar = st.form_submit_button('Ingresar')
    if entrar:
        try:
            usuario = autenticar(engine, nombre.strip(), contrasena)
        except Exception:
            st.error('No se pudo comprobar el inicio de sesión. Revisa la conexión con MySQL.')
            st.stop()
        if usuario:
            st.session_state['usuario_autenticado'] = usuario
            st.rerun()
        st.error('Usuario o contraseña incorrectos, o cuenta inactiva.')
    st.stop()


def mostrar_sesion(usuario):
    st.sidebar.write(f"Usuario: **{usuario['nombre_usuario']}**")
    st.sidebar.write('Rol: ' + ', '.join(usuario['roles']))
    if st.sidebar.button('Cerrar sesión'):
        st.session_state.pop('usuario_autenticado', None)
        st.rerun()
