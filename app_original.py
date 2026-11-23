import os
from datetime import date
import pandas as pd
import streamlit as st
from dashboard import mostrar_dashboard
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from crud_participantes import mostrar_crud_participantes
from inscripciones import mostrar_inscripciones

st.set_page_config(page_title='Gestión Deportiva | R1-R12', page_icon='🏟️', layout='wide')
st.title('🏟️ Sistema de Gestión Deportiva')
st.caption('Consultas R1 a R12 de la base MySQL gestion_deportiva_fase2_CORREGIDA_2')

CONSULTAS = {
 'R1': ('Actividades más populares', 'sp_actividades_populares', 'fechas'),
 'R2': ('Inscripciones por centro y clasificación', 'vw_distribucion_inscripciones', 'vista'),
 'R3': ('Ocupación y evaluación', 'R3_ocupacion_evaluacion', 'vista'),
 'R4': ('Actividad por centro', 'R4_centros_actividades', 'fechas'),
 'R5': ('Ocupación de espacios', 'R5_ocupacion_espacios', 'vista'),
 'R6': ('Ingresos estimados', 'R6_ingresos_actividades', 'vista'),
 'R7': ('Diversidad por centro', 'R7_diversidad_actividades_centro', 'vista'),
 'R8': ('Participantes con 6 o más asistencias', 'R8_participantes_asistentes', 'vista'),
 'R9': ('Programaciones sobre promedio', 'R9_programaciones_sobre_promedio', 'actividad_fechas'),
 'R10': ('Mantenciones sobre promedio del centro', 'sp_r10_espacios_mantencion_sobre_promedio', 'centro'),
 'R11': ('Participantes destacados', 'sp_r11_participantes_destacados', 'fechas'),
 'R12': ('Centros con ocupación sobre promedio', 'sp_r12_centros_ocupacion_sobre_promedio', 'fechas'),
}

# Configuración privada, guardada localmente en .streamlit/secrets.toml.
try:
 config = st.secrets["mysql"]
 host = config["host"]
 port = int(config["port"])
 usuario = config["user"]
 clave = config["password"]
 base = config["database"]
except (KeyError, FileNotFoundError, OSError) as exc:
 st.error("Falta configurar MySQL. Revisa el archivo .streamlit/secrets.toml según INSTRUCCIONES.txt.")
 st.stop()

@st.cache_resource(show_spinner=False)
def conectar(host, port, usuario, clave, base):
 url = URL.create('mysql+pymysql', username=usuario, password=clave, host=host, port=int(port), database=base)
 return create_engine(url, pool_pre_ping=True)

try:
 engine = conectar(host, port, usuario, clave, base)
 with engine.connect() as conn:
  conn.execute(text('SELECT 1'))
 st.success('Conectado a MySQL · Base: ' + base)
except Exception as exc:
 st.error('No se pudo conectar a MySQL. Comprueba que el servidor esté encendido, que la base esté importada y que la contraseña sea correcta.')
 st.caption('Revisa el puerto, la contraseña y que MySQL esté funcionando. Consulta la terminal para detalles.')
 st.stop()

# Navegación principal: las consultas originales se conservan intactas.
# MENÚ PRINCIPAL
seccion = st.sidebar.radio(
    "Menú principal",
    [
        "Consultas R1-R12",
        "CRUD Participantes",
        "Inscripciones",
        "Dashboard"
    ]
)

if seccion == "CRUD Participantes":
    mostrar_crud_participantes(engine)
    st.stop()

elif seccion == "Inscripciones":
    mostrar_inscripciones(engine)
    st.stop()

elif seccion == "Dashboard":
    mostrar_dashboard(engine)
    st.stop()

seleccion = st.selectbox('Selecciona el requerimiento', list(CONSULTAS), format_func=lambda r: f'{r} — {CONSULTAS[r][0]}')
nombre, objeto, tipo = CONSULTAS[seleccion]
st.subheader(f'{seleccion}: {nombre}')
params = {}
if tipo in ('fechas', 'actividad_fechas'):
 c1, c2 = st.columns(2)
 with c1: inicio = st.date_input('Fecha inicial', date(2026, 1, 1))
 with c2: fin = st.date_input('Fecha final', date(2026, 12, 31))
 if inicio > fin:
  st.warning('La fecha inicial debe ser anterior o igual a la final.')
  st.stop()
 params.update(inicio=inicio, fin=fin)
if tipo == 'actividad_fechas':
 try:
  with engine.connect() as conn:
   actividades = pd.read_sql(text('SELECT id_actividad, nombre FROM actividad_deportiva ORDER BY id_actividad'), conn)
  if actividades.empty:
   st.warning('No hay actividades cargadas.')
   st.stop()
  opciones = {f"{int(r.id_actividad)} — {r.nombre}": int(r.id_actividad) for r in actividades.itertuples(index=False)}
  etiqueta = st.selectbox('Actividad deportiva', list(opciones))
  params['actividad'] = opciones[etiqueta]
 except Exception as exc:
  st.error(f'No se pudieron cargar las actividades: {exc}')
  st.stop()
if tipo == 'centro':
 try:
  with engine.connect() as conn:
   centros = pd.read_sql(text('SELECT id_centro, nombre FROM centro_deportivo ORDER BY id_centro'), conn)
  opciones = {f"{int(r.id_centro)} — {r.nombre}": int(r.id_centro) for r in centros.itertuples(index=False)}
  etiqueta = st.selectbox('Centro deportivo', list(opciones))
  params['centro'] = opciones[etiqueta]
 except Exception as exc:
  st.error(f'No se pudieron cargar los centros: {exc}')
  st.stop()

if st.button('Ejecutar consulta', type='primary'):
 try:
  with engine.connect() as conn:
   if tipo == 'vista':
    # Objeto SQL proviene únicamente del diccionario fijo CONSULTAS.
    df = pd.read_sql(text(f'SELECT * FROM `{objeto}`'), conn)
   else:
    argumentos = {'fechas': ':inicio, :fin', 'actividad_fechas': ':actividad, :inicio, :fin', 'centro': ':centro'}[tipo]
    resultado = conn.execute(text(f'CALL `{objeto}`({argumentos})'), params)
    df = pd.DataFrame(resultado.fetchall(), columns=resultado.keys())
  st.session_state['resultado'] = df
  st.session_state['consulta_actual'] = seleccion
 except Exception as exc:
  st.error('La consulta no se pudo ejecutar. Verifica que las vistas y procedimientos existan en MySQL.')
  st.code(str(exc))

if st.session_state.get('consulta_actual') == seleccion:
 df = st.session_state['resultado']
 st.metric('Filas obtenidas', len(df))
 if df.empty:
  st.info('La consulta se ejecutó, pero no hay registros que cumplan las condiciones.')
 else:
  st.dataframe(df, use_container_width=True, hide_index=True)
  st.download_button('Descargar resultados CSV', df.to_csv(index=False).encode('utf-8-sig'), file_name=f'{seleccion}_resultados.csv', mime='text/csv')
  numericas = df.select_dtypes(include='number').columns.tolist()
  categorias = [c for c in df.columns if c not in numericas]
  if numericas and categorias:
   st.subheader('Gráfico de resultados')
   eje_x = st.selectbox('Categoría', categorias, key=f'x_{seleccion}')
   eje_y = st.selectbox('Valor', numericas, key=f'y_{seleccion}')
   grafico = df[[eje_x, eje_y]].copy().head(30)
   grafico[eje_y] = pd.to_numeric(grafico[eje_y], errors='coerce')
   st.bar_chart(grafico.set_index(eje_x)[eje_y])
