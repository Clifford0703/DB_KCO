import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Inteligencia Comercial & Pricing | KCO Group",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PALETA CORPORATIVA ---
COLOR_PRIMARY = "#1b4332"
COLOR_BARRA_CLARA = "#52b788"      # Verde esmeralda luminoso
COLOR_BARRA_BORDE = "#2d6a4f"      # Contorno contrastado
COLOR_ACCENT = "#d97706"           # Línea de precio en ámbar
COLOR_NEUTRAL = "#0f172a"
COLOR_INFO = "#0284c7"
COLOR_MERCADO = "#64748b"

VARIEDAD_COLORS = {
    'PALTA-FUERTE-A-KG': '#1b4332',
    'PALTA-FUERTE-V-KG': '#0284c7',
    'PALTA-FUERTE-P-KG': '#d97706',
    'PALTA-FUERTE-C-KG': '#7c3aed',
    'PALTA-M-KG':        '#16a34a'
}

# --- ESTILOS CSS FULL-WIDTH Y MOBILE-FIRST ---
st.markdown(f"""
    <style>
    .main {{ 
        background-color: #f8fafc; 
    }}
    .block-container {{
        max-width: 100% !important;
        padding-top: 3.6rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }}
    
    .dashboard-title {{
        font-size: clamp(1.3rem, 2.8vw, 2.2rem) !important;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.25;
        margin-top: 5px;
        margin-bottom: 6px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}
    
    h3 {{
        margin-top: 15px !important;
        padding-top: 5px !important;
        font-size: clamp(1.1rem, 2vw, 1.4rem) !important;
    }}

    /* GRID RESPONSIVO PARA KPIS */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin-bottom: 16px;
        width: 100%;
    }}
    
    .metric-card {{
        background: #ffffff;
        padding: 14px 16px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border-left: 5px solid {COLOR_PRIMARY};
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-sizing: border-box;
        min-width: 0;
    }}
    .metric-title {{
        font-size: 11px;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .metric-value {{
        font-size: clamp(17px, 1.8vw, 23px);
        color: {COLOR_NEUTRAL};
        font-weight: 800;
        margin-top: 4px;
        word-break: break-word;
        line-height: 1.2;
    }}
    .metric-sub {{
        font-size: 11px;
        color: #94a3b8;
        margin-top: 3px;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    .chart-insight {{
        background-color: #f1f5f9;
        border-left: 4px solid {COLOR_PRIMARY};
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 12px;
        color: #334155;
        margin-top: 8px;
        margin-bottom: 16px;
        line-height: 1.45;
        width: 100% !important;
    }}

    .drilldown-bar {{
        background: #e0f2fe;
        border-left: 4px solid #0284c7;
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 13.5px;
        font-weight: 700;
        color: #0369a1;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }}
    
    .header-metadata {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 8px;
        color: #64748b;
        font-size: 12.5px;
        width: 100% !important;
    }}
    
    .footer-credits {{
        border-top: 1px solid #e2e8f0;
        padding-top: 16px;
        margin-top: 30px;
        text-align: center;
        color: #64748b;
        font-size: 11.5px;
        width: 100% !important;
    }}

    /* SIDEBAR COMPACTO */
    section[data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 1.8rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    section[data-testid="stSidebar"] .stDateInput, 
    section[data-testid="stSidebar"] .stMultiSelect, 
    section[data-testid="stSidebar"] .stRadio {{
        margin-bottom: 0.6rem !important;
    }}

    /* CONTROL SEGMENTADO TÁCTIL */
    div[data-testid="stRadio"] > div {{
        background: #e2e8f0;
        padding: 4px;
        border-radius: 12px;
        gap: 4px;
    }}
    div[data-testid="stRadio"] > div > label {{
        flex: 1 1 0;
        background: transparent;
        padding: 10px 14px;
        border-radius: 9px;
        text-align: center;
        font-weight: 700;
        font-size: 13.5px;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease;
        margin: 0 !important;
    }}
    div[data-testid="stRadio"] > div > label[data-checked="true"] {{
        background: {COLOR_PRIMARY} !important;
        color: #ffffff !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.12);
    }}
    div[data-testid="stRadio"] > div > label[data-checked="true"] p {{
        color: #ffffff !important;
    }}

    /* MEDIA QUERIES PARA CELULAR */
    @media (max-width: 768px) and (orientation: portrait) {{
        .block-container {{
            padding-top: 3.2rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }}
        .kpi-grid {{
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 8px !important;
        }}
        .kpi-grid > div:nth-child(5) {{
            grid-column: span 2;
        }}
        .metric-card {{ padding: 10px 12px; }}
        .metric-title {{ font-size: 9.5px; }}
        .metric-value {{ font-size: 17px; }}
        .metric-sub {{ font-size: 10px; }}
        .header-metadata {{
            flex-direction: column;
            align-items: flex-start;
            font-size: 11px;
        }}
    }}

    @media (max-width: 950px) and (orientation: landscape) {{
        .block-container {{
            padding-top: 3.2rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }}
        .kpi-grid {{
            grid-template-columns: repeat(5, 1fr) !important;
            gap: 6px !important;
        }}
        .metric-card {{ padding: 8px 10px; }}
        .metric-value {{ font-size: 15px; }}
        .metric-title, .metric-sub {{ font-size: 9px; }}
    }}
    </style>
""", unsafe_allow_html=True)

PLOTLY_CONFIG = {
    'displayModeBar': False,
    'responsive': True
}

# --- CONTROL DE ESTADO DE SESIÓN PARA DRILL-DOWN ---
if 'drilldown_mes' not in st.session_state:
    st.session_state.drilldown_mes = None

# --- MAESTRO DE PRODUCTOS ---
PRODUCT_WEIGHTS = {
    'PALTA-FUERTE-A-KG': 0.250,
    'PALTA-FUERTE-V-KG': 0.280,
    'PALTA-FUERTE-P-KG': 0.220,
    'PALTA-FUERTE-C-KG': 0.200,
    'PALTA-M-KG': 0.150
}
KG_PER_JABA = 18.0

