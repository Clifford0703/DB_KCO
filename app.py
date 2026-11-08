import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Dashboard Comercial - Distribución de Paltas",
    page_icon="🥑",
    layout="wide"
)

# Estilo personalizado para métricas y contenedores
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Carga de datos
@st.cache_data
def load_data():
    file_path = "Ordenes_20261106.xls"
    df = pd.read_excel(file_path, sheet_name="ORDENES_DE_COMPRA")
    
    # Limpieza y formateo de fechas
    df['FECHA_EMISION'] = pd.to_datetime(df['FECHA_EMISION'], format='%d-%m-%Y', errors='coerce')
    df['FECHA_ENTREGA'] = pd.to_datetime(df['FECHA_ENTREGA'], format='%d-%m-%Y', errors='coerce')
    
    # Cálculo de volumen de venta potencial (Solicitado) y real (Despachado/Recepcionado)
    # Volumen en peso o unidades según requerimiento
    df['VALOR_VENTA_SOLICITADO'] = df['UNIDADES_SOLICITADAS'] * df['PRECIO_FINAL_NETO']
    df['VALOR_VENTA_DESPACHADO'] = df['UNIDADES_EN_DESPACHO'] * df['PRECIO_FINAL_NETO']
    
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo de datos: {e}")
    st.stop()

# --- SIDEBAR: FILTROS GLOBALES ---
st.sidebar.header("🔍 Filtros de Búsqueda")

# Rango de fechas
min_date = df_raw['FECHA_EMISION'].min()
max_date = df_raw['FECHA_EMISION'].max()

date_range = st.sidebar.date_input(
    "Rango de Fecha de Emisión",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Filtro por Producto
productos = ['Todos'] + sorted(df_raw['DESCRIPCION_PRODUCTO'].unique().tolist())
selected_producto = st.sidebar.selectbox("Producto", productos)

# Filtro por Local de Entrega
locales = ['Todos'] + sorted(df_raw['NOM_LOCAL_ENTREGA'].unique().tolist())
selected_local = st.sidebar.selectbox("Local de Entrega / Cliente", locales)

# Aplicar filtros
df = df_raw.copy()
if len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df['FECHA_EMISION'] >= pd.to_datetime(start_date)) & (df['FECHA_EMISION'] <= pd.to_datetime(end_date))]

if selected_producto != 'Todos':
    df = df[df['DESCRIPCION_PRODUCTO'] == selected_producto]

if selected_local != 'Todos':
    df = df[df['NOM_LOCAL_ENTREGA'] == selected_local]

# --- HEADER PRINCIPAL ---
st.title("🥑 Dashboard Ejecutivo: Control de Órdenes y Ventas de Paltas")
st.markdown("Monitoreo de evolución de volumen, cantidad de órdenes y curva de precios ponderados.")

if df.empty:
    st.warning("No hay datos disponibles para los filtros seleccionados.")
    st.stop()

# --- KPIs PRINCIPALES ---
total_oc = df['NRO_OC'].nunique()
volumen_solicitado = df['UNIDADES_SOLICITADAS'].sum()
volumen_despachado = df['UNIDADES_EN_DESPACHO'].sum()
monto_total = df['VALOR_VENTA_SOLICITADO'].sum()

# Precio ponderado general = Suma(Unidades * Precio) / Suma(Unidades)
precio_ponderado = (df['UNIDADES_SOLICITADAS'] * df['PRECIO_FINAL_NETO']).sum() / volumen_solicitado if volumen_solicitado > 0 else 0
fulfillment_rate = (volumen_despachado / volumen_solicitado) * 100 if volumen_solicitado > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Órdenes (OC)", f"{total_oc:,}")
with col2:
    st.metric("Volumen Solicitado", f"{volumen_solicitado:,.0f} kg/ unidades")
with col3:
    st.metric("Volumen Despachado", f"{volumen_despachado:,.0f} kg/ unidades")
with col4:
    st.metric("Precio Ponderado", f"S/ {precio_ponderado:,.2f}")
with col5:
    st.metric("Nivel de Servicio (OTIF/Fill)", f"{fulfillment_rate:.1f}%")

st.markdown("---")

# --- AGRUPACIÓN TEMPORAL PARA EVOLUCIÓN ---
# Agrupar por Mes/Semana de Emisión
df['MES_EMISION'] = df['FECHA_EMISION'].dt.to_period('M').astype(str)

