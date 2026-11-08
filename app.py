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

# Carga de datos robusta para archivos .xls / .xlsx
@st.cache_data
def load_data():
    file_path = "Ordenes.xls"
    
    try:
        xls = pd.ExcelFile(file_path, engine='xlrd')
    except Exception:
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
        except Exception:
            xls = pd.ExcelFile(file_path)
            
    sheet_name = xls.sheet_names[0]
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Eliminar columnas duplicadas
    df = df.loc[:, ~df.columns.duplicated()]

    # Limpieza y formateo de fechas
    if 'FECHA_EMISION' in df.columns:
        df['FECHA_EMISION'] = pd.to_datetime(df['FECHA_EMISION'], format='%d-%m-%Y', errors='coerce')
    if 'FECHA_ENTREGA' in df.columns:
        df['FECHA_ENTREGA'] = pd.to_datetime(df['FECHA_ENTREGA'], format='%d-%m-%Y', errors='coerce')
    
    # Cálculos clave de negocio
    unidades = df['UNIDADES_SOLICITADAS'] if 'UNIDADES_SOLICITADAS' in df.columns else 0
    precio = df['PRECIO_FINAL_NETO'] if 'PRECIO_FINAL_NETO' in df.columns else 0
    
    df['VALOR_VENTA_SOLICITADO'] = unidades * precio
    
    # Suposición de conversión estándar (si el empaque es jaba de 18kg, o métricas directas)
    # Se calculan toneladas (Tn) y jabas / unidades
    df['TONELADAS_SOLICITADAS'] = unidades / 1000.0  # Asumiendo kg o unidades equivalentes
    
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

# Filtro por Producto / Variedad
if 'DESCRIPCION_PRODUCTO' in df_raw.columns:
    productos = ['Todos'] + sorted(df_raw['DESCRIPCION_PRODUCTO'].dropna().unique().tolist())
    selected_producto = st.sidebar.selectbox("Variedad de Palta", productos)
else:
    selected_producto = 'Todos'

# Filtro por Tipo de OC
if 'TIPO_OC' in df_raw.columns:
    tipos_oc = ['Todos'] + sorted(df_raw['TIPO_OC'].dropna().unique().tolist())
    selected_tipo_oc = st.sidebar.selectbox("Tipo de Orden de Compra", tipos_oc)
else:
    selected_tipo_oc = 'Todos'

# Aplicar filtros
df = df_raw.copy()
if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df['FECHA_EMISION'] >= pd.to_datetime(start_date)) & (df['FECHA_EMISION'] <= pd.to_datetime(end_date))]

if selected_producto != 'Todos':
    df = df[df['DESCRIPCION_PRODUCTO'] == selected_producto]

if selected_tipo_oc != 'Todos':
    df = df[df['TIPO_OC'] == selected_tipo_oc]

# --- HEADER PRINCIPAL ---
st.title("🥑 Control Gerencial de Ventas y Pricing - Distribuidora de Paltas")
st.markdown("Análisis financiero, evolución de volúmenes, cantidad de órdenes (OC) y precios ponderados.")

if df.empty:
    st.warning("No hay datos disponibles para los filtros seleccionados.")
    st.stop()

# --- KPIs PRINCIPALES ---
total_oc = df['NRO_OC'].nunique() if 'NRO_OC' in df.columns else len(df)
volumen_unidades = df['UNIDADES_SOLICITADAS'].sum() if 'UNIDADES_SOLICITADAS' in df.columns else 0
volumen_tn = df['TONELADAS_SOLICITADAS'].sum() if 'TONELADAS_SOLICITADAS' in df.columns else 0
monto_total_venta = df['VALOR_VENTA_SOLICITADO'].sum() if 'VALOR_VENTA_SOLICITADO' in df.columns else 0

if volumen_unidades > 0:
    precio_ponderado_general = monto_total_venta / volumen_unidades
else:
    precio_ponderado_general = 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Órdenes (OC)", f"{total_oc:,}")
with col2:
    st.metric("Volumen Solicitado", f"{volumen_unidades:,.0f} un/jabas")
with col3:
    st.metric("Volumen en Tn (Est.)", f"{volumen_tn:,.2f} Tn")
with col4:
    st.metric("Venta Potencial Total", f"S/ {monto_total_venta:,.2f}")
with col5:
    st.metric("Precio Ponderado Prom.", f"S/ {precio_ponderado_general:,.2f}")

st.markdown("---")

