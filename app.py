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

# --- PALETA CORPORATIVA DE ALTO CONTRASTE ---
COLOR_PRIMARY = "#1b4332"
COLOR_SECONDARY = "#2d6a4f"
COLOR_ACCENT = "#d97706"
COLOR_NEUTRAL = "#0f172a"
COLOR_INFO = "#0284c7"

VARIEDAD_COLORS = {
    'PALTA-FUERTE-A-KG': '#1b4332',  # Verde bosque
    'PALTA-FUERTE-V-KG': '#0284c7',  # Azul zafiro
    'PALTA-FUERTE-P-KG': '#d97706',  # Ámbar tostado
    'PALTA-FUERTE-C-KG': '#7c3aed',  # Púrpura intenso
    'PALTA-M-KG':        '#16a34a'   # Verde esmeralda
}
DEFAULT_PALETTE = list(VARIEDAD_COLORS.values())

# --- ESTILOS CSS UI/UX ---
st.markdown(f"""
    <style>
    .main {{ background-color: #f8fafc; }}
    
    .metric-card {{
        background: #ffffff;
        padding: 18px 22px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border-left: 5px solid {COLOR_PRIMARY};
        margin-bottom: 14px;
    }}
    .metric-title {{
        font-size: 11px;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }}
    .metric-value {{
        font-size: 24px;
        color: {COLOR_NEUTRAL};
        font-weight: 800;
        margin-top: 4px;
    }}
    .metric-sub {{
        font-size: 11.5px;
        color: #94a3b8;
        margin-top: 3px;
        font-weight: 500;
    }}
    .chart-insight {{
        background-color: #f1f5f9;
        border-left: 4px solid {COLOR_PRIMARY};
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 12.5px;
        color: #334155;
        margin-top: 10px;
        margin-bottom: 18px;
        line-height: 1.45;
    }}
    .filter-box {{
        background-color: #ffffff;
        padding: 18px 22px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 18px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }}
    </style>
""", unsafe_allow_html=True)

# --- MAESTRO DE PRODUCTOS ---
PRODUCT_WEIGHTS = {
    'PALTA-FUERTE-A-KG': 0.250,
    'PALTA-FUERTE-V-KG': 0.280,
    'PALTA-FUERTE-P-KG': 0.220,
    'PALTA-FUERTE-C-KG': 0.200,
    'PALTA-M-KG': 0.150
}
KG_PER_JABA = 18.0

# --- FUNCIÓN DE SEMAFORIZACIÓN ---
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

    # Fechas y Agrupaciones
    df['FECHA_EMISION'] = pd.to_datetime(df['FECHA_EMISION'], format='%d-%m-%Y', errors='coerce')
    df['MES_AÑO'] = df['FECHA_EMISION'].dt.strftime('%Y-%m')
    df['SEMANA_AÑO'] = df['FECHA_EMISION'].dt.strftime('%Y-W%V')
    
    # Estandarización de variables comerciales
    df['KILOS_SOLICITADOS'] = df['UNIDADES_SOLICITADAS'].fillna(0)
    df['PRECIO_KG'] = df['PRECIO_FINAL_NETO'].fillna(0)
    df['VALOR_COMERCIAL'] = df['KILOS_SOLICITADOS'] * df['PRECIO_KG']
    df['FORMA_PAGO'] = df['FORMA_PAGO'].fillna('No Definido')
    
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
st.markdown("Análisis estratégico de ventas y pricing en canal Retail: Tendencias periódicas, monitoreo de precios y auditoría operativa.")

# --- SEGMENTACIÓN SUPERIOR ---
st.markdown('<div class="filter-box">', unsafe_allow_html=True)
f_row1, f_row2 = st.columns([3, 1])

with f_row1:
    st.markdown("##### 🔍 Segmentación de Información")
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
    st.markdown("##### ⏱️ Agrupación Temporal")
    periodo_seleccionado = st.radio(
        "Ver gráficos agrupados por:",
        options=["Mensual", "Semanal"],
        horizontal=True
    )
st.markdown('</div>', unsafe_allow_html=True)

col_periodo = 'MES_AÑO' if periodo_seleccionado == "Mensual" else 'SEMANA_AÑO'
label_periodo = "Mes" if periodo_seleccionado == "Mensual" else "Semana"

# Aplicar Filtros
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
total_ocs = df['NRO_OC'].nunique()  # Conteo único sin duplicados
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
    "📈 2. Análisis de Precios (Pricing), Variaciones % & Condiciones Comerciales"
])

