import pandas as pd
import streamlit as st
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


def mostrar_dashboard(engine):
    st.header('📊 Dashboard de Gestión Deportiva')
    st.caption('Indicadores obtenidos directamente de la base de datos MySQL.')

    try:
        with engine.connect() as conn:
            total_participantes = conn.execute(text('SELECT COUNT(*) FROM participante')).scalar_one()
            total_programaciones = conn.execute(text('SELECT COUNT(*) FROM programacion')).scalar_one()
            total_inscripciones = conn.execute(text('SELECT COUNT(*) FROM inscripcion')).scalar_one()
            cupos_libres = conn.execute(text('SELECT COALESCE(SUM(cupos_disponibles), 0) FROM programacion')).scalar_one()

            populares = pd.read_sql(text('''
                SELECT a.nombre AS actividad, COUNT(i.id_inscripcion) AS inscripciones
                FROM actividad_deportiva a
                JOIN programacion pr ON pr.id_actividad = a.id_actividad
                LEFT JOIN inscripcion i ON i.id_programacion = pr.id_programacion
                GROUP BY a.id_actividad, a.nombre
                ORDER BY inscripciones DESC, a.nombre
                LIMIT 10
            '''), conn)

            ocupacion = pd.read_sql(text('''
                SELECT c.nombre AS centro,
                       COALESCE(ins.inscripciones, 0) AS inscripciones,
                       COALESCE(cupos.cupos_libres, 0) AS cupos_libres
                FROM centro_deportivo c
                LEFT JOIN (
                    SELECT pr.id_centro, COUNT(i.id_inscripcion) AS inscripciones
                    FROM programacion pr
                    LEFT JOIN inscripcion i ON i.id_programacion = pr.id_programacion
                    GROUP BY pr.id_centro
                ) ins ON ins.id_centro = c.id_centro
                LEFT JOIN (
                    SELECT id_centro, SUM(cupos_disponibles) AS cupos_libres
                    FROM programacion GROUP BY id_centro
                ) cupos ON cupos.id_centro = c.id_centro
                ORDER BY inscripciones DESC, c.nombre
            '''), conn)

            ingresos = pd.read_sql(text('''
                SELECT a.nombre AS actividad,
                       COUNT(i.id_inscripcion) AS inscripciones,
                       COALESCE(COUNT(i.id_inscripcion) * a.valor_inscripcion, 0) AS ingreso_estimado
                FROM actividad_deportiva a
                LEFT JOIN programacion pr ON pr.id_actividad = a.id_actividad
                LEFT JOIN inscripcion i ON i.id_programacion = pr.id_programacion
                GROUP BY a.id_actividad, a.nombre, a.valor_inscripcion
                ORDER BY ingreso_estimado DESC
                LIMIT 10
            '''), conn)
    except SQLAlchemyError as exc:
        st.error('No se pudo cargar el dashboard desde MySQL.')
        st.code(str(exc))
        return

    a, b, c, d = st.columns(4)
    a.metric('Participantes', f'{total_participantes:,}')
    b.metric('Programaciones', f'{total_programaciones:,}')
    c.metric('Inscripciones', f'{total_inscripciones:,}')
    d.metric('Cupos libres', f'{int(cupos_libres):,}')

    st.subheader('1. Actividades más populares')
    st.caption('Número de inscripciones por actividad (todos los estados).')
    if not populares.empty:
        st.bar_chart(populares.set_index('actividad')['inscripciones'])
        with st.expander('Ver datos de popularidad'):
            st.dataframe(populares, hide_index=True, use_container_width=True)
    else:
        st.info('No hay actividades programadas.')

    st.subheader('2. Inscripciones y cupos por centro')
    st.caption('Comparación de inscripciones históricas y cupos actualmente disponibles. No es un porcentaje de ocupación.')
    if not ocupacion.empty:
        st.bar_chart(ocupacion.set_index('centro')[['inscripciones', 'cupos_libres']])
        with st.expander('Ver datos por centro'):
            st.dataframe(ocupacion, hide_index=True, use_container_width=True)
    else:
        st.info('No hay centros registrados.')

    st.subheader('3. Ingresos estimados por actividad')
    st.caption('Estimación: cantidad de inscripciones × valor de inscripción; no representa pagos efectivamente cobrados.')
    if not ingresos.empty:
        st.bar_chart(ingresos.set_index('actividad')['ingreso_estimado'])
        with st.expander('Ver datos de ingresos'):
            st.dataframe(ingresos, hide_index=True, use_container_width=True)
    else:
        st.info('No hay actividades registradas.')

    st.download_button('Descargar resumen CSV', ingresos.to_csv(index=False).encode('utf-8-sig'),
                       file_name='dashboard_ingresos_estimados.csv', mime='text/csv')
