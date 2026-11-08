import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Inteligencia Comercial & Pricing | KCO Group",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS EJECUTIVOS UI/UX ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    
    /* Tarjetas KPI compactas y estilizadas */
    .metric-card {
        background: #ffffff;
        padding: 16px 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border-left: 4px solid #16a34a;
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 11px;
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
    .metric-sub {
        font-size: 11px;
        color: #94a3b8;
        margin-top: 2px;
    }
    
    /* Contenedores de notas analíticas para gráficos */
    .chart-insight {
        background-color: #f1f5f9;
        border-left: 3px solid #3b82f6;
        padding: 8px 14px;
        border-radius: 4px;
        font-size: 12.5px;
        color: #334155;
        margin-bottom: 16px;
        line-height: 1.4;
    }
    
    /* Contenedor de Filtros Horizontales Superiores */
    .filter-box {
        background-color: #ffffff;
        padding: 16px 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    </style>
""", unsafe_allow_html=True)

# --- MAESTRO DE PRODUCTOS (Pesos promedio reales y capacidad) ---
PRODUCT_WEIGHTS = {
    'PALTA-FUERTE-A-KG': 0.250,
    'PALTA-FUERTE-V-KG': 0.280,
    'PALTA-FUERTE-P-KG': 0.220,
    'PALTA-FUERTE-C-KG': 0.200,
    'PALTA-M-KG': 0.150
}
KG_PER_JABA = 18.0

# --- INGESTA Y LIMPIEZA DE DATOS ---
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

    # Fechas
    df['FECHA_EMISION'] = pd.to_datetime(df['FECHA_EMISION'], format='%d-%m-%Y', errors='coerce')
    df['MES_AÑO'] = df['FECHA_EMISION'].dt.to_period('M').astype(str)
    df['SEMANA'] = df['FECHA_EMISION'].dt.isocalendar().week
    df['DIA_SEM'] = df['FECHA_EMISION'].dt.day_name()
    
    # Estandarización de variables comerciales
    df['KILOS_SOLICITADOS'] = df['UNIDADES_SOLICITADAS'].fillna(0)
    df['PRECIO_KG'] = df['PRECIO_FINAL_NETO'].fillna(0)
    df['VALOR_COMERCIAL'] = df['KILOS_SOLICITADOS'] * df['PRECIO_KG']
    
    # Estimaciones logísticas
    def get_fruto_weight(prod):
        return PRODUCT_WEIGHTS.get(str(prod).strip().upper(), np.nan)
        
    df['PESO_FRUTO_KG'] = df['DESCRIPCION_PRODUCTO'].apply(get_fruto_weight)
    df['FRUTOS_EST'] = np.where(df['PESO_FRUTO_KG'].notna(), df['KILOS_SOLICITADOS'] / df['PESO_FRUTO_KG'], 0)
    df['JABAS_EST'] = df['KILOS_SOLICITADOS'] / KG_PER_JABA
    df['PRECIO_FRUTO_EST'] = df['PRECIO_KG'] * df['PESO_FRUTO_KG']
    
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error cargando archivo de datos: {e}")
    st.stop()

# --- HEADER PRINCIPAL ---
st.markdown("## 🥑 KCO Group | Intelligence & Pricing Dashboard")
st.markdown("Herramienta de análisis comercial para la negociación de órdenes de compra con **Plaza Vea**.")

# --- SEGMENTACIÓN SUPERIOR (HORIZONTAL) ---
st.markdown('<div class="filter-box">', unsafe_allow_html=True)
st.markdown("##### 🔍 Segmentación de Órdenes")
f1, f2, f3, f4 = st.columns(4)

with f1:
    min_date, max_date = df_raw['FECHA_EMISION'].min(), df_raw['FECHA_EMISION'].max()
    date_range = st.date_input("Periodo de Emisión", value=(min_date, max_date), min_value=min_date, max_value=max_date)

with f2:
    prods = sorted(df_raw['DESCRIPCION_PRODUCTO'].dropna().unique().tolist())
    selected_prods = st.multiselect("Variedad / Calibre", options=prods, default=prods)

with f3:
    meses_disponibles = sorted(df_raw['MES_AÑO'].dropna().unique().tolist())
    selected_meses = st.multiselect("Meses", options=meses_disponibles, default=meses_disponibles)

with f4:
    min_p, max_p = float(df_raw['PRECIO_KG'].min()), float(df_raw['PRECIO_KG'].max())
    rango_precios = st.slider("Rango Precio S/ por Kg", min_p, max_p, (min_p, max_p))

st.markdown('</div>', unsafe_allow_html=True)

# Filtro reactivo
df = df_raw.copy()
if len(date_range) == 2:
    df = df[(df['FECHA_EMISION'] >= pd.to_datetime(date_range[0])) & (df['FECHA_EMISION'] <= pd.to_datetime(date_range[1]))]
if selected_prods:
    df = df[df['DESCRIPCION_PRODUCTO'].isin(selected_prods)]
if selected_meses:
    df = df[df['MES_AÑO'].isin(selected_meses)]
df = df[(df['PRECIO_KG'] >= rango_precios[0]) & (df['PRECIO_KG'] <= rango_precios[1])]

if df.empty:
    st.warning("⚠️ No se encontraron órdenes para la combinación de filtros seleccionada.")
    st.stop()

# --- CÁLCULO DE MÉTRICAS GLOBALES PONDERADAS ---
total_kg = df['KILOS_SOLICITADOS'].sum()
valor_comercial_total = df['VALOR_COMERCIAL'].sum()
precio_ponderado_total = valor_comercial_total / total_kg if total_kg > 0 else 0
total_ocs = df['NRO_OC'].nunique()
kg_promedio_oc = total_kg / total_ocs if total_ocs > 0 else 0
total_jabas_est = df['JABAS_EST'].sum()

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Volumen Solicitado</div><div class="metric-value">{total_kg:,.0f} kg</div><div class="metric-sub">{total_kg/1000:,.1f} Toneladas</div></div>', unsafe_allow_html=True)
with kpi2:
    st.markdown(f'<div class="metric-card" style="border-left-color: #0284c7;"><div class="metric-title">Valor Facturado</div><div class="metric-value">S/ {valor_comercial_total:,.0f}</div><div class="metric-sub">Venta Total Bruta</div></div>', unsafe_allow_html=True)
with kpi3:
    st.markdown(f'<div class="metric-card" style="border-left-color: #f59e0b;"><div class="metric-title">Precio Pond. General</div><div class="metric-value">S/ {precio_ponderado_total:.2f}</div><div class="metric-sub">Por kg entregado</div></div>', unsafe_allow_html=True)
with kpi4:
    st.markdown(f'<div class="metric-card" style="border-left-color: #8b5cf6;"><div class="metric-title">Órdenes Únicas</div><div class="metric-value">{total_ocs:,}</div><div class="metric-sub">{kg_promedio_oc:,.0f} kg / orden</div></div>', unsafe_allow_html=True)
with kpi5:
    st.markdown(f'<div class="metric-card" style="border-left-color: #ec4899;"><div class="metric-title">Jabas Estimadas</div><div class="metric-value">{total_jabas_est:,.0f}</div><div class="metric-sub">Capacidad 18 kg/jaba</div></div>', unsafe_allow_html=True)

# --- NAVEGACIÓN EN 2 PESTAÑAS CONSOLIDADAS ---
tab1, tab2 = st.tabs([
    "📊 1. Resumen Ejecutivo & Evolución Comercial",
    "📈 2. Análisis de Precios (Pricing), Variaciones % & Alertas"
])

# ==========================================================
# PESTAÑA 1: RESUMEN EJECUTIVO & EVOLUCIÓN COMERCIAL
# ==========================================================
with tab1:
    # Agrupación temporal mensual
    df_trend = df.groupby('MES_AÑO').agg(
        KG_TOTALES=('KILOS_SOLICITADOS', 'sum'),
        VALOR_TOTAL=('VALOR_COMERCIAL', 'sum'),
        ORDENES=('NRO_OC', 'nunique')
    ).reset_index()
    df_trend['PRECIO_POND'] = df_trend['VALOR_TOTAL'] / df_trend['KG_TOTALES']
    
    # Variaciones respecto al mes anterior
    df_trend['VAR_KG_PCT'] = df_trend['KG_TOTALES'].pct_change() * 100
    df_trend['VAR_PRECIO_PCT'] = df_trend['PRECIO_POND'].pct_change() * 100
    df_trend['VAR_VALOR_PCT'] = df_trend['VALOR_TOTAL'].pct_change() * 100

    col_g1, col_g2 = st.columns([1.5, 1])

    with col_g1:
        st.subheader("Evolución Mensual: Volumen (Kg) vs Precio Ponderado")
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Bar(
            x=df_trend['MES_AÑO'], y=df_trend['KG_TOTALES'], name='Volumen (Kg)',
            marker_color='#15803d', text=df_trend['KG_TOTALES'].apply(lambda x: f"{x/1000:,.1f} Tn"),
            textposition='outside', yaxis='y'
        ))
        fig_dual.add_trace(go.Scatter(
            x=df_trend['MES_AÑO'], y=df_trend['PRECIO_POND'], name='Precio Pond. (S/)',
            mode='lines+markers+text', text=df_trend['PRECIO_POND'].apply(lambda x: f"S/{x:.2f}"),
            textposition='top center', marker_color='#ea580c', line=dict(width=3), yaxis='y2'
        ))
        fig_dual.update_layout(
            yaxis=dict(title='Volumen Total (Kg)', showgrid=False),
            yaxis2=dict(title='Precio Ponderado (S/)', overlaying='y', side='right', showgrid=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template='plotly_white', height=390, margin=dict(t=30, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_dual, use_container_width=True)
        
        # Comentario analítico dinámico
        max_vol_mes = df_trend.loc[df_trend['KG_TOTALES'].idxmax()]['MES_AÑO']
        max_p_mes = df_trend.loc[df_trend['PRECIO_POND'].idxmax()]['MES_AÑO']
        st.markdown(f"""
        <div class="chart-insight">
            💡 <b>Insight Comercial:</b> El mes de mayor abastecimiento fue <b>{max_vol_mes}</b>. El pico en el precio promedio ponderado ocurrió en <b>{max_p_mes}</b>. 
            Observa cómo ante ajustes de precio, Plaza Vea modula el volumen semanal solicitado.
        </div>
        """, unsafe_allow_html=True)

    with col_g2:
        st.subheader("Mix y Concentración por Producto")
        df_prod = df.groupby('DESCRIPCION_PRODUCTO').agg(
            VALOR=('VALOR_COMERCIAL', 'sum'),
            KG=('KILOS_SOLICITADOS', 'sum')
        ).reset_index()
        
        fig_pie = px.pie(
            df_prod, names='DESCRIPCION_PRODUCTO', values='VALOR', hole=0.45,
            color_discrete_sequence=px.colors.sequential.Greens_r
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(template='plotly_white', showlegend=False, height=390, margin=dict(t=30, b=20, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)
        
        top_prod = df_prod.loc[df_prod['VALOR'].idxmax()]
        part_top = (top_prod['VALOR'] / valor_comercial_total) * 100
        st.markdown(f"""
        <div class="chart-insight">
            📌 <b>Concentración:</b> <b>{top_prod['DESCRIPCION_PRODUCTO']}</b> representa el <b>{part_top:.1f}%</b> de la facturación global, constituyendo el ancla principal de negociación.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📋 Matriz de Variación Intermensual (MoM)")
    
    # Tabla formal de variación intermensual
    df_var_display = df_trend[['MES_AÑO', 'KG_TOTALES', 'VAR_KG_PCT', 'PRECIO_POND', 'VAR_PRECIO_PCT', 'VALOR_TOTAL', 'VAR_VALOR_PCT']].copy()
    df_var_display.columns = ['Mes', 'Kilos Solicitados', 'Var. Kg %', 'Precio Ponderado', 'Var. Precio %', 'Valor Venta (S/)', 'Var. Valor %']
    
    st.dataframe(
        df_var_display.style.format({
            'Kilos Solicitados': '{:,.0f} kg',
            'Var. Kg %': '{:+.1f}%',
            'Precio Ponderado': 'S/ {:.2f}',
            'Var. Precio %': '{:+.1f}%',
            'Valor Venta (S/)': 'S/ {:,.0f}',
            'Var. Valor %': '{:+.1f}%'
        }).highlight_null(color='#f1f5f9'),
        use_container_width=True, hide_index=True
    )

# ==========================================================
# PESTAÑA 2: PRICING, VARIACIONES % & AUDITORÍA
# ==========================================================
with tab2:
    st.subheader("🔍 Auditoría de Cambios de Precio por Producto")
    st.markdown("Trazabilidad histórica de variaciones en soles y porcentaje respecto a la orden anterior.")
    
    # Detección cronológica de cambios de precio por producto
    df_sorted = df.sort_values(by=['DESCRIPCION_PRODUCTO', 'FECHA_EMISION'])
    changes_list = []
    
    for prod_name, group in df_sorted.groupby('DESCRIPCION_PRODUCTO'):
        # Consolidar por fecha y precio
        daily = group.groupby(['FECHA_EMISION', 'PRECIO_KG'])['KILOS_SOLICITADOS'].sum().reset_index()
        daily = daily.sort_values('FECHA_EMISION')
        daily['PRECIO_ANTERIOR'] = daily['PRECIO_KG'].shift(1)
        daily['DIF_SOLES'] = daily['PRECIO_KG'] - daily['PRECIO_ANTERIOR']
        daily['VAR_PCT'] = (daily['DIF_SOLES'] / daily['PRECIO_ANTERIOR']) * 100
        daily['PRODUCTO'] = prod_name
        # Filtrar solo cuando ocurrió un cambio
        c = daily[daily['DIF_SOLES'].notna() & (daily['DIF_SOLES'] != 0)]
        changes_list.append(c)

    if changes_list and not pd.concat(changes_list).empty:
        all_changes = pd.concat(changes_list).sort_values('FECHA_EMISION', ascending=False)
        all_changes['FECHA_STR'] = all_changes['FECHA_EMISION'].dt.strftime('%d-%m-%Y')
        
        # Gráfico de barras de variaciones porcentuales recientes
        fig_var = px.bar(
            all_changes.head(20),
            x='FECHA_STR', y='VAR_PCT', color='VAR_PCT',
            text=all_changes.head(20)['VAR_PCT'].apply(lambda x: f"{x:+.1f}%"),
            color_continuous_scale='RdYlGn',
            labels={'FECHA_STR': 'Fecha de Emisión', 'VAR_PCT': 'Variación %', 'PRODUCTO': 'Producto'},
            hover_data=['PRODUCTO', 'PRECIO_ANTERIOR', 'PRECIO_KG', 'KILOS_SOLICITADOS']
        )
        fig_var.update_traces(textposition='outside')
        fig_var.update_layout(template='plotly_white', height=360, margin=dict(t=30, b=20))
        st.plotly_chart(fig_var, use_container_width=True)
        
        st.markdown(f"""
        <div class="chart-insight">
            💡 <b>Lectura de Fluctuación:</b> Se visualizan los últimos 20 cambios de precio pactados. Las barras positivas reflejan alzas negociadas y las negativas reducciones aplicadas en las órdenes de compra.
        </div>
        """, unsafe_allow_html=True)
        
        # Tabla detallada de cambios
        with st.expander("Ver tabla completa de historial de cambios de precio"):
            display_changes = all_changes[['FECHA_STR', 'PRODUCTO', 'PRECIO_ANTERIOR', 'PRECIO_KG', 'DIF_SOLES', 'VAR_PCT', 'KILOS_SOLICITADOS']].copy()
            display_changes.columns = ['Fecha', 'Producto', 'Precio Anterior', 'Precio Nuevo', 'Dif (S/)', 'Var %', 'Kilos en la OC']
            st.dataframe(
                display_changes.style.format({
                    'Precio Anterior': 'S/ {:.2f}',
                    'Precio Nuevo': 'S/ {:.2f}',
                    'Dif (S/)': 'S/ {:+.2f}',
                    'Var %': '{:+.2f}%',
                    'Kilos en la OC': '{:,.0f} kg'
                }),
                use_container_width=True, hide_index=True
            )
    else:
        st.info("No se registraron fluctuaciones de precio dentro del rango seleccionado.")

    st.markdown("---")
    
    # Análisis de Dispersión y Elasticidad
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.subheader("Dispersión de Precios por Variedad")
        fig_box = px.box(
            df, x='DESCRIPCION_PRODUCTO', y='PRECIO_KG', color='DESCRIPCION_PRODUCTO',
            points='all', hover_data=['NRO_OC', 'KILOS_SOLICITADOS']
        )
        fig_box.update_layout(template='plotly_white', showlegend=False, height=380, xaxis_title="Calibre", yaxis_title="Precio S/")
        st.plotly_chart(fig_box, use_container_width=True)
        st.markdown("""
        <div class="chart-insight">
            📌 <b>Rango y Volatilidad:</b> Cada punto representa una orden. Permite identificar la dispersión entre calibres y verificar si los precios se mantienen dentro de la banda aceptable.
        </div>
        """, unsafe_allow_html=True)

    with col_e2:
        st.subheader("Relación Volumen vs Precio")
        fig_scat = px.scatter(
            df, x='PRECIO_KG', y='KILOS_SOLICITADOS', color='DESCRIPCION_PRODUCTO',
            size='VALOR_COMERCIAL', hover_data=['FECHA_EMISION', 'NRO_OC'], opacity=0.75
        )
        fig_scat.update_layout(template='plotly_white', height=380, xaxis_title="Precio (S/)", yaxis_title="Volumen (Kg)")
        st.plotly_chart(fig_scat, use_container_width=True)
        st.markdown("""
        <div class="chart-insight">
            📌 <b>Sensibilidad de Demanda:</b> Evalúa si los pedidos de mayor volumen se cierran a precios inferiores o si la demanda de Plaza Vea es inelástica en calibres clave.
        </div>
        """, unsafe_allow_html=True)

    # Detalle Operativo y Estimaciones
    st.markdown("---")
    st.subheader("📋 Detalle Operativo de Órdenes & Estimaciones")
    cols_grid = ['NRO_OC', 'FECHA_EMISION', 'DESCRIPCION_PRODUCTO', 'KILOS_SOLICITADOS', 'PRECIO_KG', 'VALOR_COMERCIAL', 'JABAS_EST', 'FRUTOS_EST']
    df_grid = df[cols_grid].copy()
    df_grid['FECHA_EMISION'] = df_grid['FECHA_EMISION'].dt.strftime('%d-%m-%Y')
    
    st.dataframe(
        df_grid.style.format({
            'KILOS_SOLICITADOS': '{:,.0f} kg',
            'PRECIO_KG': 'S/ {:.2f}',
            'VALOR_COMERCIAL': 'S/ {:,.2f}',
            'JABAS_EST': '{:,.1f}',
            'FRUTOS_EST': '{:,.0f}'
        }),
        use_container_width=True, height=320, hide_index=True
    )
