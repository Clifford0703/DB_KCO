import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Control Gerencial | Distribución de Paltas",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS UI/UX AVANZADOS ---
st.markdown("""
    <style>
    /* Estilo general y tipografía */
    .main { background-color: #f4f6f9; }
    
    /* Tarjetas de Métricas Ejecutivas */
    .metric-card {
        background: #ffffff;
        padding: 20px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border-left: 5px solid #2ca02c;
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 13px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 26px;
        color: #1e293b;
        font-weight: 700;
        margin-top: 5px;
    }
    
    /* Encabezados de sección */
    h3 {
        color: #0f172a;
        font-weight: 700;
        padding-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CARGA Y LIMPIEZA DE DATOS ---
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
    
    # Eliminar duplicados de columnas
    df = df.loc[:, ~df.columns.duplicated()]

    # Limpieza de fechas
    if 'FECHA_EMISION' in df.columns:
        df['FECHA_EMISION'] = pd.to_datetime(df['FECHA_EMISION'], format='%d-%m-%Y', errors='coerce')
    if 'FECHA_ENTREGA' in df.columns:
        df['FECHA_ENTREGA'] = pd.to_datetime(df['FECHA_ENTREGA'], format='%d-%m-%Y', errors='coerce')
    
    # Métricas de negocio base
    unidades = df['UNIDADES_SOLICITADAS'] if 'UNIDADES_SOLICITADAS' in df.columns else 0
    precio = df['PRECIO_FINAL_NETO'] if 'PRECIO_FINAL_NETO' in df.columns else 0
    
    df['VALOR_VENTA_SOLICITADO'] = unidades * precio
    df['TONELADAS_SOLICITADAS'] = unidades / 1000.0
    
    if 'UNIDADES_EN_DESPACHO' in df.columns:
        df['VALOR_VENTA_DESPACHADO'] = df['UNIDADES_EN_DESPACHO'] * precio
        
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error crítico al cargar el archivo de datos: {e}")
    st.stop()

# --- SIDEBAR DE FILTROS ---
st.sidebar.markdown("### 🎛️ Filtros Globales")
st.sidebar.markdown("---")

if 'FECHA_EMISION' in df_raw.columns and not df_raw['FECHA_EMISION'].isna().all():
    min_date = df_raw['FECHA_EMISION'].min()
    max_date = df_raw['FECHA_EMISION'].max()
    date_range = st.sidebar.date_input(
        "📅 Rango de Fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None

# Filtros condicionales
productos = ['Todos'] + sorted(df_raw['DESCRIPCION_PRODUCTO'].dropna().unique().tolist()) if 'DESCRIPCION_PRODUCTO' in df_raw.columns else ['Todos']
selected_producto = st.sidebar.selectbox("🥑 Variedad de Palta", productos)

tipos_oc = ['Todos'] + sorted(df_raw['TIPO_OC'].dropna().unique().tolist()) if 'TIPO_OC' in df_raw.columns else ['Todos']
selected_tipo_oc = st.sidebar.selectbox("📋 Tipo de Orden de Compra", tipos_oc)

# Aplicación de filtros
df = df_raw.copy()
if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df['FECHA_EMISION'] >= pd.to_datetime(start_date)) & (df['FECHA_EMISION'] <= pd.to_datetime(end_date))]

if selected_producto != 'Todos':
    df = df[df['DESCRIPCION_PRODUCTO'] == selected_producto]

if selected_tipo_oc != 'Todos':
    df = df[df['TIPO_OC'] == selected_tipo_oc]

# --- HEADER PRINCIPAL ---
st.markdown("## 🥑 Dashboard Gerencial: Control Operacional y Pricing")
st.markdown("Monitoreo ejecutivo de volúmenes, participación de mercado, tendencias mensuales y precios ponderados.")
st.markdown("---")

if df.empty:
    st.warning("⚠️ No se encontraron registros con los filtros seleccionados.")
    st.stop()

# --- CÁLCULO DE KPIS ---
total_oc = df['NRO_OC'].nunique() if 'NRO_OC' in df.columns else len(df)
volumen_unidades = df['UNIDADES_SOLICITADAS'].sum() if 'UNIDADES_SOLICITADAS' in df.columns else 0
volumen_tn = df['TONELADAS_SOLICITADAS'].sum() if 'TONELADAS_SOLICITADAS' in df.columns else 0
monto_total_venta = df['VALOR_VENTA_SOLICITADO'].sum() if 'VALOR_VENTA_SOLICITADO' in df.columns else 0
precio_ponderado_general = monto_total_venta / volumen_unidades if volumen_unidades > 0 else 0

# Tarjetas Métricas UI/UX (Evita cortes de texto con contenedores limpios)
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Órdenes (OC)</div>
            <div class="metric-value">{total_oc:,}</div>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Volumen Solicitado</div>
            <div class="metric-value">{volumen_unidades:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ff7f0e;">
            <div class="metric-title">Volumen en Tn</div>
            <div class="metric-value">{volumen_tn:,.2f} Tn</div>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #1f77b4;">
            <div class="metric-title">Venta Potencial</div>
            <div class="metric-value">S/ {monto_total_venta:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: #9467bd;">
            <div class="metric-title">Precio Ponderado</div>
            <div class="metric-value">S/ {precio_ponderado_general:.2f}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("")

# --- PROCESAMIENTO TEMPORAL Y PARTICIPACIÓN ---
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

    # --- FILA 1: TENDENCIA MENSUAL (DOBLE EJE) & PARTICIPACIÓN POR VALOR ---
    col_chart1, col_chart2 = st.columns([1.3, 1])

    with col_chart1:
        st.subheader("📈 Tendencia: Volumen vs Precio Ponderado")
        
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Bar(
            x=df_trend['MES_EMISION'],
            y=df_trend['VOLUMEN'],
            name='Volumen Solicitado',
            marker_color='#2ca02c',
            text=df_trend['VOLUMEN'].apply(lambda x: f"{x:,.0f}"),
            textposition='outside',
            yaxis='y'
        ))
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
            xaxis=dict(title='Mes'),
            yaxis=dict(title='Volumen', showgrid=False),
            yaxis2=dict(title='Precio Ponderado (S/)', overlaying='y', side='right', showgrid=True),
            legend=dict(x=0.01, y=0.98),
            template='plotly_white',
            hovermode='x unified',
            margin=dict(t=30, b=20, l=20, r=20),
            height=380
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    with col_chart2:
        st.subheader("🍩 Participación de Ventas por Mes")
        
        fig_pie = px.pie(
            df_trend,
            names='MES_EMISION',
            values='VALOR_TOTAL',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Greens_r
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(
            template='plotly_white',
            showlegend=False,
            margin=dict(t=30, b=20, l=20, r=20),
            height=380
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# --- FILA 2: ANÁLISIS DE PRODUCTOS Y EVOLUCIÓN DE OCS ---
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.subheader("🥑 Participación y Volumen por Variedad")
    if 'DESCRIPCION_PRODUCTO' in df.columns:
        df_prod = df.groupby('DESCRIPCION_PRODUCTO').agg(
            CANT_OC=('NRO_OC', 'nunique'),
            VOLUMEN=('UNIDADES_SOLICITADAS', 'sum'),
            VALOR_TOTAL=('VALOR_VENTA_SOLICITADO', 'sum')
        ).reset_index()
        
        df_prod['PRECIO_PONDERADO'] = df_prod['VALOR_TOTAL'] / df_prod['VOLUMEN']

        fig_prod = px.bar(
            df_prod,
            x='DESCRIPCION_PRODUCTO',
            y='VOLUMEN',
            text=df_prod['VOLUMEN'].apply(lambda x: f"{x:,.0f}"),
            color='PRECIO_PONDERADO',
            color_continuous_scale='Tealgrn',
            labels={'DESCRIPCION_PRODUCTO': 'Variedad', 'VOLUMEN': 'Volumen', 'PRECIO_PONDERADO': 'Precio Pond.'}
        )
        fig_prod.update_traces(textposition='outside')
        fig_prod.update_layout(
            template='plotly_white',
            xaxis_tickangle=-15,
            margin=dict(t=30, b=20, l=20, r=20),
            height=360
        )
        st.plotly_chart(fig_prod, use_container_width=True)

with col_chart4:
    st.subheader("📊 Cantidad de OCs y Dinámica Operativa")
    if 'FECHA_EMISION' in df.columns:
        fig_oc = px.line(
            df_trend,
            x='MES_EMISION',
            y='CANT_OC',
            markers=True,
            text=df_trend['CANT_OC'],
            labels={'MES_EMISION': 'Mes', 'CANT_OC': 'Número de Órdenes'}
        )
        fig_oc.update_traces(textposition='top center', line=dict(color='#1f77b4', width=3))
        fig_oc.update_layout(
            template='plotly_white',
            margin=dict(t=30, b=20, l=20, r=20),
            height=360
        )
        st.plotly_chart(fig_oc, use_container_width=True)

# --- TABLA DE DETALLE OPERATIVO ---
st.markdown("---")
st.subheader("📋 Detalle Operativo de Órdenes de Compra")

with st.expander("🔍 Ver tabla completa de registros filtrados"):
    st.dataframe(df, use_container_width=True)
