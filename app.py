import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Inteligencia Comercial & Pricing | KCO Group",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS UI/UX AVANZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .metric-card {
        background: #ffffff;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 12px;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 22px;
        color: #0f172a;
        font-weight: 800;
        margin-top: 4px;
    }
    .metric-delta {
        font-size: 12px;
        font-weight: 600;
        margin-top: 4px;
    }
    .delta-up { color: #16a34a; }
    .delta-down { color: #dc2626; }
    .filter-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- MAESTRO DE PRODUCTOS (Configurable) ---
PRODUCT_WEIGHTS = {
    'PALTA-FUERTE-A-KG': 0.250,
    'PALTA-FUERTE-V-KG': 0.280,
    'PALTA-FUERTE-P-KG': 0.220,
    'PALTA-FUERTE-C-KG': 0.200,
    'PALTA-M-KG': 0.150
}
KG_PER_JABA = 18.0

# --- CARGA Y TRANSFORMACIÓN DE DATOS ---
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
            
    df = pd.read_excel(file_path, sheet_name=xls.sheet_names[0])
    df = df.loc[:, ~df.columns.duplicated()]

    if 'FECHA_EMISION' in df.columns:
        df['FECHA_EMISION'] = pd.to_datetime(df['FECHA_EMISION'], format='%d-%m-%Y', errors='coerce')
        df['MES_AÑO'] = df['FECHA_EMISION'].dt.to_period('M').astype(str)
        df['SEMANA'] = df['FECHA_EMISION'].dt.isocalendar().week
    
    # Estandarización de variables comerciales
    df['KILOS_SOLICITADOS'] = df['UNIDADES_SOLICITADAS'] if 'UNIDADES_SOLICITADAS' in df.columns else 0
    df['PRECIO_KG'] = df['PRECIO_FINAL_NETO'] if 'PRECIO_FINAL_NETO' in df.columns else 0
    df['VALOR_COMERCIAL'] = df['KILOS_SOLICITADOS'] * df['PRECIO_KG']
    
    # Estimaciones según Maestro de Productos
    def get_weight(prod_name):
        return PRODUCT_WEIGHTS.get(str(prod_name).strip().upper(), np.nan)
        
    df['PESO_FRUTO_KG'] = df['DESCRIPCION_PRODUCTO'].apply(get_weight)
    df['FRUTOS_ESTIMADOS'] = np.where(df['PESO_FRUTO_KG'].notna(), df['KILOS_SOLICITADOS'] / df['PESO_FRUTO_KG'], 0)
    df['JABAS_ESTIMADAS'] = df['KILOS_SOLICITADOS'] / KG_PER_JABA
    df['PRECIO_FRUTO_ESTIMADO'] = df['PRECIO_KG'] * df['PESO_FRUTO_KG']
    
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error en la ingesta de datos: {e}")
    st.stop()

# --- HEADER PRINCIPAL ---
st.markdown("## 📊 Dashboard de Inteligencia Comercial & Pricing | KCO Group")
st.markdown("Análisis estratégico de ventas a Plaza Vea: Comportamiento de demanda, evolución de precios y alertas comerciales.")

# --- FILTROS GLOBALES SUPERIORES ---
st.markdown('<div class="filter-container">', unsafe_allow_html=True)
st.markdown("#### 🎛️ Segmentación Estratégica")
f_col1, f_col2, f_col3, f_col4 = st.columns(4)

with f_col1:
    min_date, max_date = df_raw['FECHA_EMISION'].min(), df_raw['FECHA_EMISION'].max()
    date_range = st.date_input("Rango de Emisión", value=(min_date, max_date), min_value=min_date, max_value=max_date)

with f_col2:
    productos = sorted(df_raw['DESCRIPCION_PRODUCTO'].dropna().unique().tolist())
    selected_prods = st.multiselect("Variedad de Producto", options=productos, default=productos)

with f_col3:
    meses = sorted(df_raw['MES_AÑO'].dropna().unique().tolist())
    selected_meses = st.multiselect("Meses de Análisis", options=meses, default=meses)

with f_col4:
    rango_precios = st.slider("Rango de Precio/Kg (S/)", 
                              float(df_raw['PRECIO_KG'].min()), float(df_raw['PRECIO_KG'].max()), 
                              (float(df_raw['PRECIO_KG'].min()), float(df_raw['PRECIO_KG'].max())))

st.markdown('</div>', unsafe_allow_html=True)

# Aplicar Filtros
df = df_raw.copy()
if len(date_range) == 2:
    df = df[(df['FECHA_EMISION'] >= pd.to_datetime(date_range[0])) & (df['FECHA_EMISION'] <= pd.to_datetime(date_range[1]))]
if selected_prods:
    df = df[df['DESCRIPCION_PRODUCTO'].isin(selected_prods)]
if selected_meses:
    df = df[df['MES_AÑO'].isin(selected_meses)]
df = df[(df['PRECIO_KG'] >= rango_precios[0]) & (df['PRECIO_KG'] <= rango_precios[1])]

if df.empty:
    st.warning("⚠️ Sin datos para los filtros seleccionados.")
    st.stop()

# --- KPIS GERENCIALES (Cálculos Ponderados) ---
total_kg = df['KILOS_SOLICITADOS'].sum()
valor_total = df['VALOR_COMERCIAL'].sum()
precio_ponderado = valor_total / total_kg if total_kg > 0 else 0
ordenes_unicas = df['NRO_OC'].nunique()
kg_por_oc = total_kg / ordenes_unicas if ordenes_unicas > 0 else 0

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Volumen Total (Kg)</div><div class="metric-value">{total_kg:,.0f}</div></div>', unsafe_allow_html=True)
with kpi2:
    st.markdown(f'<div class="metric-card" style="border-left-color: #2ca02c;"><div class="metric-title">Valor Comercial (S/)</div><div class="metric-value">S/ {valor_total:,.0f}</div></div>', unsafe_allow_html=True)
with kpi3:
    st.markdown(f'<div class="metric-card" style="border-left-color: #ff7f0e;"><div class="metric-title">Precio Pond. Promedio</div><div class="metric-value">S/ {precio_ponderado:.2f} /kg</div></div>', unsafe_allow_html=True)
with kpi4:
    st.markdown(f'<div class="metric-card" style="border-left-color: #9467bd;"><div class="metric-title">Órdenes Únicas (OC)</div><div class="metric-value">{ordenes_unicas:,}</div></div>', unsafe_allow_html=True)
with kpi5:
    st.markdown(f'<div class="metric-card" style="border-left-color: #e377c2;"><div class="metric-title">Tamaño Prom. por OC</div><div class="metric-value">{kg_por_oc:,.0f} kg</div></div>', unsafe_allow_html=True)

# --- NAVEGACIÓN MULTIPESTAÑA (Top 3) ---
tab1, tab2, tab3 = st.tabs([
    "📈 1. Resumen Ejecutivo & Evolución Comercial", 
    "💰 2. Análisis de Pricing y Demanda", 
    "📋 3. Operativa, Alertas & Auditoría"
])

# ==========================================================
# TAB 1: RESUMEN EJECUTIVO Y EVOLUCIÓN
# ==========================================================
with tab1:
    # Agrupación temporal
    df_trend = df.groupby('MES_AÑO').agg(
        KG_TOTALES=('KILOS_SOLICITADOS', 'sum'),
        VALOR_TOTAL=('VALOR_COMERCIAL', 'sum'),
        CANT_OC=('NRO_OC', 'nunique')
    ).reset_index()
    df_trend['PRECIO_POND'] = df_trend['VALOR_TOTAL'] / df_trend['KG_TOTALES']
    
    col_t1, col_t2 = st.columns([1.5, 1])
    
    with col_t1:
        st.subheader("Evolución: Kilos Solicitados vs Precio Ponderado")
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Bar(
            x=df_trend['MES_AÑO'], y=df_trend['KG_TOTALES'], name='Volumen (Kg)',
            marker_color='#1f77b4', text=df_trend['KG_TOTALES'].apply(lambda x: f"{x:,.0f} kg"), textposition='outside'
        ))
        fig_dual.add_trace(go.Scatter(
            x=df_trend['MES_AÑO'], y=df_trend['PRECIO_POND'], name='Precio Pond. (S/)',
            mode='lines+markers+text', text=df_trend['PRECIO_POND'].apply(lambda x: f"S/ {x:.2f}"),
            textposition='top center', marker_color='#ff7f0e', line=dict(width=3), yaxis='y2'
        ))
        fig_dual.update_layout(
            yaxis=dict(title='Kilos', showgrid=False),
            yaxis2=dict(title='Precio (S/)', overlaying='y', side='right'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template='plotly_white', height=400, margin=dict(t=50, b=20)
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    with col_t2:
        st.subheader("Concentración de Valor Comercial")
        df_prod = df.groupby('DESCRIPCION_PRODUCTO').agg(VALOR=('VALOR_COMERCIAL', 'sum'), KG=('KILOS_SOLICITADOS', 'sum')).reset_index()
        fig_pie = px.pie(df_prod, names='DESCRIPCION_PRODUCTO', values='VALOR', hole=0.4, 
                         color_discrete_sequence=px.colors.sequential.Tealgrn_r)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(template='plotly_white', showlegend=False, height=400, margin=dict(t=50, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================================
# TAB 2: ANÁLISIS DE PRICING Y DEMANDA
# ==========================================================
with tab2:
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.subheader("Dispersión y Estrategia de Precios por Calibre")
        fig_box = px.box(
            df, x='DESCRIPCION_PRODUCTO', y='PRECIO_KG', color='DESCRIPCION_PRODUCTO',
            points='all', hover_data=['NRO_OC', 'KILOS_SOLICITADOS']
        )
        fig_box.update_layout(template='plotly_white', showlegend=False, height=400, 
                              xaxis_title="Producto", yaxis_title="Precio de Venta (S/)")
        st.plotly_chart(fig_box, use_container_width=True)

    with col_p2:
        st.subheader("Elasticidad: Relación Precio vs Kilos Solicitados")
        fig_scatter = px.scatter(
            df, x='PRECIO_KG', y='KILOS_SOLICITADOS', color='DESCRIPCION_PRODUCTO',
            size='VALOR_COMERCIAL', hover_data=['FECHA_EMISION', 'NRO_OC'],
            opacity=0.7
        )
        fig_scatter.update_layout(template='plotly_white', height=400,
                                  xaxis_title="Precio Facturado (S/)", yaxis_title="Volumen de la OC (Kg)")
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Matriz Comparativa de Pricing por Producto")
    
    df_pricing = df.groupby('DESCRIPCION_PRODUCTO').agg(
        KG_TOTALES=('KILOS_SOLICITADOS', 'sum'),
        VALOR_TOTAL=('VALOR_COMERCIAL', 'sum'),
        PRECIO_MIN=('PRECIO_KG', 'min'),
        PRECIO_MAX=('PRECIO_KG', 'max'),
        RANGO_PRECIOS=('PRECIO_KG', lambda x: x.max() - x.min()),
        CANT_CAMBIOS=('PRECIO_KG', 'nunique')
    ).reset_index()
    
    df_pricing['PRECIO_PONDERADO'] = df_pricing['VALOR_TOTAL'] / df_pricing['KG_TOTALES']
    
    # Formateo visual
    df_pricing_fmt = df_pricing.copy()
    for col in ['PRECIO_MIN', 'PRECIO_MAX', 'RANGO_PRECIOS', 'PRECIO_PONDERADO']:
        df_pricing_fmt[col] = df_pricing_fmt[col].apply(lambda x: f"S/ {x:.2f}")
    df_pricing_fmt['KG_TOTALES'] = df_pricing_fmt['KG_TOTALES'].apply(lambda x: f"{x:,.0f} kg")
    df_pricing_fmt['VALOR_TOTAL'] = df_pricing_fmt['VALOR_TOTAL'].apply(lambda x: f"S/ {x:,.0f}")
    
    st.dataframe(df_pricing_fmt, use_container_width=True, hide_index=True)

# ==========================================================
# TAB 3: OPERATIVA, ALERTAS & AUDITORÍA
# ==========================================================
with tab3:
    col_a1, col_a2 = st.columns([1, 2.5])
    
    with col_a1:
        st.markdown("### 🚨 Motor de Alertas")
        
        # Alertas lógicas simples basadas en la data filtrada
        umbral_concentracion = 60.0
        
        # 1. Concentración de producto
        if not df_prod.empty:
            prod_top = df_prod.loc[df_prod['VALOR'].idxmax()]
            part_top = (prod_top['VALOR'] / valor_total) * 100
            if part_top > umbral_concentracion:
                st.error(f"**Crítica:** Concentración excesiva. El producto **{prod_top['DESCRIPCION_PRODUCTO']}** representa el **{part_top:.1f}%** del valor comercial del periodo.")
        
        # 2. Precios anómalos o iguales a 0
        if (df['PRECIO_KG'] == 0).any():
            st.error("**Crítica:** Se detectaron órdenes de compra con Precio S/ 0.00. Requiere auditoría inmediata en la facturación.")
            
        # 3. Kilos igual a 0
        if (df['KILOS_SOLICITADOS'] == 0).any():
            st.warning("**Media:** Existen registros con Kilos solicitados igual a 0.")
            
        # 4. Cambios bruscos de precio
        if not df_pricing.empty and df_pricing['CANT_CAMBIOS'].max() > 3:
            st.info("**Informativa:** Alta volatilidad. Algunos productos registran más de 3 cambios de precio en el periodo seleccionado.")
            
    with col_a2:
        st.markdown("### 📋 Base de Datos Operativa & Estimaciones Logísticas")
        st.markdown("Detalle a nivel de Orden de Compra incluyendo **Jabas** y **Frutos** estimados según el maestro de pesos.")
        
        cols_mostrar = [
            'NRO_OC', 'FECHA_EMISION', 'DESCRIPCION_PRODUCTO', 'KILOS_SOLICITADOS', 
            'PRECIO_KG', 'VALOR_COMERCIAL', 'JABAS_ESTIMADAS', 'FRUTOS_ESTIMADOS'
        ]
        
        df_operativo = df[cols_mostrar].copy()
        df_operativo['PRECIO_KG'] = df_operativo['PRECIO_KG'].apply(lambda x: f"S/ {x:.2f}")
        df_operativo['VALOR_COMERCIAL'] = df_operativo['VALOR_COMERCIAL'].apply(lambda x: f"S/ {x:,.2f}")
        df_operativo['JABAS_ESTIMADAS'] = df_operativo['JABAS_ESTIMADAS'].apply(lambda x: f"{x:,.1f}")
        df_operativo['FRUTOS_ESTIMADOS'] = df_operativo['FRUTOS_ESTIMADOS'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
        
        st.dataframe(df_operativo, use_container_width=True, height=350)