# ==========================================================
# PESTAÑA 1: RESUMEN EJECUTIVO & EVOLUCIÓN PERIÓDICA
# ==========================================================
with tab1:
    df_trend = df.groupby(col_periodo).agg(
        KG_TOTALES=('KILOS_SOLICITADOS', 'sum'),
        VALOR_TOTAL=('VALOR_COMERCIAL', 'sum'),
        ORDENES=('NRO_OC', 'nunique')  # Validación de órdenes únicas
    ).reset_index()
    df_trend['PRECIO_POND'] = df_trend['VALOR_TOTAL'] / df_trend['KG_TOTALES']
    df_trend['TN_TOTALES'] = df_trend['KG_TOTALES'] / 1000.0
    
    df_trend['VAR_KG_PCT'] = df_trend['KG_TOTALES'].pct_change() * 100
    df_trend['VAR_PRECIO_PCT'] = df_trend['PRECIO_POND'].pct_change() * 100
    df_trend['VAR_VALOR_PCT'] = df_trend['VALOR_TOTAL'].pct_change() * 100

    col_g1, col_g2 = st.columns([1.55, 1])

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
            marker=dict(size=8, color=COLOR_ACCENT),
            line=dict(width=3, color=COLOR_ACCENT),
            hovertemplate=(
                f"<b>{label_periodo}: %{{x}}</b><br>" +
                "🏷️ <b>Precio Ponderado: S/ %{y:.2f} /kg</b><extra></extra>"
            ),
            yaxis='y2'
        ))

        fig_dual.update_layout(
            xaxis=dict(title=label_periodo, tickangle=-45 if periodo_seleccionado == "Semanal" else 0),
            yaxis=dict(title='Volumen Total (Toneladas)', showgrid=False),
            yaxis2=dict(title='Precio Ponderado (S/ por Kg)', overlaying='y', side='right', showgrid=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template='plotly_white',
            height=410,
            margin=dict(t=30, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_dual, use_container_width=True)
        
        max_vol_row = df_trend.loc[df_trend['KG_TOTALES'].idxmax()]
        max_p_row = df_trend.loc[df_trend['PRECIO_POND'].idxmax()]
        st.markdown(f"""
        <div class="chart-insight">
            💡 <b>Insight Comercial ({periodo_seleccionado}):</b> 
            El pico de volumen se registró en <b>{max_vol_row[col_periodo]}</b> con <b>{max_vol_row['TN_TOTALES']:.1f} Toneladas</b> ({max_vol_row['ORDENES']} OCs). 
            El mayor precio ponderado de venta se alcanzó en <b>{max_p_row[col_periodo]}</b> a <b>S/ {max_p_row['PRECIO_POND']:.2f} /kg</b>.
        </div>
        """, unsafe_allow_html=True)

    with col_g2:
        st.subheader("Mix y Concentración por Producto")
        
        # Agrupación precisa por producto
        df_prod = df.groupby('DESCRIPCION_PRODUCTO').agg(
            VALOR=('VALOR_COMERCIAL', 'sum'),
            KG=('KILOS_SOLICITADOS', 'sum'),
            ORDENES=('NRO_OC', 'nunique')
        ).reset_index()
        df_prod['PRECIO_POND'] = df_prod['VALOR'] / df_prod['KG']
        
        # Mapeo de colores estricto
        pie_colors = [VARIEDAD_COLORS.get(prod, '#2d6a4f') for prod in df_prod['DESCRIPCION_PRODUCTO']]
        
        # Matriz 2D para customdata en Pie chart
        customdata_matrix = np.column_stack((
            df_prod['KG'],
            df_prod['PRECIO_POND'],
            df_prod['ORDENES'],
            df_prod['VALOR']
        ))
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=df_prod['DESCRIPCION_PRODUCTO'],
            values=df_prod['VALOR'],
            hole=0.45,
            marker=dict(colors=pie_colors),
            textposition='inside',
            textinfo='percent+label',
            customdata=customdata_matrix,
            hovertemplate=(
                "<b>Variedad: %{label}</b><br>" +
                "💰 Facturación: S/ %{customdata[3]:,.2f} (%{percent})<br>" +
                "📦 Volumen Total: %{customdata[0]:,.0f} kg<br>" +
                "🏷️ Precio Ponderado: S/ %{customdata[1]:.2f} /kg<br>" +
                "📋 Órdenes Únicas: %{customdata[2]:,}<extra></extra>"
            )
        )])
        
        fig_pie.update_layout(
            template='plotly_white',
            showlegend=False,
            height=410,
            margin=dict(t=30, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        top_prod = df_prod.loc[df_prod['VALOR'].idxmax()]
        part_top = (top_prod['VALOR'] / valor_comercial_total) * 100
        st.markdown(f"""
        <div class="chart-insight">
            📌 <b>Concentración de Portafolio:</b> <b>{top_prod['DESCRIPCION_PRODUCTO']}</b> concentra el <b>{part_top:.1f}%</b> de la facturación en el periodo filtrado (S/ {top_prod['VALOR']:,.0f}).
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # --- GRÁFICO DEDICADO DE ÓRDENES DE COMPRA ÚNICAS Y MATRIZ DE VARIACIÓN ---
    col_oc1, col_oc2 = st.columns([1.1, 1.4])
    
    with col_oc1:
        st.subheader(f"📋 Órdenes de Compra Únicas por {label_periodo}")
        fig_oc_bars = px.bar(
            df_trend,
            x=col_periodo,
            y='ORDENES',
            text='ORDENES',
            color='ORDENES',
            color_continuous_scale='Greens',
            labels={col_periodo: label_periodo, 'ORDENES': 'Órdenes de Compra (OC)'}
        )
        fig_oc_bars.update_traces(
            textposition='outside',
            hovertemplate=f"<b>{label_periodo}: %{{x}}</b><br>📋 Órdenes Únicas: <b>%{{y:,}}</b><extra></extra>"
        )
        fig_oc_bars.update_layout(
            template='plotly_white',
            height=370,
            coloraxis_showscale=False,
            xaxis=dict(tickangle=-45 if periodo_seleccionado == "Semanal" else 0),
            margin=dict(t=30, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_oc_bars, use_container_width=True)

    with col_oc2:
        st.subheader(f"📋 Matriz Periódica de Variación ({periodo_seleccionado})")
        st.caption("Semáforo: 🟢 Aumento > +2% | 🟡 Estable [-2%, +2%] | 🔴 Descenso < -2%")
        
        df_var_display = df_trend[[col_periodo, 'KG_TOTALES', 'VAR_KG_PCT', 'PRECIO_POND', 'VAR_PRECIO_PCT', 'VALOR_TOTAL', 'VAR_VALOR_PCT']].copy()
        df_var_display.columns = [label_periodo, 'Kilos Solicitados', 'Var. Kg %', 'Precio Ponderado', 'Var. Precio %', 'Venta Bruta (S/)', 'Var. Venta %']
        
        st.dataframe(
            df_var_display.style.format({
                'Kilos Solicitados': '{:,.0f} kg',
                'Var. Kg %': '{:+.1f}%',
                'Precio Ponderado': 'S/ {:.2f}',
                'Var. Precio %': '{:+.1f}%',
                'Venta Bruta (S/)': 'S/ {:,.0f}',
                'Var. Venta %': '{:+.1f}%'
            })
            .map(style_semaphore, subset=['Var. Kg %', 'Var. Precio %', 'Var. Venta %'])
            .highlight_null(color='#f1f5f9'),
            use_container_width=True, height=330, hide_index=True
        )

# ==========================================================
# PESTAÑA 2: PRICING, VARIACIONES % & CONDICIONES COMERCIALES
# ==========================================================
with tab2:
    st.subheader("🔍 Auditoría de Variaciones de Precios por Producto")
    st.markdown(f"Evolución y variaciones porcentuales agrupadas por **{periodo_seleccionado.lower()}** para cada variedad.")
    
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
                df_changes.tail(25),
                x=col_periodo,
                y='VAR_PRECIO_PCT',
                color='VAR_PRECIO_PCT',
                text=df_changes.tail(25)['VAR_PRECIO_PCT'].apply(lambda x: f"{x:+.1f}%"),
                color_continuous_scale='RdYlGn',
                custom_data=['DESCRIPCION_PRODUCTO', 'PRECIO_PREV', 'PRECIO_POND', 'KG']
            )
            fig_var.update_traces(
                textposition='outside',
                hovertemplate=(
                    f"<b>{label_periodo}: %{{x}}</b><br>" +
                    "🥑 <b>Producto: %{customdata[0]}</b><br>" +
                    "🏷️ Precio Anterior: S/ %{customdata[1]:.2f} /kg<br>" +
                    "🏷️ Precio Nuevo: S/ %{customdata[2]:.2f} /kg<br>" +
                    "📊 Variación: <b>%{y:+.2f}%</b><br>" +
                    "📦 Volumen del Periodo: %{customdata[3]:,.0f} kg<extra></extra>"
                )
            )
            fig_var.update_layout(
                template='plotly_white',
                xaxis=dict(title=label_periodo, tickangle=-45 if periodo_seleccionado == "Semanal" else 0),
                yaxis=dict(title='Variación Porcentual (%)'),
                height=440,
                margin=dict(t=20, b=20, l=10, r=10)
            )
            st.plotly_chart(fig_var, use_container_width=True)
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
            height=440,
            margin=dict(t=50, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_line_prod, use_container_width=True)

    if not df_changes.empty:
        st.markdown("##### Matriz Detallada de Cambios de Precio")
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
    col_v1, col_v2 = st.columns([1.4, 1])

    with col_v1:
        st.subheader("🎯 Banda de Negociación de Precios (Mínimo, Ponderado y Máximo)")
        st.markdown("Rango efectivo de precios pactados por variedad en el periodo analizado.")
        
        df_banda = df.groupby('DESCRIPCION_PRODUCTO').agg(
            PRECIO_MIN=('PRECIO_KG', 'min'),
            PRECIO_MAX=('PRECIO_KG', 'max'),
            KILOS=('KILOS_SOLICITADOS', 'sum'),
            VALOR=('VALOR_COMERCIAL', 'sum')
        ).reset_index()
        df_banda['PRECIO_POND'] = df_banda['VALOR'] / df_banda['KILOS']
        
        fig_banda = go.Figure()
        
        # Banda Min-Max
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
        
        # Marcador de Precio Ponderado Real
        fig_banda.add_trace(go.Scatter(
            name='Precio Ponderado Real',
            x=df_banda['DESCRIPCION_PRODUCTO'],
            y=df_banda['PRECIO_POND'],
            mode='markers+text',
            text=df_banda['PRECIO_POND'].apply(lambda x: f"S/{x:.2f}"),
            textposition='top center',
            marker=dict(size=12, color=COLOR_ACCENT, symbol='diamond'),
            hovertemplate="<b>%{x}</b><br>🏷️ Precio Ponderado: <b>S/ %{y:.2f} /kg</b><extra></extra>"
        ))
        
        fig_banda.update_layout(
            template='plotly_white',
            height=370,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            yaxis_title="Precio (S/ por Kg)",
            xaxis_title="Variedad",
            margin=dict(t=40, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_banda, use_container_width=True)

    with col_v2:
        st.subheader("💳 Condiciones de Pago (Z015 vs Z045)")
        st.markdown("Impacto en días de crédito y rotación de cobro.")
        
        df_fp = df.groupby('FORMA_PAGO').agg(
            ORDENES=('NRO_OC', 'nunique'),
            KILOS=('KILOS_SOLICITADOS', 'sum'),
            VALOR=('VALOR_COMERCIAL', 'sum')
        ).reset_index()
        df_fp['PART_VALOR'] = (df_fp['VALOR'] / df_fp['VALOR'].sum()) * 100
        
        fig_fp = px.pie(
            df_fp,
            names='FORMA_PAGO',
            values='VALOR',
            hole=0.45,
            color='FORMA_PAGO',
            color_discrete_map={'Z015': '#16a34a', 'Z045': '#d97706', 'No Definido': '#94a3b8'}
        )
        fig_fp.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate="<b>Condición %{label}</b><br>Monto: S/ %{value:,.2f} (%{percent})<extra></extra>"
        )
        fig_fp.update_layout(
            template='plotly_white',
            showlegend=False,
            height=370,
            margin=dict(t=40, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_fp, use_container_width=True)

    st.markdown("""
    <div class="chart-insight">
        📌 <b>Diagnóstico Financiero de Negociación:</b> 
        El cliente migró sus órdenes de compra al plazo <b>Z045 (45 días)</b> a partir de abril, absorbiendo más del 95% de la facturación anual. 
        En la banda de precios, variedades como <b>PALTA-M-KG</b> y <b>PALTA-FUERTE-V-KG</b> exhiben mayor amplitud de negociación (techo superior a S/ 12.00 en temporada baja).
    </div>
    """, unsafe_allow_html=True)

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
