
import streamlit as st
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def mostrar_crud_participantes(engine):
    st.title("Gestión de participantes")

    pestañas = st.tabs([
        "Consultar",
        "Registrar",
        "Editar",
        "Eliminar"
    ])

    with pestañas[0]:
        st.subheader("Listado de participantes")

        with engine.connect() as conexion:
            datos = pd.read_sql(
                text("""
                    SELECT id_participante, nombre,
                           correo, telefono
                    FROM participante
                    ORDER BY id_participante
                """),
                conexion
            )

        st.dataframe(datos, use_container_width=True)

    with pestañas[1]:
        st.subheader("Registrar participante")

        with st.form("registrar_participante"):
            nombre = st.text_input("Nombre")
            correo = st.text_input("Correo electrónico")
            telefono = st.text_input("Teléfono")

            guardar = st.form_submit_button("Guardar")

        if guardar:
            if not nombre.strip():
                st.error("Debes ingresar un nombre.")
            else:
                try:
                    with engine.begin() as conexion:
                        conexion.execute(
                            text("""
                                INSERT INTO participante
                                    (nombre, correo, telefono)
                                VALUES
                                    (:nombre, :correo, :telefono)
                            """),
                            {
                                "nombre": nombre.strip(),
                                "correo": correo.strip() or None,
                                "telefono": telefono.strip() or None
                            }
                        )
                    st.success("Participante registrado.")
                except IntegrityError:
                    st.error("El correo ya existe o los datos no son válidos.")

    with pestañas[2]:
        st.subheader("Editar participante")

        with engine.connect() as conexion:
            participantes = conexion.execute(
                text("""
                    SELECT id_participante, nombre,
                           correo, telefono
                    FROM participante
                    ORDER BY id_participante
                """)
            ).mappings().all()

        if participantes:
            opciones = {
                f"{p['id_participante']} - {p['nombre']}": p
                for p in participantes
            }

            elegido = st.selectbox(
                "Selecciona un participante",
                list(opciones.keys())
            )
            actual = opciones[elegido]

            with st.form("editar_participante"):
                nuevo_nombre = st.text_input(
                    "Nombre", value=actual["nombre"]
                )
                nuevo_correo = st.text_input(
                    "Correo", value=actual["correo"] or ""
                )
                nuevo_telefono = st.text_input(
                    "Teléfono", value=actual["telefono"] or ""
                )
                actualizar = st.form_submit_button("Actualizar")

            if actualizar:
                if not nuevo_nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    try:
                        with engine.begin() as conexion:
                            conexion.execute(
                                text("""
                                    UPDATE participante
                                    SET nombre = :nombre,
                                        correo = :correo,
                                        telefono = :telefono
                                    WHERE id_participante = :id
                                """),
                                {
                                    "nombre": nuevo_nombre.strip(),
                                    "correo": nuevo_correo.strip() or None,
                                    "telefono": nuevo_telefono.strip() or None,
                                    "id": actual["id_participante"]
                                }
                            )
                        st.success("Participante actualizado.")
                    except IntegrityError:
                        st.error("El correo ya está registrado.")
        else:
            st.info("No hay participantes registrados.")

    with pestañas[3]:
        st.subheader("Eliminar participante")

        st.warning(
            "No se podrán eliminar participantes que tengan "
            "registros relacionados en otras tablas."
        )

        with engine.connect() as conexion:
            participantes = conexion.execute(
                text("""
                    SELECT id_participante, nombre
                    FROM participante
                    ORDER BY id_participante
                """)
            ).all()

        if participantes:
            opciones = {
                f"{p[0]} - {p[1]}": p[0]
                for p in participantes
            }

            elegido = st.selectbox(
                "Participante a eliminar",
                list(opciones.keys())
            )

            with st.form("eliminar_participante"):
                confirmar = st.checkbox("Confirmar eliminación")
                eliminar = st.form_submit_button("Eliminar")

            if eliminar:
                if not confirmar:
                    st.error("Debes confirmar la eliminación.")
                else:
                    try:
                        with engine.begin() as conexion:
                            conexion.execute(
                                text("""
                                    DELETE FROM participante
                                    WHERE id_participante = :id
                                """),
                                {"id": opciones[elegido]}
                            )
                        st.success("Participante eliminado.")
                    except IntegrityError:
                        st.error(
                            "No se puede eliminar: tiene "
                            "registros relacionados."
                        )