# --- PROCESAMIENTO MENSUAL PARA TENDENCIAS ---
if 'FECHA_EMISION' in df.columns:
    df['MES_EMISION'] = df['FECHA_EMISION'].dt.to_period('M').astype(str)
    
    df_temp = df.copy()
    df_temp['VALOR_PARCIAL'] = df_temp['UNIDADES_SOLICITADAS'] * df_temp['PRECIO_FINAL_NETO']
    
    df_trend = df_temp.groupby('MES_EMISION').agg(
        CANT_OC=('NRO_OC', 'nunique'),
        VOLUMEN=('UNIDADES_SOLICITADAS', 'sum'),
        TONELADAS=('TONELADAS_SOLICITADAS', 'sum'),
        VALOR_TOTAL=('VALOR_PARCIAL', 'sum')
    ).reset_index()
    
    df_trend['PRECIO_PONDERADO'] = df_trend['VALOR_TOTAL'] / df_trend['VOLUMEN']

    # --- GRÁFICO 1: TENDENCIA MENSUAL DE VOLUMEN Y PRECIO PONDERADO (DOBLE EJE) ---
    st.subheader("📈 Tendencia Mensual: Volumen Solicitado vs Precio Ponderado")
    
    fig_dual = go.Figure()

    # Barras de Volumen
    fig_dual.add_trace(go.Bar(
        x=df_trend['MES_EMISION'],
        y=df_trend['VOLUMEN'],
        name='Volumen (Unidades/Jabas)',
        marker_color='#2ca02c',
        text=df_trend['VOLUMEN'].apply(lambda x: f"{x:,.0f}"),
        textposition='outside',
        yaxis='y'
    ))

    # Línea de Precio Ponderado
    fig_dual.add_trace(go.Scatter(
        x=df_trend['MES_EMISION'],
        y=df_trend['PRECIO_PONDERADO'],
        name='Precio Ponderado (S/)',
        mode='lines+markers+text',
        text=df_trend['PRECIO_PONDERADO'].apply(lambda x: f"S/ {x:.2f}"),
        textposition='top center',
        marker_color='#ff7f0e',
        line=dict(width=3),
        yaxis='y2'
    ))

    fig_dual.update_layout(
        title='Evolución de Volumen de Venta y Precio Ponderado por Mes',
        xaxis=dict(title='Mes de Emisión'),
        yaxis=dict(title='Volumen Total', side='left', showgrid=False),
        yaxis2=dict(title='Precio Ponderado (S/)', overlaying='y', side='right', showgrid=True),
        legend=dict(x=0.01, y=0.99),
        template='plotly_white',
        hovermode='x unified',
        margin=dict(t=50, b=30)
    )

    st.plotly_chart(fig_dual, use_container_width=True)

    # --- GRÁFICO 2: EVOLUCIÓN DE LA CANTIDAD DE ÓRDENES DE COMPRA (OC) Y VALOR ---
    st.markdown("---")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📊 Cantidad de Órdenes de Compra (OC) por Mes")
        fig_oc = px.bar(
            df_trend,
            x='MES_EMISION',
            y='CANT_OC',
            text='CANT_OC',
            color='CANT_OC',
            color_continuous_scale='Greens',
            labels={'MES_EMISION': 'Mes', 'CANT_OC': 'Número de OCs'}
        )
        fig_oc.update_traces(texttemplate='%{text} OCs', textposition='outside')
        fig_oc.update_layout(template='plotly_white', showlegend=False)
        st.plotly_chart(fig_oc, use_container_width=True)

    with col_g2:
        st.subheader("💰 Evolución del Valor de Venta Total (S/)")
        fig_val = px.line(
            df_trend,
            x='MES_EMISION',
            y='VALOR_TOTAL',
            text=df_trend['VALOR_TOTAL'].apply(lambda x: f"S/ {x:,.0f}"),
            markers=True,
            labels={'MES_EMISION': 'Mes', 'VALOR_TOTAL': 'Venta Total (S/)'}
        )
        fig_val.update_traces(textposition='top center', line=dict(color='#2ca02c', width=3))
        fig_val.update_layout(template='plotly_white')
        st.plotly_chart(fig_val, use_container_width=True)

# --- ANÁLISIS POR VARIEDAD DE PRODUCTO ---
st.markdown("---")
st.subheader("🥑 Desglose por Variedad de Palta y Precios Ponderados")

if 'DESCRIPCION_PRODUCTO' in df.columns:
    df_prod = df.groupby('DESCRIPCION_PRODUCTO').agg(
        CANT_OC=('NRO_OC', 'nunique'),
        VOLUMEN=('UNIDADES_SOLICITADAS', 'sum'),
        VALOR_TOTAL=('VALOR_VENTA_SOLICITADO', 'sum'),
        PRECIO_MEDIO=('PRECIO_FINAL_NETO', 'mean')
    ).reset_index()
    
    df_prod['PRECIO_PONDERADO'] = df_prod['VALOR_TOTAL'] / df_prod['VOLUMEN']

    fig_prod = px.bar(
        df_prod,
        x='DESCRIPCION_PRODUCTO',
        y='VOLUMEN',
        text=df_prod['VOLUMEN'].apply(lambda x: f"{x:,.0f} un"),
        color='PRECIO_PONDERADO',
        color_continuous_scale='Tealgrn',
        labels={'DESCRIPCION_PRODUCTO': 'Variedad de Producto', 'VOLUMEN': 'Volumen Solicitado', 'PRECIO_PONDERADO': 'Precio Ponderado (S/)'},
        title='Volumen por Variedad y Precio Ponderado de Cierre'
    )
    fig_prod.update_traces(textposition='outside')
    fig_prod.update_layout(template='plotly_white', xaxis_tickangle=-20)
    st.plotly_chart(fig_prod, use_container_width=True)

# --- TABLA DETALLADA DE REGISTROS ---
st.markdown("---")
st.subheader("📋 Detalle Operativo de Solicitudes y Envíos")

with st.expander("Ver tabla completa de datos filtrados"):
    st.dataframe(df, use_container_width=True)