def style_semaphore(val):
    if pd.isna(val):
        return ''
    if val > 2.0:
        return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
    elif val < -2.0:
        return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
    else:
        return 'background-color: #fef9c3; color: #854d0e; font-weight: bold;'

# --- CARGA Y TRANSFORMACIÓN DE DATOS ---
@st.cache_data
def load_all_data():
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

    df['FECHA_EMISION'] = pd.to_datetime(df['FECHA_EMISION'], format='%d-%m-%Y', errors='coerce')
    df['MES_AÑO'] = df['FECHA_EMISION'].dt.strftime('%Y-%m')
    df['SEMANA_AÑO'] = df['FECHA_EMISION'].dt.strftime('%Y-W%V')
    
    df['KILOS_SOLICITADOS'] = df['UNIDADES_SOLICITADAS'].fillna(0)
    df['PRECIO_KG'] = df['PRECIO_FINAL_NETO'].fillna(0)
    df['VALOR_COMERCIAL'] = df['KILOS_SOLICITADOS'] * df['PRECIO_KG']
    
    def get_fruto_weight(prod):
        return PRODUCT_WEIGHTS.get(str(prod).strip().upper(), np.nan)
        
    df['PESO_FRUTO_KG'] = df['DESCRIPCION_PRODUCTO'].apply(get_fruto_weight)
    df['FRUTOS_EST'] = np.where(df['PESO_FRUTO_KG'].notna(), df['KILOS_SOLICITADOS'] / df['PESO_FRUTO_KG'], 0)
    df['JABAS_EST'] = df['KILOS_SOLICITADOS'] / KG_PER_JABA
    df['PRECIO_FRUTO_EST'] = df['PRECIO_KG'] * df['PESO_FRUTO_KG']
    
    df_mercado = pd.DataFrame()
    mkt_file = "reporte_fuerte.xls"
    if os.path.exists(mkt_file):
        try:
            try:
                mkt_xls = pd.ExcelFile(mkt_file, engine='xlrd')
            except Exception:
                mkt_xls = pd.ExcelFile(mkt_file, engine='openpyxl')
            df_m = pd.read_excel(mkt_file, sheet_name=mkt_xls.sheet_names[0])
            df_m['Fecha'] = pd.to_datetime(df_m['Fecha'], errors='coerce')
            df_m = df_m.dropna(subset=['Fecha', 'Palta Fuerte']).sort_values('Fecha')
            df_m['MES_AÑO'] = df_m['Fecha'].dt.strftime('%Y-%m')
            df_m['SEMANA_AÑO'] = df_m['Fecha'].dt.strftime('%Y-W%V')
            df_mercado = df_m
        except Exception:
            df_mercado = pd.DataFrame()
            
    timestamp_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return df, df_mercado, timestamp_actualizacion

try:
    df_raw, df_mercado_raw, update_time = load_all_data()
except Exception as e:
    st.error(f"Error cargando los archivos: {e}")
    st.stop()

