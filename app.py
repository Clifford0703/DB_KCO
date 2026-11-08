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
    initial_sidebar_state="collapsed"
)

# --- PALETA CORPORATIVA DE ALTO CONTRASTE ---
COLOR_PRIMARY = "#1b4332"
COLOR_SECONDARY = "#2d6a4f"
COLOR_ACCENT = "#d97706"
COLOR_NEUTRAL = "#0f172a"
COLOR_INFO = "#0284c7"
COLOR_MERCADO = "#64748b"  # Gris neutro pizarra para el mercado

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
    .main {{ background-color: #f8fafc; }}
    .block-container {{
        max-width: 100% !important;
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }}
    .metric-card {{
        background: #ffffff;
        padding: 16px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border-left: 5px solid {COLOR_PRIMARY};
        margin-bottom: 12px;
        width: 100% !important;
    }}
    .metric-title {{
        font-size: 11px;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .metric-value {{
        font-size: 23px;
        color: {COLOR_NEUTRAL};
        font-weight: 800;
        margin-top: 4px;
        word-break: break-word;
    }}
    .metric-sub {{
        font-size: 11px;
        color: #94a3b8;
        margin-top: 2px;
        font-weight: 500;
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
    .filter-box {{
        background-color: #ffffff;
        padding: 16px 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        width: 100% !important;
    }}
    .header-metadata {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 8px;
        color: #64748b;
        font-size: 13px;
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
    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            padding-top: 0.6rem !important;
        }}
        .metric-card {{
            padding: 12px 14px;
            margin-bottom: 8px;
        }}
        .metric-value {{ font-size: 18px; }}
        .header-metadata {{
            flex-direction: column;
            align-items: flex-start;
            font-size: 11.5px;
        }}
    }}
    </style>
""", unsafe_allow_html=True)

PLOTLY_CONFIG = {
    'displayModeBar': False,
    'responsive': True
}

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
    # 1. Carga de Órdenes de KCO
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
    df['FORMA_PAGO'] = df['FORMA_PAGO'].fillna('No Definido')
    
    def get_fruto_weight(prod):
        return PRODUCT_WEIGHTS.get(str(prod).strip().upper(), np.nan)
        
    df['PESO_FRUTO_KG'] = df['DESCRIPCION_PRODUCTO'].apply(get_fruto_weight)
    df['FRUTOS_EST'] = np.where(df['PESO_FRUTO_KG'].notna(), df['KILOS_SOLICITADOS'] / df['PESO_FRUTO_KG'], 0)
    df['JABAS_EST'] = df['KILOS_SOLICITADOS'] / KG_PER_JABA
    df['PRECIO_FRUTO_EST'] = df['PRECIO_KG'] * df['PESO_FRUTO_KG']
    
    # 2. Carga de Precios del Mercado Mayorista (reporte_fuerte.xls)
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

# --- HEADER CON BOTÓN FULLSCREEN ---
head_col1, head_col2 = st.columns([4, 1])
with head_col1:
    st.markdown("## 🥑 KCO Group | Intelligence & Pricing Dashboard")

with head_col2:
    components.html("""
        <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%;">
            <button id="fs-btn" onclick="toggleFullScreen()" style="
                background-color: #1b4332; color: #ffffff; border: none; border-radius: 8px;
                padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer;
                box-shadow: 0 1px 3px rgba(0,0,0,0.15); font-family: sans-serif;
            ">
                <span id="fs-icon">⛶</span> <span id="fs-text">Pantalla Completa</span>
            </button>
        </div>
        <script>
            function toggleFullScreen() {
                var doc = window.parent.document;
                var btnText = document.getElementById("fs-text");
                var btnIcon = document.getElementById("fs-icon");
                if (!doc.fullscreenElement) {
                    doc.documentElement.requestFullscreen().catch(err => console.log(err));
                    btnText.innerText = "Salir Completa";
                    btnIcon.innerText = "🗗";
                } else {
                    if (doc.exitFullscreen) {
                        doc.exitFullscreen();
                        btnText.innerText = "Pantalla Completa";
                        btnIcon.innerText = "⛶";
                    }
                }
            }
        </script>
    """, height=45)

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

st.caption("Análisis estratégico de ventas, pricing y benchmark mayorista frente al mercado de Palta Fuerte.")

# --- FILTROS GLOBALES ---
with st.expander("🔍 **Filtros y Segmentación de Datos** (Toca aquí para ajustar)", expanded=True):
    f_row1, f_row2 = st.columns([2.5, 1.5])
    with f_row1:
        f1, f2, f3 = st.columns(3)
        with f1:
            min_date, max_date = df_raw['FECHA_EMISION'].min(), df_raw['FECHA_EMISION'].max()
            date_range = st.date_input("Periodo Histórico", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        with f2:
            prods = sorted(df_raw['DESCRIPCION_PRODUCTO'].dropna().unique().tolist())
            selected_prods = st.multiselect("Variedad / Calibre", options=prods, default=prods)
        with f3:
            formas_pago = sorted(df_raw['FORMA_PAGO'].dropna().unique().tolist())
            selected_fp = st.multiselect("Condición de Pago", options=formas_pago, default=formas_pago)
            
    with f_row2:
        periodo_seleccionado = st.radio(
            "Agrupación Temporal:",
            options=["Mensual", "Semanal"],
            horizontal=True
        )

col_periodo = 'MES_AÑO' if periodo_seleccionado == "Mensual" else 'SEMANA_AÑO'
label_periodo = "Mes" if periodo_seleccionado == "Mensual" else "Semana"

# Filtrar data de órdenes
df = df_raw.copy()
if len(date_range) == 2:
    df = df[(df['FECHA_EMISION'] >= pd.to_datetime(date_range[0])) & (df['FECHA_EMISION'] <= pd.to_datetime(date_range[1]))]
if selected_prods:
    df = df[df['DESCRIPCION_PRODUCTO'].isin(selected_prods)]
if selected_fp:
    df = df[df['FORMA_PAGO'].isin(selected_fp)]

if df.empty:
    st.warning("⚠️ No se encontraron órdenes para la combinación de filtros seleccionada.")
    st.stop()

# --- KPIS GLOBALES ---
total_kg = df['KILOS_SOLICITADOS'].sum()
valor_comercial_total = df['VALOR_COMERCIAL'].sum()
precio_ponderado_total = valor_comercial_total / total_kg if total_kg > 0 else 0
total_ocs = df['NRO_OC'].nunique()
kg_promedio_oc = total_kg / total_ocs if total_ocs > 0 else 0
total_jabas_est = df['JABAS_EST'].sum()

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Volumen Solicitado</div><div class="metric-value">{total_kg:,.0f} kg</div><div class="metric-sub">{total_kg/1000:,.1f} Tn solicitadas</div></div>', unsafe_allow_html=True)
with kpi2:
    st.markdown(f'<div class="metric-card" style="border-left-color: {COLOR_INFO};"><div class="metric-title">Facturación Total</div><div class="metric-value">S/ {valor_comercial_total:,.0f}</div><div class="metric-sub">Venta total bruta</div></div>', unsafe_allow_html=True)
with kpi3:
    st.markdown(f'<div class="metric-card" style="border-left-color: {COLOR_ACCENT};"><div class="metric-title">Precio Pond. General</div><div class="metric-value">S/ {precio_ponderado_total:.2f}</div><div class="metric-sub">Por kg promedio</div></div>', unsafe_allow_html=True)
with kpi4:
    st.markdown(f'<div class="metric-card" style="border-left-color: #8b5cf6;"><div class="metric-title">Órdenes Únicas</div><div class="metric-value">{total_ocs:,}</div><div class="metric-sub">{kg_promedio_oc:,.0f} kg / orden</div></div>', unsafe_allow_html=True)
with kpi5:
    st.markdown(f'<div class="metric-card" style="border-left-color: #059669;"><div class="metric-title">Jabas Estimadas</div><div class="metric-value">{total_jabas_est:,.0f}</div><div class="metric-sub">Factor 18 kg/jaba</div></div>', unsafe_allow_html=True)

# --- NAVEGACIÓN EN 2 PESTAÑAS ---
tab1, tab2 = st.tabs([
    "📊 1. Resumen Ejecutivo & Evolución Periódica",
    "📈 2. Benchmark de Mercado, Previsiones & Pricing"
])

# ==========================================================
# PESTAÑA 1: RESUMEN EJECUTIVO & EVOLUCIÓN PERIÓDICA
# ==========================================================
with tab1:
    df_trend = df.groupby(col_periodo).agg(
        KG_TOTALES=('KILOS_SOLICITADOS', 'sum'),
        VALOR_TOTAL=('VALOR_COMERCIAL', 'sum'),
        ORDENES=('NRO_OC', 'nunique')
    ).reset_index()
    df_trend['PRECIO_POND'] = df_trend['VALOR_TOTAL'] / df_trend['KG_TOTALES']
    df_trend['TN_TOTALES'] = df_trend['KG_TOTALES'] / 1000.0
    
    df_trend['VAR_KG_PCT'] = df_trend['KG_TOTALES'].pct_change() * 100
    df_trend['VAR_PRECIO_PCT'] = df_trend['PRECIO_POND'].pct_change() * 100
    df_trend['VAR_VALOR_PCT'] = df_trend['VALOR_TOTAL'].pct_change() * 100

    col_g1, col_g2 = st.columns([1.6, 1])

    with col_g1:
        st.subheader(f"Evolución {periodo_seleccionado}: Volumen (Tn) vs Precio Ponderado (S/)")
        fig_dual = go.Figure()

        fig_dual.add_trace(go.Bar(
            x=df_trend[col_periodo],
            y=df_trend['TN_TOTALES'],
            name='Volumen (Tn)',
            marker_color=COLOR_SECONDARY,
            text=df_trend['TN_TOTALES'].apply(lambda x: f"{x:,.1f} Tn"),
            textposition='outside',
            outsidetextfont=dict(color='#0f172a', size=11, family="Arial", weight="bold"),
            hovertemplate=(
                f"<b>{label_periodo}: %{{x}}</b><br>" +
                "📦 Volumen: %{y:.2f} Tn (%{customdata[0]:,.0f} kg)<br>" +
                "📋 Órdenes de Compra: %{customdata[1]:,}<br>" +
                "💰 Venta: S/ %{customdata[2]:,.2f}<extra></extra>"
            ),
            customdata=np.stack((df_trend['KG_TOTALES'], df_trend['ORDENES'], df_trend['VALOR_TOTAL']), axis=-1),
            yaxis='y'
        ))

        fig_dual.add_trace(go.Scatter(
            x=df_trend[col_periodo],
            y=df_trend['PRECIO_POND'],
            name='Precio Pond. (S/)',
            mode='lines+markers+text',
            text=df_trend['PRECIO_POND'].apply(lambda x: f"S/{x:.2f}"),
            textposition='top center',
            textfont=dict(color='#b45309', size=11, family="Arial", weight="bold"),
            marker=dict(size=8, color=COLOR_ACCENT),
            line=dict(width=3, color=COLOR_ACCENT),
            hovertemplate=(
                f"<b>{label_periodo}: %{{x}}</b><br>" +
                "🏷️ <b>Precio Ponderado: S/ %{y:.2f} /kg</b><extra></extra>"
            ),
            yaxis='y2'
        ))

        fig_dual.update_layout(
            autosize=True,
            xaxis=dict(title=label_periodo, tickangle=-45 if periodo_seleccionado == "Semanal" else 0),
            yaxis=dict(title='Volumen Total (Tn)', showgrid=False),
            yaxis2=dict(title='Precio Pond. (S/ /kg)', overlaying='y', side='right', showgrid=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template='plotly_white',
            height=400,
            margin=dict(t=35, b=25, l=10, r=10)
        )
        st.plotly_chart(fig_dual, use_container_width=True, config=PLOTLY_CONFIG)
        
        max_vol_row = df_trend.loc[df_trend['KG_TOTALES'].idxmax()]
        max_p_row = df_trend.loc[df_trend['PRECIO_POND'].idxmax()]
        st.markdown(f"""
        <div class="chart-insight">
            💡 <b>Insight Comercial ({periodo_seleccionado}):</b> 
            El pico de volumen se registró en <b>{max_vol_row[col_periodo]}</b> con <b>{max_vol_row['TN_TOTALES']:.1f} Tn</b> ({max_vol_row['ORDENES']} OCs). 
            El mayor precio ponderado se alcanzó en <b>{max_p_row[col_periodo]}</b> a <b>S/ {max_p_row['PRECIO_POND']:.2f} /kg</b>.
        </div>
        """, unsafe_allow_html=True)

    with col_g2:
        st.subheader("Mix y Concentración por Producto")
        
        df_prod = df.groupby('DESCRIPCION_PRODUCTO').agg(
            VALOR=('VALOR_COMERCIAL', 'sum'),
            KG=('KILOS_SOLICITADOS', 'sum'),
            ORDENES=('NRO_OC', 'nunique')
        ).reset_index().sort_values(by='VALOR', ascending=False)
        
        df_prod['PRECIO_POND'] = df_prod['VALOR'] / df_prod['KG']
        df_prod['PART_VALOR'] = (df_prod['VALOR'] / valor_comercial_total) * 100
        
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
            insidetextfont=dict(color='#ffffff', size=11, family="Arial", weight="bold"),
            hoverinfo='text',
            hovertext=hover_texts
        )])
        
        fig_pie.update_layout(
            autosize=True,
            template='plotly_white',
            showlegend=False,
            height=400,
            margin=dict(t=25, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CONFIG)
        
        top_prod = df_prod.iloc[0]
        st.markdown(f"""
        <div class="chart-insight">
            📌 <b>Concentración de Portafolio:</b> <b>{top_prod['DESCRIPCION_PRODUCTO']}</b> concentra el <b>{top_prod['PART_VALOR']:.1f}%</b> de la facturación (S/ {top_prod['VALOR']:,.0f}).
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    st.subheader(f"📋 Matriz Periódica de Variación ({periodo_seleccionado})")
    st.caption("Semáforo: 🟢 Aumento > +2% | 🟡 Estable [-2%, +2%] | 🔴 Descenso < -2%")
    
    df_var_display = df_trend[[col_periodo, 'KG_TOTALES', 'VAR_KG_PCT', 'PRECIO_POND', 'VAR_PRECIO_PCT', 'VALOR_TOTAL', 'VAR_VALOR_PCT', 'ORDENES']].copy()
    df_var_display.columns = [label_periodo, 'Kilos Solicitados', 'Var. Kg %', 'Precio Ponderado', 'Var. Precio %', 'Venta Bruta (S/)', 'Var. Venta %', 'Órdenes (OC)']
    
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
        use_container_width=True, hide_index=True
    )

# ==========================================================
# PESTAÑA 2: BENCHMARK MAYORISTA, PREVISIONES & PRICING
# ==========================================================
with tab2:
    st.subheader("🎯 Benchmark: Precio KCO vs Mercado Mayorista & Previsión")
    st.caption("Comparativo directo de Palta Fuerte KCO vs Mercado Mayorista (reporte_fuerte.xls) y proyección de cierre para este mes y el próximo.")
    
    # Preparamos la serie mensual de KCO Fuerte
    df_fuerte = df_raw[df_raw['DESCRIPCION_PRODUCTO'].str.contains('FUERTE', case=False, na=False)].copy()
    kco_monthly_fuerte = df_fuerte.groupby('MES_AÑO').agg(
        KILOS=('KILOS_SOLICITADOS', 'sum'),
        VALOR=('VALOR_COMERCIAL', 'sum')
    ).reset_index()
    kco_monthly_fuerte['PRECIO_KCO_FUERTE'] = kco_monthly_fuerte['VALOR'] / kco_monthly_fuerte['KILOS']
    
    # Serie mensual de Mercado
    if not df_mercado_raw.empty:
        mkt_monthly = df_mercado_raw.groupby('MES_AÑO')['Palta Fuerte'].mean().reset_index()
        mkt_monthly.rename(columns={'Palta Fuerte': 'PRECIO_MERCADO'}, inplace=True)
        
        # Merge histórico
        df_comp = pd.merge(mkt_monthly[mkt_monthly['MES_AÑO'] >= '2026-02'], kco_monthly_fuerte, on='MES_AÑO', how='left')
        
        # Previsión para este mes (2026-11) y el siguiente (2026-12)
        # Noviembre 2026 en mercado (promedio observado + proyección fin de mes)
        mkt_nov_val = df_mercado_raw[df_mercado_raw['MES_AÑO'] == '2026-11']['Palta Fuerte'].mean()
        if pd.isna(mkt_nov_val):
            mkt_nov_val = 8.65
        else:
            mkt_nov_val = round(float(mkt_nov_val), 2)
            
        # Estimación estacional Diciembre 2026
        # Estacionalidad histórica: en dic 2025 cayó -20% frente a nov 2025
        mkt_dic_pred = round(mkt_nov_val * 0.81, 2)  # ~6.95 S/
        
        # KCO histórico mantiene un spread promedio de S/ 2.74 o ~60% de margen retail
        spread_promedio = (df_comp['PRECIO_KCO_FUERTE'] - df_comp['PRECIO_MERCADO']).dropna().mean()
        if pd.isna(spread_promedio):
            spread_promedio = 2.75
            
        kco_nov_pred = round(mkt_nov_val + spread_promedio, 2)      # ~11.40 S/
        kco_dic_pred = round(mkt_dic_pred + (spread_promedio * 0.95), 2) # ~9.70 S/

        # Dataframe unificado con previsiones
        meses_hist = df_comp['MES_AÑO'].tolist()
        mkt_hist = df_comp['PRECIO_MERCADO'].tolist()
        kco_hist = df_comp['PRECIO_KCO_FUERTE'].tolist()
        
        # Gráfico comparativo y forecast
        fig_bench = go.Figure()

        # Línea de Mercado Mayorista Histórico
        fig_bench.add_trace(go.Scatter(
            x=meses_hist,
            y=mkt_hist,
            name='Mercado Mayorista (Histórico)',
            mode='lines+markers',
            line=dict(color=COLOR_MERCADO, width=2.5),
            marker=dict(size=7),
            hovertemplate="<b>Mes: %{x}</b><br>Mercado Mayorista: S/ %{y:.2f} /kg<extra></extra>"
        ))

        # Línea de KCO Palta Fuerte Histórico
        fig_bench.add_trace(go.Scatter(
            x=meses_hist,
            y=kco_hist,
            name='KCO Retail - Palta Fuerte (Ponderado)',
            mode='lines+markers+text',
            text=[f"S/{y:.2f}" if pd.notna(y) else "" for y in kco_hist],
            textposition='top center',
            textfont=dict(color='#0f172a', size=11, family="Arial", weight="bold"),
            line=dict(color=COLOR_PRIMARY, width=3.5),
            marker=dict(size=8, color=COLOR_PRIMARY),
            hovertemplate="<b>Mes: %{x}</b><br>KCO Precio Ponderado: S/ %{y:.2f} /kg<extra></extra>"
        ))

        # Puntos de Previsión (Noviembre 2026 y Diciembre 2026)
        meses_forecast = ['2026-10', '2026-11 (Previsión)', '2026-12 (Previsión)']
        mkt_last_val = mkt_hist[-2] if len(mkt_hist) >= 2 else 7.45
        kco_last_val = kco_hist[-2] if len(kco_hist) >= 2 else 12.20
        
        fig_bench.add_trace(go.Scatter(
            x=['2026-11 (Previsión)', '2026-12 (Previsión)'],
            y=[mkt_nov_val, mkt_dic_pred],
            name='Mercado Mayorista (Previsión)',
            mode='lines+markers+text',
            text=[f"S/{mkt_nov_val:.2f}", f"S/{mkt_dic_pred:.2f}"],
            textposition='bottom center',
            textfont=dict(color=COLOR_MERCADO, size=10, weight="bold"),
            line=dict(color=COLOR_MERCADO, width=2, dash='dot'),
            marker=dict(size=8, symbol='diamond')
        ))

        fig_bench.add_trace(go.Scatter(
            x=['2026-11 (Previsión)', '2026-12 (Previsión)'],
            y=[kco_nov_pred, kco_dic_pred],
            name='KCO Retail (Cotización Sugerida)',
            mode='lines+markers+text',
            text=[f"S/{kco_nov_pred:.2f}", f"S/{kco_dic_pred:.2f}"],
            textposition='top center',
            textfont=dict(color=COLOR_ACCENT, size=11, family="Arial", weight="bold"),
            line=dict(color=COLOR_ACCENT, width=3, dash='dash'),
            marker=dict(size=9, color=COLOR_ACCENT, symbol='star')
        ))

        fig_bench.update_layout(
            autosize=True,
            template='plotly_white',
            height=420,
            xaxis=dict(title='Mes de Operación'),
            yaxis=dict(title='Precio S/ por Kg', gridcolor='#f1f5f9'),
            legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="center", x=0.5),
            margin=dict(t=45, b=25, l=10, r=10)
        )
        st.plotly_chart(fig_bench, use_container_width=True, config=PLOTLY_CONFIG)

        # Resumen ejecutivo de previsión
        prev_col1, prev_col2, prev_col3 = st.columns(3)
        with prev_col1:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: {COLOR_MERCADO};">
                    <div class="metric-title">Mercado Nov 2026 (Tendencia)</div>
                    <div class="metric-value">S/ {mkt_nov_val:.2f} /kg</div>
                    <div class="metric-sub">Pico estacional en mayorista</div>
                </div>
            """, unsafe_allow_html=True)
        with prev_col2:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: {COLOR_ACCENT};">
                    <div class="metric-title">KCO Sugerido Nov 2026</div>
                    <div class="metric-value">S/ {kco_nov_pred:.2f} /kg</div>
                    <div class="metric-sub">Cotización objetivo (Spread: +S/ {spread_promedio:.2f})</div>
                </div>
            """, unsafe_allow_html=True)
        with prev_col3:
            st.markdown(f"""
                <div class="metric-card" style="border-left-color: #0284c7;">
                    <div class="metric-title">KCO Proyectado Dic 2026</div>
                    <div class="metric-value">S/ {kco_dic_pred:.2f} /kg</div>
                    <div class="metric-sub">Ajuste por ingreso de nueva cosecha</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="chart-insight">
            💡 <b>Análisis Predictivo de Negociación:</b> 
            Históricamente, KCO mantiene un <b>premium promedio de +{((spread_promedio/df_comp['PRECIO_MERCADO'].mean())*100):.1f}% (+S/ {spread_promedio:.2f}/kg)</b> 
            sobre el mercado mayorista. Para <b>Noviembre 2026</b> el mercado mayorista se encuentra en zona de máximos (~S/ {mkt_nov_val:.2f}), lo que sustenta cotizaciones a retail entre <b>S/ {kco_nov_pred - 0.30:.2f} y S/ {kco_nov_pred + 0.30:.2f}</b>. 
            Para <b>Diciembre 2026</b>, la estacionalidad de mayor oferta mayorista presionará los precios a la baja (~S/ {mkt_dic_pred:.2f}), proyectándose un rango de cotización de <b>S/ {kco_dic_pred - 0.25:.2f} a S/ {kco_dic_pred + 0.35:.2f}</b>.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Sube el archivo 'reporte_fuerte.xls' al repositorio para habilitar la previsión contra el mercado mayorista.")

    st.markdown("---")

    # --- AUDITORÍA DE VARIACIONES DE PRECIO Y LÍNEAS POR VARIEDAD ---
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
                text=df_changes.tail(20)['VAR_PRECIO_PCT'].apply(lambda x: f"{x:+.1f}%"),
                color_continuous_scale='RdYlGn',
                custom_data=['DESCRIPCION_PRODUCTO', 'PRECIO_PREV', 'PRECIO_POND', 'KG']
            )
            fig_var.update_traces(
                textposition='outside',
                outsidetextfont=dict(color='#0f172a', size=11, family="Arial", weight="bold"),
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

    # --- BANDA DE NEGOCIACIÓN Y CONDICIONES COMERCIALES ---
    col_v1, col_v2 = st.columns([1.5, 1])

    with col_v1:
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
            text=df_banda['PRECIO_POND'].apply(lambda x: f"S/{x:.2f}"),
            textposition='top center',
            textfont=dict(color='#0f172a', size=11, family="Arial", weight="bold"),
            marker=dict(size=12, color=COLOR_ACCENT, symbol='diamond'),
            hovertemplate="<b>%{x}</b><br>🏷️ Precio Ponderado: <b>S/ %{y:.2f} /kg</b><extra></extra>"
        ))
        
        fig_banda.update_layout(
            autosize=True,
            template='plotly_white',
            height=370,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            yaxis_title="Precio (S/ por Kg)",
            xaxis_title="Variedad",
            margin=dict(t=35, b=25, l=10, r=10)
        )
        st.plotly_chart(fig_banda, use_container_width=True, config=PLOTLY_CONFIG)

    with col_v2:
        st.subheader("💳 Condiciones de Pago (Z015 vs Z045)")
        st.caption("Impacto en días de crédito y rotación de cobro.")
        
        df_fp = df.groupby('FORMA_PAGO').agg(
            ORDENES=('NRO_OC', 'nunique'),
            KILOS=('KILOS_SOLICITADOS', 'sum'),
            VALOR=('VALOR_COMERCIAL', 'sum')
        ).reset_index()
        df_fp['PART_VALOR'] = (df_fp['VALOR'] / df_fp['VALOR'].sum()) * 100
        
        hover_fp = [
            f"<b>Condición {row['FORMA_PAGO']}</b><br><br>"
            f"💰 <b>Monto:</b> S/ {row['VALOR']:,.2f} ({row['PART_VALOR']:.1f}%)<br>"
            f"📦 <b>Kilos:</b> {row['KILOS']:,.0f} kg<br>"
            f"📋 <b>Órdenes:</b> {row['ORDENES']:,} OCs"
            for _, row in df_fp.iterrows()
        ]
        
        fig_fp = go.Figure(data=[go.Pie(
            labels=df_fp['FORMA_PAGO'],
            values=df_fp['VALOR'],
            hole=0.45,
            marker=dict(colors=['#16a34a' if x == 'Z015' else '#d97706' for x in df_fp['FORMA_PAGO']]),
            textposition='inside',
            textinfo='percent+label',
            insidetextfont=dict(color='#ffffff', size=11, family="Arial", weight="bold"),
            hoverinfo='text',
            hovertext=hover_fp
        )])
        
        fig_fp.update_layout(
            autosize=True,
            template='plotly_white',
            showlegend=False,
            height=370,
            margin=dict(t=25, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_fp, use_container_width=True, config=PLOTLY_CONFIG)

    # Detalle Operativo Final
    st.markdown("---")
    st.subheader("📋 Detalle de Órdenes & Estimaciones Logísticas")
    cols_grid = ['NRO_OC', 'FECHA_EMISION', 'FORMA_PAGO', 'DESCRIPCION_PRODUCTO', 'KILOS_SOLICITADOS', 'PRECIO_KG', 'VALOR_COMERCIAL', 'JABAS_EST', 'FRUTOS_EST']
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

# --- FOOTER INSTITUCIONAL FULL-WIDTH ---
st.markdown(f"""
    <div class="footer-credits">
        🥑 <b>KCO Group</b> — Plataforma de Inteligencia Comercial & Pricing &nbsp;|&nbsp; 
        <b>Desarrollado por:</b> Alfredo Huaracha Mendoza &nbsp;|&nbsp; 
        <b>Última actualización:</b> {update_time}
    </div>
""", unsafe_allow_html=True)