df_trend = df.groupby('MES_EMISION').agg(
    CANT_OC=('NRO_OC', 'nunique'),
    VOLUMEN=('UNIDADES_SOLICITADAS', 'sum'),
    VALOR_TOTAL=('VALOR_VENTA_SOLICITADO', 'sum'),
    VOLUMEN_PRECIO=('UNIDADES_SOLICITADAS', lambda x: (x * df.loc[x.index, 'PRECIO_FINAL_NETO']).sum())
).reset_index()

df_trend['PRECIO_PONDERADO'] = df_trend['VOLUMEN_PRECIO'] / df_trend['VOLUMEN']

# --- SECCIÓN 1: CURVA DE VENTAS Y PRECIOS PONDERADOS (GRÁFICO PRINCIPAL) ---
st.subheader("📈 Curva de Evolución: Volumen, Cantidad de OC y Precio Ponderado")

fig = go.Figure()

# Eje principal (Barras): Volumen de Venta
fig.add_trace(go.Bar(
    x=df_trend['MES_EMISION'],
    y=df_trend['VOLUMEN'],
    name='Volumen Solicitado (kg/unid)',
    marker_color='#2ca02c',
    yaxis='y'
))

# Línea secundaria 1: Precio Ponderado
fig.add_trace(go.Scatter(
    x=df_trend['MES_EMISION'],
    y=df_trend['PRECIO_PONDERADO'],
    name='Precio Ponderado (S/)',
    mode='lines+markers',
    marker_color='#ff7f0e',
    line=dict(width=3),
    yaxis='y2'
))

# Configuración de doble eje Y
fig.update_layout(
    title='Evolución Mensual de Volumen de Venta y Precio Ponderado',
    xaxis=dict(title='Mes de Emisión'),
    yaxis=dict(title='Volumen Total', side='left', showgrid=False),
    yaxis2=dict(title='Precio Ponderado (S/)', overlaying='y', side='right', showgrid=True),
    legend=dict(x=0.01, y=0.99),
    template='plotly_white',
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

# --- SECCIÓN 2: ANÁLISIS DETALLADO (2 Columnas) ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Cantidad de OC y Volumen por Producto")
    df_prod = df.groupby('DESCRIPCION_PRODUCTO').agg(
        CANT_OC=('NRO_OC', 'nunique'),
        VOLUMEN=('UNIDADES_SOLICITADAS', 'sum'),
        PRECIO_PROMEDIO=('PRECIO_FINAL_NETO', 'mean')
    ).reset_index()
    
    fig_prod = px.bar(
        df_prod,
        x='DESCRIPCION_PRODUCTO',
        y='VOLUMEN',
        text='CANT_OC',
        color='PRECIO_PROMEDIO',
        color_continuous_scale='Greens',
        labels={'DESCRIPCION_PRODUCTO': 'Variedad/Producto', 'VOLUMEN': 'Volumen Solicitado'},
        title='Volumen por Producto (Etiqueta: Cant. de OC)'
    )
    fig_prod.update_traces(texttemplate='%{text} OCs', textposition='outside')
    fig_prod.update_layout(template='plotly_white', xaxis_tickangle=-30)
    st.plotly_chart(fig_prod, use_container_width=True)

with col_right:
    st.subheader("🏢 Distribución por Local de Destino/Entrega")
    df_local = df.groupby('NOM_LOCAL_ENTREGA').agg(
        VOLUMEN=('UNIDADES_SOLICITADAS', 'sum'),
        PENDIENTE=('UNIDADES_PENDIENTES', 'sum')
    ).reset_index().sort_values(by='VOLUMEN', ascending=False).head(10)
    
    fig_local = px.bar(
        df_local,
        y='NOM_LOCAL_ENTREGA',
        x=['VOLUMEN', 'PENDIENTE'],
        orientation='h',
        title='Top 10 Locales: Volumen Solicitado vs Pendiente',
        labels={'value': 'Unidades', 'NOM_LOCAL_ENTREGA': 'Local'}
    )
    fig_local.update_layout(template='plotly_white', barmode='group')
    st.plotly_chart(fig_local, use_container_width=True)

# --- SECCIÓN 3: TABLA DE DATOS DETALLADA ---
st.markdown("---")
st.subheader("📋 Detalle de Órdenes de Compra")

with st.expander("Ver tabla completa de registros filtrados"):
    st.dataframe(
        df[[
            'NRO_OC', 'FECHA_EMISION', 'FECHA_ENTREGA', 'TIPO_OC',
            'NOM_LOCAL_ENTREGA', 'DESCRIPCION_PRODUCTO', 'PRECIO_FINAL_NETO',
            'UNIDADES_SOLICITADAS', 'UNIDADES_EN_DESPACHO', 'UNIDADES_PENDIENTES', 'FORMA_PAGO'
        ]],
        use_container_width=True
    )