# --- SIDEBAR: PANEL DE CONTROL ---
with st.sidebar:
    st.markdown("### 🥑 Panel de Control")
    st.caption("Filtros y parámetros operativos")
    
    min_date, max_date = df_raw['FECHA_EMISION'].min(), df_raw['FECHA_EMISION'].max()
    date_range = st.date_input("📅 Rango de Fechas", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    
    prods = sorted(df_raw['DESCRIPCION_PRODUCTO'].dropna().unique().tolist())
    selected_prods = st.multiselect("🏷️ Variedad / Calibre", options=prods, default=prods)
    
    periodo_seleccionado = st.radio(
        "⏱️ Agrupación Temporal",
        options=["Mensual", "Semanal"],
        horizontal=True
    )
    
    st.divider()
    st.caption("KCO Group — Intelligence & Pricing")

col_periodo = 'MES_AÑO' if periodo_seleccionado == "Mensual" else 'SEMANA_AÑO'
label_periodo = "Mes" if periodo_seleccionado == "Mensual" else "Semana"

# Filtrar data
df = df_raw.copy()
if len(date_range) == 2:
    df = df[(df['FECHA_EMISION'] >= pd.to_datetime(date_range[0])) & (df['FECHA_EMISION'] <= pd.to_datetime(date_range[1]))]
if selected_prods:
    df = df[df['DESCRIPCION_PRODUCTO'].isin(selected_prods)]

if df.empty:
    st.warning("⚠️ No se encontraron órdenes para la combinación de filtros seleccionada.")
    st.stop()

# Si se cambia el radio de agrupación a Semanal desde el sidebar, se reinicia cualquier drilldown
if periodo_seleccionado == "Semanal":
    st.session_state.drilldown_mes = None

# --- HEADER PRINCIPAL ---
st.markdown('<div class="dashboard-title">🥑 KCO Group | Intelligence & Pricing Dashboard</div>', unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-metadata">
        <div>
            <b>Desarrollado por:</b> Alfredo Huaracha Mendoza &nbsp;|&nbsp; <i>Industrial Engineering & Operations BI</i>
        </div>
        <div>
            🕒 <b>Última actualización:</b> {update_time}
        </div>
    </div>
""", unsafe_allow_html=True)

# BOTÓN DE PANTALLA COMPLETA
components.html("""
    <div style="display: flex; justify-content: flex-start; align-items: center; margin-bottom: 4px;">
        <button id="fs-btn" onclick="toggleFullScreen()" style="
            background-color: #1b4332; color: #ffffff; border: none; border-radius: 8px;
            padding: 7px 14px; font-size: 12.5px; font-weight: 600; cursor: pointer;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex; align-items: center; gap: 7px;
        ">
            <span id="fs-icon">⛶</span> <span id="fs-text">Activar Pantalla Completa</span>
        </button>
    </div>
    <script>
        function toggleFullScreen() {
            var doc = window.parent.document;
            var btnText = document.getElementById("fs-text");
            var btnIcon = document.getElementById("fs-icon");
            if (!doc.fullscreenElement) {
                doc.documentElement.requestFullscreen().catch(err => console.log(err));
                btnText.innerText = "Salir de Pantalla Completa";
                btnIcon.innerText = "🗗";
            } else {
                if (doc.exitFullscreen) {
                    doc.exitFullscreen();
                    btnText.innerText = "Activar Pantalla Completa";
                    btnIcon.innerText = "⛶";
                }
            }
        }
    </script>
""", height=38)

st.caption("Análisis estratégico de ventas, pricing y benchmark mayorista frente al mercado de Palta Fuerte.")

# --- KPIS GLOBALES CON GRID RESPONSIVE ---
total_kg = df['KILOS_SOLICITADOS'].sum()
valor_comercial_total = df['VALOR_COMERCIAL'].sum()
precio_ponderado_total = valor_comercial_total / total_kg if total_kg > 0 else 0
total_ocs = df['NRO_OC'].nunique()
kg_promedio_oc = total_kg / total_ocs if total_ocs > 0 else 0
total_jabas_est = df['JABAS_EST'].sum()

st.markdown(f"""
    <div class="kpi-grid">
        <div class="metric-card" style="border-left-color: {COLOR_PRIMARY};">
            <div class="metric-title">Volumen Solicitado</div>
            <div class="metric-value">{total_kg:,.0f} kg</div>
            <div class="metric-sub">{total_kg/1000:,.1f} Tn solicitadas</div>
        </div>
        <div class="metric-card" style="border-left-color: {COLOR_INFO};">
            <div class="metric-title">Facturación Total</div>
            <div class="metric-value">S/ {valor_comercial_total:,.0f}</div>
            <div class="metric-sub">Venta total bruta</div>
        </div>
        <div class="metric-card" style="border-left-color: {COLOR_ACCENT};">
            <div class="metric-title">Precio Pond. General</div>
            <div class="metric-value">S/ {precio_ponderado_total:.2f}</div>
            <div class="metric-sub">Por kg promedio</div>
        </div>
        <div class="metric-card" style="border-left-color: #8b5cf6;">
            <div class="metric-title">Órdenes Únicas</div>
            <div class="metric-value">{total_ocs:,}</div>
            <div class="metric-sub">{kg_promedio_oc:,.0f} kg / orden</div>
        </div>
        <div class="metric-card" style="border-left-color: #059669;">
            <div class="metric-title">Jabas Estimadas</div>
            <div class="metric-value">{total_jabas_est:,.0f}</div>
            <div class="metric-sub">Factor 18 kg/jaba</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- NAVEGACIÓN MOBILE-FIRST CON CONTROL SEGMENTADO TÁCTIL ---
vista_activa = st.radio(
    "Selecciona la vista a explorar:",
    options=["📊 Resumen & Evolución", "🎯 Benchmark & Previsión"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

# ==========================================================
# VISTA 1: RESUMEN EJECUTIVO & EVOLUCIÓN PERIÓDICA CON DRILL-DOWN
# ==========================================================
if vista_activa == "📊 Resumen & Evolución":
    
    es_vista_mensual = (periodo_seleccionado == "Mensual")
    mes_en_drilldown = st.session_state.drilldown_mes if es_vista_mensual else None

    # Miga de pan / Botón de retorno exclusivo cuando se está dentro de un mes
    if es_vista_mensual and mes_en_drilldown:
        col_bread1, col_bread2 = st.columns([3, 1])
        with col_bread1:
            st.markdown(f"""
                <div class="drilldown-bar">
                    <span>🔍 Vista Semanal activa del mes: <b>{mes_en_drilldown}</b></span>
                </div>
            """, unsafe_allow_html=True)
        with col_bread2:
            if st.button("⬅️ Volver a vista mensual", use_container_width=True, type="primary"):
                st.session_state.drilldown_mes = None
                st.rerun()

    # Selección de datos: mes específico o general
    if es_vista_mensual and mes_en_drilldown:
        df_target = df[df['MES_AÑO'] == mes_en_drilldown].copy()
        col_actual = 'SEMANA_AÑO'
        label_actual = f"Semana de {mes_en_drilldown}"
        titulo_grafico = f"Evolución Semanal de {mes_en_drilldown}: Volumen (Tn) vs Precio Ponderado (S/)"
    else:
        df_target = df.copy()
        col_actual = col_periodo
        label_actual = label_periodo
        hint = " — (Toca o haz clic en una barra para ver sus semanas)" if es_vista_mensual else ""
        titulo_grafico = f"Evolución {periodo_seleccionado}: Volumen (Tn) vs Precio Ponderado (S/){hint}"

    df_trend = df_target.groupby(col_actual).agg(
        KG_TOTALES=('KILOS_SOLICITADOS', 'sum'),
        VALOR_TOTAL=('VALOR_COMERCIAL', 'sum'),
        ORDENES=('NRO_OC', 'nunique')
    ).reset_index()
    df_trend['PRECIO_POND'] = df_trend['VALOR_TOTAL'] / df_trend['KG_TOTALES']
    df_trend['TN_TOTALES'] = df_trend['KG_TOTALES'] / 1000.0
    
    df_trend['VAR_KG_PCT'] = df_trend['KG_TOTALES'].pct_change() * 100
    df_trend['VAR_PRECIO_PCT'] = df_trend['PRECIO_POND'].pct_change() * 100
    df_trend['VAR_VALOR_PCT'] = df_trend['VALOR_TOTAL'].pct_change() * 100

    # 1. GRÁFICO A TODO EL ANCHO
    st.subheader(titulo_grafico)
    fig_dual = go.Figure()

    # Barras de Volumen
    fig_dual.add_trace(go.Bar(
        x=df_trend[col_actual],
        y=df_trend['TN_TOTALES'],
        name='Volumen (Tn)',
        marker=dict(
            color=COLOR_BARRA_CLARA,
            line=dict(color=COLOR_BARRA_BORDE, width=1.5)
        ),
        text=df_trend['TN_TOTALES'].apply(lambda x: f"<b>{x:,.1f} Tn</b>"),
        textposition='outside',
        outsidetextfont=dict(color='#0f172a', size=11, family="Arial"),
        hovertemplate=(
            f"<b>{label_actual}: %{{x}}</b><br>" +
            "📦 Volumen Solicitado: <b>%{y:.2f} Tn</b> (%{customdata[0]:,.0f} kg)<br>" +
            "📋 Órdenes de Compra: %{customdata[1]:,}<br>" +
            "💰 Facturación: S/ %{customdata[2]:,.2f}<br>" +
            ("👉 <b>Haz clic para abrir el desglose semanal</b>" if (es_vista_mensual and not mes_en_drilldown) else "") +
            "<extra></extra>"
        ),
        customdata=np.stack((df_trend['KG_TOTALES'], df_trend['ORDENES'], df_trend['VALOR_TOTAL']), axis=-1),
        yaxis='y'
    ))

    # Línea de Precio Ponderado
    fig_dual.add_trace(go.Scatter(
        x=df_trend[col_actual],
        y=df_trend['PRECIO_POND'],
        name='Precio Pond. (S/)',
        mode='lines+markers+text',
        text=df_trend['PRECIO_POND'].apply(lambda x: f"<b>S/{x:.2f}</b>"),
        textposition='top center',
        textfont=dict(color='#b45309', size=11, family="Arial"),
        marker=dict(size=9, color=COLOR_ACCENT),
        line=dict(width=3.2, color=COLOR_ACCENT),
        hovertemplate=(
            f"<b>{label_actual}: %{{x}}</b><br>" +
            "🏷️ <b>Precio Ponderado: S/ %{y:.2f} /kg</b><extra></extra>"
        ),
        yaxis='y2'
    ))

    anotaciones_estaciones = []
    lineas_estaciones = []

    # Delimitadores de Estaciones en vista mensual general
    if es_vista_mensual and not mes_en_drilldown:
        lista_meses = df_trend[col_actual].tolist()
        
        m_verano = [m for m in lista_meses if any(m.endswith(f"-{str(x).zfill(2)}") for x in [1, 2, 3])]
        m_otono = [m for m in lista_meses if any(m.endswith(f"-{str(x).zfill(2)}") for x in [4, 5, 6])]
        m_invierno = [m for m in lista_meses if any(m.endswith(f"-{str(x).zfill(2)}") for x in [7, 8, 9])]
        m_primavera = [m for m in lista_meses if any(m.endswith(f"-{str(x).zfill(2)}") for x in [10, 11, 12])]

        def agregar_delimitador_estacion(meses_est, nombre_est, color_txt):
            if not meses_est:
                return
            ini = meses_est[0]
            fin = meses_est[-1]
            
            lineas_estaciones.append(dict(
                type="line", xref="x", yref="paper",
                x0=ini, x1=fin, y0=-0.14, y1=-0.14,
                line=dict(color="#94a3b8", width=1.5, dash="dot")
            ))
            lineas_estaciones.append(dict(
                type="line", xref="x", yref="paper",
                x0=ini, x1=ini, y0=-0.11, y1=-0.17,
                line=dict(color="#94a3b8", width=1.5)
            ))
            lineas_estaciones.append(dict(
                type="line", xref="x", yref="paper",
                x0=fin, x1=fin, y0=-0.11, y1=-0.17,
                line=dict(color="#94a3b8", width=1.5)
            ))
            
            idx_ini = lista_meses.index(ini)
            idx_fin = lista_meses.index(fin)
            idx_med = int(round((idx_ini + idx_fin) / 2))
            med_mes = lista_meses[idx_med]
            
            anotaciones_estaciones.append(dict(
                x=med_mes, y=-0.23, xref='x', yref='paper',
                text=f"<b>{nombre_est}</b>", showarrow=False,
                font=dict(size=11, color=color_txt, family='Arial')
            ))

        agregar_delimitador_estacion(m_verano, "☀️ Verano", "#854d0e")
        agregar_delimitador_estacion(m_otono, "🍂 Otoño", "#9a3412")
        agregar_delimitador_estacion(m_invierno, "❄️ Invierno", "#0369a1")
        agregar_delimitador_estacion(m_primavera, "🌸 Primavera", "#15803d")

    fig_dual.update_layout(
        autosize=True,
        clickmode='event+select',
        xaxis=dict(title='', tickangle=-30 if (periodo_seleccionado == "Semanal" or mes_en_drilldown) else 0),
        yaxis=dict(title='Volumen Total (Tn)', showgrid=False),
        yaxis2=dict(title='Precio Pond. (S/ /kg)', overlaying='y', side='right', showgrid=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template='plotly_white',
        shapes=lineas_estaciones,
        annotations=anotaciones_estaciones,
        height=470,
        margin=dict(t=40, b=80 if (es_vista_mensual and not mes_en_drilldown) else 45, l=10, r=10)
    )

    # CAPTURA ROBUSTA DEL CLIC MEDIANTE KEY Y STREAMLIT SELECTION
    chart_key = "grafico_mensual_interactivo" if not mes_en_drilldown else "grafico_semanal_drilldown"
    
    chart_event = st.plotly_chart(
        fig_dual,
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key=chart_key,
        on_select="rerun",
        selection_mode="points"
    )

    # Si estamos en la vista mensual y el usuario hace clic en una barra
    if es_vista_mensual and not mes_en_drilldown and chart_event:
        selection_data = chart_event.get("selection", {})
        points = selection_data.get("points", [])
        if points:
            mes_seleccionado = points[0].get("x")
            if mes_seleccionado and mes_seleccionado in df['MES_AÑO'].unique():
                st.session_state.drilldown_mes = mes_seleccionado
                st.rerun()

    max_vol_row = df_trend.loc[df_trend['KG_TOTALES'].idxmax()]
    max_p_row = df_trend.loc[df_trend['PRECIO_POND'].idxmax()]
    st.markdown(f"""
    <div class="chart-insight">
        💡 <b>Diagnóstico del Periodo Analizado ({label_actual}):</b><br>
        • <b>Pico de Abastecimiento:</b> El mayor volumen se registró en <b>{max_vol_row[col_actual]}</b> con <b>{max_vol_row['TN_TOTALES']:.1f} Tn</b> ({max_vol_row['ORDENES']} OCs).<br>
        • <b>Máximo Precio Ponderado:</b> El precio promedio más alto fue de <b>S/ {max_p_row['PRECIO_POND']:.2f} /kg</b> en <b>{max_p_row[col_actual]}</b>.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 2. MIX DE PRODUCTO Y MATRIZ PERIÓDICA EN LA MISMA LÍNEA
    col_mix, col_matriz = st.columns([1, 1.35])
    
    with col_mix:
        st.subheader("Mix y Concentración por Producto")
        
        df_prod = df_target.groupby('DESCRIPCION_PRODUCTO').agg(
            VALOR=('VALOR_COMERCIAL', 'sum'),
            KG=('KILOS_SOLICITADOS', 'sum'),
            ORDENES=('NRO_OC', 'nunique')
        ).reset_index().sort_values(by='VALOR', ascending=False)
        
        valor_target_total = df_target['VALOR_COMERCIAL'].sum()
        df_prod['PRECIO_POND'] = df_prod['VALOR'] / df_prod['KG']
        df_prod['PART_VALOR'] = (df_prod['VALOR'] / valor_target_total) * 100 if valor_target_total > 0 else 0
        
        hover_texts = [
            f"🥑 <b>{row['DESCRIPCION_PRODUCTO']}</b><br><br>"
            f"💰 <b>Venta:</b> S/ {row['VALOR']:,.2f} ({row['PART_VALOR']:.1f}%)<br>"
            f"📦 <b>Volumen:</b> {row['KG']:,.0f} kg ({row['KG']/1000:,.1f} Tn)<br>"
            f"🏷️ <b>Precio Ponderado:</b> S/ {row['PRECIO_POND']:.2f} /kg<br>"
            f"📋 <b>Órdenes Únicas:</b> {row['ORDENES']:,} OCs"
            for _, row in df_prod.iterrows()
        ]
        
        pie_colors = [VARIEDAD_COLORS.get(prod, '#2d6a4f') for prod in df_prod['DESCRIPCION_PRODUCTO']]
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=df_prod['DESCRIPCION_PRODUCTO'],
            values=df_prod['VALOR'],
            hole=0.45,
            marker=dict(colors=pie_colors),
            textposition='inside',
            textinfo='percent+label',
            insidetextfont=dict(color='#ffffff', size=11, family="Arial"),
            hoverinfo='text',
            hovertext=hover_texts
        )])
        
        fig_pie.update_layout(
            autosize=True,
            template='plotly_white',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5),
            height=430,
            margin=dict(t=15, b=25, l=10, r=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CONFIG)
        
        top_prod = df_prod.iloc[0]
        st.markdown(f"""
        <div class="chart-insight">
            📌 <b>Concentración:</b> <b>{top_prod['DESCRIPCION_PRODUCTO']}</b> concentra el <b>{top_prod['PART_VALOR']:.1f}%</b> de la facturación del tramo (S/ {top_prod['VALOR']:,.0f}).
        </div>
        """, unsafe_allow_html=True)

    with col_matriz:
        st.subheader(f"📋 Matriz Periódica de Variación ({label_actual})")
        st.caption("Semáforo: 🟢 Aumento > +2% | 🟡 Estable [-2%, +2%] | 🔴 Descenso < -2%")
        
        df_var_display = df_trend[[col_actual, 'KG_TOTALES', 'VAR_KG_PCT', 'PRECIO_POND', 'VAR_PRECIO_PCT', 'VALOR_TOTAL', 'VAR_VALOR_PCT', 'ORDENES']].copy()
        df_var_display.columns = [label_actual, 'Kilos Solicitados', 'Var. Kg %', 'Precio Ponderado', 'Var. Precio %', 'Venta Bruta (S/)', 'Var. Venta %', 'Órdenes (OC)']
        
        st.dataframe(
            df_var_display.style.format({
                'Kilos Solicitados': '{:,.0f} kg',
                'Var. Kg %': '{:+.1f}%',
                'Precio Ponderado': 'S/ {:.2f}',
                'Var. Precio %': '{:+.1f}%',
                'Venta Bruta (S/)': 'S/ {:,.0f}',
                'Var. Venta %': '{:+.1f}%',
                'Órdenes (OC)': '{:,}'
            })
            .map(style_semaphore, subset=['Var. Kg %', 'Var. Precio %', 'Var. Venta %'])
            .highlight_null(color='#f1f5f9'),
            use_container_width=True, height=430, hide_index=True
        )

# ==========================================================
# VISTA 2: BENCHMARK MAYORISTA, PREVISIONES & PRICING
# ==========================================================
else:
    st.subheader("🎯 Comparativo Anual de Precios: Mayorista vs KCO Retail & Previsión")
    st.caption("Evolución mensual (Ene - Dic): Comparativa multianual de mercado y precio ponderado de venta a cliente con proyección estacional a Diciembre.")

    meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Dic']

    if not df_mercado_raw.empty:
        df_m = df_mercado_raw.copy()
        df_m['AÑO'] = df_m['Fecha'].dt.year
        df_m['MES'] = df_m['Fecha'].dt.month
        
        mkt_mensual = df_m.groupby(['AÑO', 'MES'])['Palta Fuerte'].mean().unstack(level=0)
        mkt_2025 = [mkt_mensual[2025].get(i, np.nan) if 2025 in mkt_mensual else np.nan for i in range(1, 13)]
        mkt_2026_real = [mkt_mensual[2026].get(i, np.nan) if 2026 in mkt_mensual else np.nan for i in range(1, 13)]
        
        df_kco = df_raw.copy()
        df_kco['MES'] = df_kco['FECHA_EMISION'].dt.month
        kco_mensual = df_kco.groupby('MES').agg(
            KILOS=('KILOS_SOLICITADOS', 'sum'),
            VALOR=('VALOR_COMERCIAL', 'sum')
        ).reset_index()
        kco_mensual['PRECIO_POND'] = kco_mensual['VALOR'] / kco_mensual['KILOS']
        kco_dict = dict(zip(kco_mensual['MES'], kco_mensual['PRECIO_POND']))
        kco_2026_real = [kco_dict.get(i, np.nan) for i in range(1, 13)]

        # Previsión Diciembre 2026
        factor_estacional_dic = (mkt_2025[11] - mkt_2025[10]) / mkt_2025[10] if pd.notna(mkt_2025[10]) and pd.notna(mkt_2025[11]) else -0.20
        mkt_nov_val = mkt_2026_real[10] if pd.notna(mkt_2026_real[10]) else 8.59
        mkt_dic_pred = round(mkt_nov_val * (1 + factor_estacional_dic), 2)
        
        kco_nov_val = kco_2026_real[10] if pd.notna(kco_2026_real[10]) else 11.00
        spread_historico = np.nanmean(np.array(kco_2026_real[:11]) - np.array(mkt_2026_real[:11]))
        if pd.isna(spread_historico):
            spread_historico = 2.74
            
        kco_dic_pred = round(mkt_dic_pred + (spread_historico * 0.95), 2)

        # Etiquetas intercaladas
        text_mkt_intercalado = []
        for idx, val in enumerate(mkt_2026_real[:11]):
            mes_num = idx + 1
            if pd.isna(val):
                text_mkt_intercalado.append("")
            elif mes_num % 2 != 0 or mes_num == 11:
                text_mkt_intercalado.append(f"<b>S/{val:.2f}</b>")
            else:
                text_mkt_intercalado.append("")

        text_kco_intercalado = []
        for idx, val in enumerate(kco_2026_real[:11]):
            mes_num = idx + 1
            if pd.isna(val):
                text_kco_intercalado.append("")
            elif mes_num % 2 == 0 or mes_num == 11:
                text_kco_intercalado.append(f"<b>S/{val:.2f}</b>")
            else:
                text_kco_intercalado.append("")

        fig_anual = go.Figure()

        # A. Mercado Mayorista 2025
        fig_anual.add_trace(go.Scatter(
            x=meses_nombres,
            y=mkt_2025,
            name='Mayorista 2025 (Referencia)',
            mode='lines+markers',
            line=dict(color='#cbd5e1', width=2, dash='dot'),
            marker=dict(size=5, color='#cbd5e1'),
            hovertemplate="<b>%{x} (Mayorista 2025)</b><br>Precio: S/ %{y:.2f} /kg<extra></extra>"
        ))

        # B. Mercado Mayorista 2026
        fig_anual.add_trace(go.Scatter(
            x=meses_nombres[:11],
            y=mkt_2026_real[:11],
            name='Mayorista 2026 (Costo Base)',
            mode='lines+markers+text',
            text=text_mkt_intercalado,
            textposition='bottom center',
            textfont=dict(color='#475569', size=11, family='Arial'),
            line=dict(color='#475569', width=2.8),
            marker=dict(size=7, color='#475569'),
            hovertemplate="<b>%{x} (Mayorista 2026)</b><br>Costo Mercado: S/ %{y:.2f} /kg<extra></extra>"
        ))

        # C. Proyección Mercado Dic (Punteada)
        fig_anual.add_trace(go.Scatter(
            x=['Nov', 'Dic'],
            y=[mkt_nov_val, mkt_dic_pred],
            name='Mayorista 2026 (Previsión Dic)',
            mode='lines+markers+text',
            text=["", f"<b>S/{mkt_dic_pred:.2f}*</b>"],
            textposition='bottom center',
            textfont=dict(color='#64748b', size=11, family='Arial'),
            line=dict(color='#64748b', width=2.5, dash='dash'),
            marker=dict(size=8, symbol='diamond', color='#64748b'),
            hovertemplate="<b>%{x} (Previsión Mercado)</b><br>Costo Estimado: S/ %{y:.2f} /kg<extra></extra>"
        ))

        # D. KCO Retail Ponderado
        fig_anual.add_trace(go.Scatter(
            x=meses_nombres[:11],
            y=kco_2026_real[:11],
            name='KCO Venta Cliente 2026 (Ponderado)',
            mode='lines+markers+text',
            text=text_kco_intercalado,
            textposition='top center',
            textfont=dict(color='#1b4332', size=11, family='Arial'),
            line=dict(color='#1b4332', width=3.5),
            marker=dict(size=9, color='#1b4332'),
            hovertemplate="<b>%{x} (KCO Venta)</b><br>Precio Ponderado: S/ %{y:.2f} /kg<extra></extra>"
        ))

        # E. Proyección KCO Dic (Punteada)
        fig_anual.add_trace(go.Scatter(
            x=['Nov', 'Dic'],
            y=[kco_nov_val, kco_dic_pred],
            name='KCO Venta (Previsión Dic)',
            mode='lines+markers+text',
            text=["", f"<b>S/{kco_dic_pred:.2f}*</b>"],
            textposition='top center',
            textfont=dict(color='#d97706', size=12, family='Arial'),
            line=dict(color='#d97706', width=3.2, dash='dash'),
            marker=dict(size=10, symbol='star', color='#d97706'),
            hovertemplate="<b>%{x} (Previsión KCO)</b><br>Cotización Sugerida: S/ %{y:.2f} /kg<extra></extra>"
        ))

        fig_anual.update_layout(
            autosize=True,
            template='plotly_white',
            height=440,
            xaxis=dict(
                title='',
                categoryorder='array',
                categoryarray=meses_nombres,
                tickfont=dict(size=12, color='#1e293b')
            ),
            yaxis=dict(
                title='Precio (S/ por Kg)',
                gridcolor='#f1f5f9',
                zeroline=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="center",
                x=0.5,
                title_text=""
            ),
            margin=dict(t=45, b=25, l=10, r=10)
        )
        st.plotly_chart(fig_anual, use_container_width=True, config=PLOTLY_CONFIG)

        c_prev1, c_prev2, c_prev3 = st.columns(3)
        with c_prev1:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #64748b;">
                    <div class="metric-title">Costo Mayorista (Nov Real / Dic Proy)</div>
                    <div class="metric-value">S/ {mkt_nov_val:.2f} ➔ S/ {mkt_dic_pred:.2f}</div>
                    <div class="metric-sub">Ajuste estacional fin de año (-20.1%)</div>
                </div>
            """, unsafe_allow_html=True)
        with c_prev2:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #1b4332;">
                    <div class="metric-title">KCO Venta Cliente (Nov Real)</div>
                    <div class="metric-value">S/ {kco_nov_val:.2f} /kg</div>
                    <div class="metric-sub">Precio ponderado registrado a la fecha</div>
                </div>
            """, unsafe_allow_html=True)
        with c_prev3:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #d97706;">
                    <div class="metric-title">KCO Cotización Sugerida (Dic Proy)</div>
                    <div class="metric-value">S/ {kco_dic_pred:.2f} /kg</div>
                    <div class="metric-sub">Banda objetivo: S/ {kco_dic_pred - 0.30:.2f} a S/ {kco_dic_pred + 0.30:.2f}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="chart-insight">
            💡 <b>Estrategia de Pricing para Diciembre:</b> 
            En <b>Diciembre</b>, el incremento de cosecha temprana en valles costeros empuja a la baja el costo mayorista (como ocurrió en 2025 al pasar de S/ 7.41 a S/ 5.92). 
            La <b>línea punteada dorada (*)</b> proyecta que cotizar a tu cliente en torno a <b>S/ {kco_dic_pred:.2f} /kg</b> asegura tu margen habitual de intermediación (~S/ {spread_historico:.2f}/kg) manteniendo la competitividad frente a otros proveedores de retail.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Sube el archivo 'reporte_fuerte.xls' al repositorio para habilitar la previsión contra el mercado mayorista.")

    st.markdown("---")

    # --- AUDITORÍA DE VARIACIONES DE PRECIO Y BANDA DE NEGOCIACIÓN ---
    st.subheader("🔍 Auditoría de Variaciones de Precios por Producto")
    st.caption(f"Evolución y variaciones porcentuales agrupadas por **{periodo_seleccionado.lower()}** para cada variedad.")
    
    df_prod_trend = df.groupby(['DESCRIPCION_PRODUCTO', col_periodo]).agg(
        KG=('KILOS_SOLICITADOS', 'sum'),
        VALOR=('VALOR_COMERCIAL', 'sum')
    ).reset_index()
    df_prod_trend['PRECIO_POND'] = df_prod_trend['VALOR'] / df_prod_trend['KG']
    df_prod_trend = df_prod_trend.sort_values(by=['DESCRIPCION_PRODUCTO', col_periodo])
    
    df_prod_trend['PRECIO_PREV'] = df_prod_trend.groupby('DESCRIPCION_PRODUCTO')['PRECIO_POND'].shift(1)
    df_prod_trend['VAR_PRECIO_PCT'] = ((df_prod_trend['PRECIO_POND'] - df_prod_trend['PRECIO_PREV']) / df_prod_trend['PRECIO_PREV']) * 100
    df_prod_trend['DIF_SOLES'] = df_prod_trend['PRECIO_POND'] - df_prod_trend['PRECIO_PREV']

    df_changes = df_prod_trend[df_prod_trend['VAR_PRECIO_PCT'].notna() & (df_prod_trend['VAR_PRECIO_PCT'] != 0)].copy()

    col_c1, col_c2 = st.columns([1.5, 1.5])
    
    with col_c1:
        st.markdown(f"##### Variaciones Porcentuales de Precio ({periodo_seleccionado})")
        if not df_changes.empty:
            fig_var = px.bar(
                df_changes.tail(20),
                x=col_periodo,
                y='VAR_PRECIO_PCT',
                color='VAR_PRECIO_PCT',
                text=df_changes.tail(20)['VAR_PRECIO_PCT'].apply(lambda x: f"<b>{x:+.1f}%</b>"),
                color_continuous_scale='RdYlGn',
                custom_data=['DESCRIPCION_PRODUCTO', 'PRECIO_PREV', 'PRECIO_POND', 'KG']
            )
            fig_var.update_traces(
                textposition='outside',
                outsidetextfont=dict(color='#0f172a', size=11, family="Arial"),
                hovertemplate=(
                    f"<b>{label_periodo}: %{{x}}</b><br>" +
                    "🥑 <b>Producto: %{customdata[0]}</b><br>" +
                    "🏷️ Precio Anterior: S/ %{customdata[1]:.2f} /kg<br>" +
                    "🏷️ Precio Nuevo: S/ %{customdata[2]:.2f} /kg<br>" +
                    "📊 Variación: <b>%{y:+.2f}%</b><br>" +
                    "📦 Volumen: %{customdata[3]:,.0f} kg<extra></extra>"
                )
            )
            fig_var.update_layout(
                autosize=True,
                template='plotly_white',
                xaxis=dict(title=label_periodo, tickangle=-45 if periodo_seleccionado == "Semanal" else 0),
                yaxis=dict(title='Variación Porcentual (%)'),
                height=400,
                margin=dict(t=20, b=25, l=10, r=10)
            )
            st.plotly_chart(fig_var, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("Sin variaciones registradas en el periodo.")

    with col_c2:
        st.markdown("##### Precios Ponderados por Variedad")
        fig_line_prod = px.line(
            df_prod_trend,
            x=col_periodo,
            y='PRECIO_POND',
            color='DESCRIPCION_PRODUCTO',
            markers=True,
            color_discrete_map=VARIEDAD_COLORS
        )
        fig_line_prod.update_traces(
            line=dict(width=2.8),
            marker=dict(size=7),
            hovertemplate=(
                f"<b>{label_periodo}: %{{x}}</b><br>" +
                "🥑 %{fullData.name}<br>" +
                "🏷️ Precio Ponderado: <b>S/ %{y:.2f} /kg</b><extra></extra>"
            )
        )
        fig_line_prod.update_layout(
            autosize=True,
            template='plotly_white',
            xaxis=dict(title=label_periodo, tickangle=-45 if periodo_seleccionado == "Semanal" else 0),
            yaxis=dict(title='Precio S/ por Kg'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.03,
                xanchor="center",
                x=0.5,
                title_text=""
            ),
            height=400,
            margin=dict(t=45, b=25, l=10, r=10)
        )
        st.plotly_chart(fig_line_prod, use_container_width=True, config=PLOTLY_CONFIG)

    if not df_changes.empty:
        with st.expander("Ver tabla completa de historial de cambios de precio"):
            tbl_c = df_changes[[col_periodo, 'DESCRIPCION_PRODUCTO', 'PRECIO_PREV', 'PRECIO_POND', 'DIF_SOLES', 'VAR_PRECIO_PCT', 'KG']].copy()
            tbl_c.columns = [label_periodo, 'Producto', 'Precio Anterior', 'Precio Actual', 'Diferencia S/', 'Variación %', 'Kilos del Periodo']
            st.dataframe(
                tbl_c.sort_values(by=label_periodo, ascending=False).style.format({
                    'Precio Anterior': 'S/ {:.2f}',
                    'Precio Actual': 'S/ {:.2f}',
                    'Diferencia S/': 'S/ {:+.2f}',
                    'Variación %': '{:+.2f}%',
                    'Kilos del Periodo': '{:,.0f} kg'
                })
                .map(style_semaphore, subset=['Variación %', 'Diferencia S/']),
                use_container_width=True, hide_index=True
            )

    st.markdown("---")

    # --- BANDA DE NEGOCIACIÓN DE PRECIOS A ANCHO COMPLETO ---
    st.subheader("🎯 Banda de Negociación de Precios (Mín / Pond / Máx)")
    st.caption("Rango efectivo de precios pactados por variedad en el periodo analizado.")
    
    df_banda = df.groupby('DESCRIPCION_PRODUCTO').agg(
        PRECIO_MIN=('PRECIO_KG', 'min'),
        PRECIO_MAX=('PRECIO_KG', 'max'),
        KILOS=('KILOS_SOLICITADOS', 'sum'),
        VALOR=('VALOR_COMERCIAL', 'sum')
    ).reset_index()
    df_banda['PRECIO_POND'] = df_banda['VALOR'] / df_banda['KILOS']
    
    fig_banda = go.Figure()
    
    fig_banda.add_trace(go.Bar(
        name='Banda Min-Max',
        x=df_banda['DESCRIPCION_PRODUCTO'],
        y=df_banda['PRECIO_MAX'] - df_banda['PRECIO_MIN'],
        base=df_banda['PRECIO_MIN'],
        marker_color='rgba(45, 106, 79, 0.25)',
        hovertemplate=(
            "<b>%{x}</b><br>" +
            "Piso: S/ %{base:.2f}<br>" +
            "Techo: S/ %{customdata:.2f}<extra></extra>"
        ),
        customdata=df_banda['PRECIO_MAX']
    ))
    
    fig_banda.add_trace(go.Scatter(
        name='Precio Ponderado Real',
        x=df_banda['DESCRIPCION_PRODUCTO'],
        y=df_banda['PRECIO_POND'],
        mode='markers+text',
        text=df_banda['PRECIO_POND'].apply(lambda x: f"<b>S/{x:.2f}</b>"),
        textposition='top center',
        textfont=dict(color='#0f172a', size=11, family="Arial"),
        marker=dict(size=12, color=COLOR_ACCENT, symbol='diamond'),
        hovertemplate="<b>%{x}</b><br>🏷️ Precio Ponderado: <b>S/ %{y:.2f} /kg</b><extra></extra>"
    ))
    
    fig_banda.update_layout(
        autosize=True,
        template='plotly_white',
        height=380,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        yaxis_title="Precio (S/ por Kg)",
        xaxis_title="Variedad",
        margin=dict(t=35, b=25, l=10, r=10)
    )
    st.plotly_chart(fig_banda, use_container_width=True, config=PLOTLY_CONFIG)

    # Detalle Operativo Final
    st.markdown("---")
    st.subheader("📋 Detalle de Órdenes & Estimaciones Logísticas")
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

# --- FOOTER INSTITUCIONAL ---
st.markdown(f"""
    <div class="footer-credits">
        🥑 <b>KCO Group</b> — Plataforma de Inteligencia Comercial & Pricing &nbsp;|&nbsp; 
        <b>Desarrollado por:</b> Alfredo Huaracha Mendoza &nbsp;|&nbsp; 
        <b>Última actualización:</b> {update_time}
    </div>
""", unsafe_allow_html=True)
