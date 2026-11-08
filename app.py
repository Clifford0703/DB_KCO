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

# Estilo personalizado
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    </style>
""", unsafe_allow_html=True)

# Carga de datos directa y automática desde el archivo del repositorio (sin uploader)
@st.cache_data
def load_data():
    file_path = "Ordenes.xls"
    xls = pd.ExcelFile(file_path)
    sheet_name = xls.sheet_names[0]
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Eliminar duplicados en nombres de columnas para evitar conflictos en operaciones
    df = df.loc[:, ~df.columns.duplicated()]

    # Limpieza y formateo de fechas
    if 'FECHA_EMISION' in df.columns:
        df['FECHA_EMISION'] = pd.to_datetime(df['FECHA_EMISION'], format='%d-%m-%Y', errors='coerce')
    if 'FECHA_ENTREGA' in df.columns:
        df['FECHA_ENTREGA'] = pd.to_datetime(df['FECHA_ENTREGA'], format='%d-%m-%Y', errors='coerce')
    
    # Cálculo seguro de valores de venta
    unidades = df['UNIDADES_SOLICITADAS'] if 'UNIDADES_SOLICITADAS' in df.columns else 0
    precio = df['PRECIO_FINAL_NETO'] if 'PRECIO_FINAL_NETO' in df.columns else 0
    
    df['VALOR_VENTA_SOLICITADO'] = unidades * precio
    
    if 'UNIDADES_EN_DESPACHO' in df.columns:
        df['VALOR_VENTA_DESPACHADO'] = df['UNIDADES_EN_DESPACHO'] * precio
        
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo de datos: {e}")
    st.stop()

# --- SIDEBAR: FILTROS GLOBALES ---
st.sidebar.header("🔍 Filtros de Búsqueda")

if 'FECHA_EMISION' in df_raw.columns and not df_raw['FECHA_EMISION'].isna().all():
    min_date = df_raw['FECHA_EMISION'].min()
    max_date = df_raw['FECHA_EMISION'].max()
    date_range = st.sidebar.date_input(
        "Rango de Fecha de Emisión",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None

# Filtro por Producto
if 'DESCRIPCION_PRODUCTO' in df_raw.columns:
    productos = ['Todos'] + sorted(df_raw['DESCRIPCION_PRODUCTO'].dropna().unique().tolist())
    selected_producto = st.sidebar.selectbox("Producto", productos)
else:
    selected_producto = 'Todos'

# Filtro por Local de Entrega
if 'NOM_LOCAL_ENTREGA' in df_raw.columns:
    locales = ['Todos'] + sorted(df_raw['NOM_LOCAL_ENTREGA'].dropna().unique().tolist())
    selected_local = st.sidebar.selectbox("Local de Entrega / Cliente", locales)
else:
    selected_local = 'Todos'

# Aplicar filtros
df = df_raw.copy()
if date_range and len(date_range) == 2:
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
total_oc = df['NRO_OC'].nunique() if 'NRO_OC' in df.columns else len(df)
volumen_solicitado = df['UNIDADES_SOLICITADAS'].sum() if 'UNIDADES_SOLICITADAS' in df.columns else 0
volumen_despachado = df['UNIDADES_EN_DESPACHO'].sum() if 'UNIDADES_EN_DESPACHO' in df.columns else 0

if 'UNIDADES_SOLICITADAS' in df.columns and 'PRECIO_FINAL_NETO' in df.columns:
    precio_ponderado = (df['UNIDADES_SOLICITADAS'] * df['PRECIO_FINAL_NETO']).sum() / volumen_solicitado if volumen_solicitado > 0 else 0
else:
    precio_ponderado = 0

fulfillment_rate = (volumen_despachado / volumen_solicitado) * 100 if volumen_solicitado > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Órdenes (OC)", f"{total_oc:,}")
with col2:
    st.metric("Volumen Solicitado", f"{volumen_solicitado:,.0f}")
with col3:
    st.metric("Volumen Despachado", f"{volumen_despachado:,.0f}")
with col4:
    st.metric("Precio Ponderado", f"S/ {precio_ponderado:,.2f}")
with col5:
    st.metric("Nivel de Servicio", f"{fulfillment_rate:.1f}%")

st.markdown("---")

# --- AGRUPACIÓN TEMPORAL PARA EVOLUCIÓN ---
if 'FECHA_EMISION' in df.columns:
    df['MES_EMISION'] = df['FECHA_EMISION'].dt.to_period('M').astype(str)
    
    df_temp = df.copy()
    df_temp['VALOR_PARCIAL'] = df_temp['UNIDADES_SOLICITADAS'] * df_temp['PRECIO_FINAL_NETO']
    
    df_trend = df_temp.groupby('MES_EMISION').agg(
        CANT_OC=('NRO_OC', 'nunique'),
        VOLUMEN=('UNIDADES_SOLICITADAS', 'sum'),
        VALOR_TOTAL=('VALOR_PARCIAL', 'sum')
    ).reset_index()
    
    df_trend['PRECIO_PONDERADO'] = df_trend['VALOR_TOTAL'] / df_trend['VOLUMEN']

    # --- SECCIÓN 1: CURVA DE VENTAS Y PRECIOS PONDERADOS ---
    st.subheader("📈 Curva de Evolución: Volumen, Cantidad de OC y Precio Ponderado")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_trend['MES_EMISION'],
        y=df_trend['VOLUMEN'],
        name='Volumen Solicitado',
        marker_color='#2ca02c',
        yaxis='y'
    ))

    fig.add_trace(go.Scatter(
        x=df_trend['MES_EMISION'],
        y=df_trend['PRECIO_PONDERADO'],
        name='Precio Ponderado (S/)',
        mode='lines+markers',
        marker_color='#ff7f0e',
        line=dict(width=3),
        yaxis='y2'
    ))

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

# --- SECCIÓN 2: ANÁLISIS DETALLADO ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Volumen por Producto")
    if 'DESCRIPCION_PRODUCTO' in df.columns:
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
            labels={'DESCRIPCION_PRODUCTO': 'Variedad/Producto', 'VOLUMEN': 'Volumen Solicitado'}
        )
        fig_prod.update_traces(texttemplate='%{text} OCs', textposition='outside')
        fig_prod.update_layout(template='plotly_white', xaxis_tickangle=-30)
        st.plotly_chart(fig_prod, use_container_width=True)

with col_right:
    st.subheader("🏢 Distribución por Local de Destino")
    if 'NOM_LOCAL_ENTREGA' in df.columns:
        df_local = df.groupby('NOM_LOCAL_ENTREGA').agg(
            VOLUMEN=('UNIDADES_SOLICITADAS', 'sum')
        ).reset_index().sort_values(by='VOLUMEN', ascending=False).head(10)
        
        fig_local = px.bar(
            df_local,
            y='NOM_LOCAL_ENTREGA',
            x='VOLUMEN',
            orientation='h',
            title='Top 10 Locales por Volumen Solicitado',
            labels={'VOLUMEN': 'Unidades', 'NOM_LOCAL_ENTREGA': 'Local'}
        )
        fig_local.update_layout(template='plotly_white')
        st.plotly_chart(fig_local, use_container_width=True)

# --- SECCIÓN 3: TABLA DETALLADA ---
st.markdown("---")
st.subheader("📋 Detalle de Órdenes de Compra")

with st.expander("Ver tabla completa de registros filtrados"):
    st.dataframe(df, use_container_width=True)
