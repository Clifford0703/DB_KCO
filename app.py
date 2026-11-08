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
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS UI/UX AVANZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* Tarjetas de Métricas Ejecutivas */
    .metric-card {
        background: #ffffff;
        padding: 18px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        border-left: 4px solid #2ca02c;
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 12px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 24px;
        color: #1e293b;
        font-weight: 700;
        margin-top: 4px;
    }
    
    /* Contenedor de Filtros Superiores */
    .filter-container {
        background-color: #ffffff;
        padding: 15px 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
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
    despachadas = df['UNIDADES_EN_DESPACHO'] if 'UNIDADES_EN_DESPACHO' in df.columns else 0
    precio = df['PRECIO_FINAL_NETO'] if 'PRECIO_FINAL_NETO' in df.columns else 0
    
    df['VALOR_VENTA_SOLICITADO'] = unidades * precio
    df['VALOR_VENTA_DESPACHADO'] = despachadas * precio
    df['TONELADAS_SOLICITADAS'] = unidades / 1000.0
    
    # Indicador de cumplimiento (Fill Rate)
    df['CUMPLIMIENTO_VOLUMEN'] = (despachadas / unidades.replace(0, 1)) * 100
        
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error crítico al cargar el archivo de datos: {e}")
    st.stop()

# --- HEADER PRINCIPAL ---
st.markdown("## 🥑 Dashboard Gerencial: Control Operacional y Pricing")
st.markdown("Monitoreo ejecutivo de volúmenes, participación de mercado, tendencias mensuales, precios ponderados y nivel de servicio.")
st.markdown("---")

# --- PANEL DE FILTROS SUPERIOR (Evita deformaciones en barra lateral) ---
with st.container():
    st.markdown("### 🎛️ Segmentación de Datos")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        if 'FECHA_EMISION' in df_raw.columns and not df_raw['FECHA_EMISION'].isna().all():
            min_date = df_raw['FECHA_EMISION'].min()
            max_date = df_raw['FECHA_EMISION'].max()
            date_range = st.date_input(
                "📅 Rango de Fechas de Emisión",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        else:
            date_range = None

    with f_col2:
        productos = ['Todos'] + sorted(df_raw['DESCRIPCION_PRODUCTO'].dropna().unique().tolist()) if 'DESCRIPCION_PRODUCTO' in df_raw.columns else ['Todos']
        selected_producto = st.selectbox("🥑 Variedad de Palta", productos)

    with f_col3:
        tipos_oc = ['Todos'] + sorted(df_raw['TIPO_OC'].dropna().unique().tolist()) if 'TIPO_OC' in df_raw.columns else ['Todos']
        selected_tipo_oc = st.selectbox("📋 Tipo de Orden de Compra", tipos_oc)

# Aplicación de filtros
df = df_raw.copy()
if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    df = df[(df['FECHA_EMISION'] >= pd.to_datetime(start_date)) & (df['FECHA_EMISION'] <= pd.to_datetime(end_date))]

if selected_producto != 'Todos':
    df = df[df['DESCRIPCION_PRODUCTO'] == selected_producto]

if selected_tipo_oc != 'Todos':
    df = df[df['TIPO_OC'] == selected_tipo_oc]

if df.empty:
    st.warning("⚠️ No se encontraron registros con los filtros seleccionados.")
    st.stop()

st.markdown("---")

# --- CÁLCULO DE KPIS GLOBALES ---
total_oc = df['NRO_OC'].nunique() if 'NRO_OC' in df.columns else len(df)
volumen_unidades = df['UNIDADES_SOLICITADAS'].sum() if 'UNIDADES_SOLICITADAS' in df.columns else 0
volumen_tn = df['TONELADAS_SOLICITADAS'].sum() if 'TONELADAS_SOLICITADAS' in df.columns else 0
monto_total_venta = df['VALOR_VENTA_SOLICITADO'].sum() if 'VALOR_VENTA_SOLICITADO' in df.columns else 0
precio_ponderado_general = monto_total_venta / volumen_unidades if volumen_unidades > 0 else 0
fill_rate_promedio = df['CUMPLIMIENTO_VOLUMEN'].mean() if 'CUMPLIMIENTO_VOLUMEN' in df.columns else 0

# Tarjetas Métricas Superiores
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

# --- PROCESAMIENTO TEMPORAL ---
if 'FECHA_EMISION' in df.columns:
    df['MES_EMISION'] = df['FECHA_EMISION'].dt.to_period('M').astype(str)
    
    df_trend = df.groupby('MES_EMISION').agg(
        CANT_OC=('NRO_OC', 'nunique'),
        VOLUMEN=('UNIDADES_SOLICITADAS', 'sum'),
        TONELADAS=('TONELADAS_SOLICITADAS', 'sum'),
        VALOR_TOTAL=('VALOR_VENTA_SOLICITADO', 'sum'),
        VALOR_DESPACHADO=('VALOR_VENTA_DESPACHADO', 'sum')
    ).reset_index()
    
    df_trend['PRECIO_PONDERADO'] = df_trend['VALOR_TOTAL'] / df_trend['VOLUMEN']

# --- CREACIÓN DE PESTAÑAS (TABS) ---
tab1, tab2, tab3 = st.tabs([
    "📈 1. Tendencias y Volúmenes", 
    "💰 2. Análisis Financiero y OTIF", 
    "📋 3. Detalle Operativo"
])

with tab1:
    st.markdown("### Análisis de Evolución Comercial")
    
    col_chart1, col_chart2 = st.columns([1.3, 1])

    with col_chart1:
        st.subheader("Tendencia: Volumen vs Precio Ponderado")
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
        st.subheader("Participación de Ventas por Mes")
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

    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.subheader("Volumen por Variedad de Producto")
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
            fig_prod.update_layout(template='plotly_white', xaxis_tickangle=-15, height=360)
            st.plotly_chart(fig_prod, use_container_width=True)

    with col_chart4:
        st.subheader("Dinámica de Órdenes de Compra (OC)")
        fig_oc = px.line(
            df_trend,
            x='MES_EMISION',
            y='CANT_OC',
            markers=True,
            text=df_trend['CANT_OC'],
            labels={'MES_EMISION': 'Mes', 'CANT_OC': 'Número de Órdenes'}
        )
        fig_oc.update_traces(textposition='top center', line=dict(color='#1f77b4', width=3))
        fig_oc.update_layout(template='plotly_white', height=360)
        st.plotly_chart(fig_oc, use_container_width=True)

with tab2:
    st.markdown("### Análisis Financiero Avanzado y Nivel de Servicio (OTIF/Fill Rate)")
    
    f_col_a, f_col_b = st.columns(2)
    
    with f_col_a:
        st.subheader("💵 Comparativa: Venta Solicitada vs Despachada por Mes")
        fig_fin = go.Figure()
        fig_fin.add_trace(go.Bar(
            x=df_trend['MES_EMISION'],
            y=df_trend['VALOR_TOTAL'],
            name='Venta Solicitada (S/)',
            marker_color='#2ca02c'
        ))
        fig_fin.add_trace(go.Bar(
            x=df_trend['MES_EMISION'],
            y=df_trend['VALOR_DESPACHADO'],
            name='Venta Despachada (S/)',
            marker_color='#1f77b4'
        ))
        fig_fin.update_layout(
            barmode='group',
            template='plotly_white',
            xaxis=dict(title='Mes'),
            yaxis=dict(title='Soles (S/)'),
            height=380
        )
        st.plotly_chart(fig_fin, use_container_width=True)

    with f_col_b:
        st.subheader("📦 Cumplimiento Operativo (Fill Rate por Tipo de OC)")
        if 'TIPO_OC' in df.columns and 'CUMPLIMIENTO_VOLUMEN' in df.columns:
            df_otif = df.groupby('TIPO_OC')['CUMPLIMIENTO_VOLUMEN'].mean().reset_index()
            fig_otif = px.bar(
                df_otif,
                x='TIPO_OC',
                y='CUMPLIMIENTO_VOLUMEN',
                text=df_otif['CUMPLIMIENTO_VOLUMEN'].apply(lambda x: f"{x:.1f}%"),
                color='CUMPLIMIENTO_VOLUMEN',
                color_continuous_scale='Greens',
                labels={'TIPO_OC': 'Tipo de OC', 'CUMPLIMIENTO_VOLUMEN': 'Fill Rate Promedio (%)'}
            )
            fig_otif.update_traces(textposition='outside')
            fig_otif.update_layout(template='plotly_white', height=380, yaxis_range=[0, 110])
            st.plotly_chart(fig_otif, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Distribución y Dispersión de Precios Unitarios")
    if 'PRECIO_FINAL_NETO' in df.columns and 'DESCRIPCION_PRODUCTO' in df.columns:
        fig_box = px.box(
            df,
            x='DESCRIPCION_PRODUCTO',
            y='PRECIO_FINAL_NETO',
            color='DESCRIPCION_PRODUCTO',
            labels={'DESCRIPCION_PRODUCTO': 'Variedad', 'PRECIO_FINAL_NETO': 'Precio Final Neto (S/)'},
            title='Variabilidad de Precios por Variedad de Palta'
        )
        fig_box.update_layout(template='plotly_white', showlegend=False, height=400)
        st.plotly_chart(fig_box, use_container_width=True)

with tab3:
    st.markdown("### 📋 Detalle Operativo de Órdenes de Compra")
    st.markdown("Visualización completa de los registros filtrados para auditoría y control operativo.")
    st.dataframe(df, use_container_width=True)
