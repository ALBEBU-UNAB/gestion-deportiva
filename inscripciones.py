import streamlit as st
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


def mostrar_inscripciones(engine):
    st.header("Inscripción a actividades deportivas")
    st.caption("Registro transaccional: inscripción y descuento de cupo en una sola operación.")

    try:
        with engine.connect() as conn:
            participantes = pd.read_sql(
                text("SELECT id_participante, nombre FROM participante ORDER BY nombre"), conn
            )
            programaciones = pd.read_sql(
                text("""
                    SELECT pr.id_programacion, a.nombre AS actividad, pr.fecha,
                           pr.hora_inicio, pr.cupos_disponibles
                    FROM programacion pr
                    JOIN actividad_deportiva a ON a.id_actividad = pr.id_actividad
                    ORDER BY pr.fecha, pr.hora_inicio, pr.id_programacion
                """), conn
            )
    except SQLAlchemyError as exc:
        st.error(f"No se pudieron cargar los datos: {exc}")
        return

    if participantes.empty or programaciones.empty:
        st.warning("Necesitas participantes y programaciones cargadas.")
        return

    opciones_part = {
        f"{r.nombre} (ID {int(r.id_participante)})": int(r.id_participante)
        for r in participantes.itertuples(index=False)
    }
    opciones_prog = {
        f"ID {int(r.id_programacion)} · {r.actividad} · {r.fecha} · "
        f"{r.hora_inicio} · Cupos: {int(r.cupos_disponibles)}": int(r.id_programacion)
        for r in programaciones.itertuples(index=False)
    }

    with st.form("formulario_inscripcion"):
        etiqueta_part = st.selectbox("Participante", list(opciones_part))
        etiqueta_prog = st.selectbox("Actividad programada", list(opciones_prog))
        enviar = st.form_submit_button("Registrar inscripción", type="primary")

    if enviar:
        id_part = opciones_part[etiqueta_part]
        id_prog = opciones_prog[etiqueta_prog]
        try:
            # FOR UPDATE bloquea la programación hasta confirmar o revertir.
            with engine.begin() as conn:
                fila = conn.execute(
                    text("""
                        SELECT cupos_disponibles
                        FROM programacion
                        WHERE id_programacion = :id
                        FOR UPDATE
                    """), {"id": id_prog}
                ).mappings().first()

                if fila is None:
                    raise ValueError("La programación ya no existe.")
                if fila["cupos_disponibles"] <= 0:
                    raise ValueError("No quedan cupos disponibles.")

                # La restricción UNIQUE evita inscribir dos veces al mismo participante.
                conn.execute(
                    text("""
                        INSERT INTO inscripcion (id_programacion, id_participante, estado)
                        VALUES (:programacion, :participante, 'activa')
                    """),
                    {"programacion": id_prog, "participante": id_part},
                )
                conn.execute(
                    text("""
                        UPDATE programacion
                        SET cupos_disponibles = cupos_disponibles - 1
                        WHERE id_programacion = :id
                    """), {"id": id_prog}
                )
            st.success("Inscripción registrada. Se descontó un cupo.")
        except IntegrityError:
            st.error("El participante ya está inscrito en esa programación o existe un conflicto de integridad. No se descontó ningún cupo.")
        except ValueError as exc:
            st.warning(str(exc))
        except SQLAlchemyError as exc:
            st.error(f"No se pudo registrar la inscripción. Se revirtió la transacción: {exc}")

    st.subheader("Inscripciones registradas")
    try:
        with engine.connect() as conn:
            listado = pd.read_sql(
                text("""
                    SELECT i.id_inscripcion, p.nombre AS participante,
                           a.nombre AS actividad, pr.fecha,
                           i.estado, i.fecha_inscripcion
                    FROM inscripcion i
                    JOIN participante p ON p.id_participante = i.id_participante
                    JOIN programacion pr ON pr.id_programacion = i.id_programacion
                    JOIN actividad_deportiva a ON a.id_actividad = pr.id_actividad
                    ORDER BY i.id_inscripcion DESC
                    LIMIT 100
                """), conn
            )
        st.dataframe(listado, use_container_width=True, hide_index=True)
    except SQLAlchemyError as exc:
        st.error(f"No se pudo consultar el listado: {exc}")
