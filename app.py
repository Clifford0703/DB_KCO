import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Pricing & Volumen - InRetail 2026",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {font-size: 26px; font-weight: 700; color: #1B365D; margin-bottom: 4px;}
    .sub-header {font-size: 14px; color: #4A5568; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🥑 Dashboard Comercial de Pricing, Volumen y Negociación - InRetail 2026</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Control de órdenes de compra (CD 918), elasticidad precio-volumen, evolución por calibre y simulador de descuentos para distribuidor.</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. CARGA Y PROCESAMIENTO DE DATOS
# ==============================================================================
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    else:
        try:
            df = pd.read_excel("Ordenes al 06-11-2026 09.39.25 hrs.xls")
        except Exception:
            try:
                df = pd.read_excel("Dashboard_Interactivo_Pricing_InRetail_2026.xlsx", sheet_name="Base_Ordenes_2026", skiprows=2)
            except Exception:
                return pd.DataFrame()

    col_map = {
        'PRECIO_FINAL_CON_IMP': 'PRECIO_KG',
        'PRECIO_FINAL_NETO': 'PRECIO_KG',
        'PRECIO_FINAL_KG': 'PRECIO_KG',
        'SKU_EMPAQUE': 'KG_POR_JABA',
        'PESO KG/JABA': 'KG_POR_JABA',
        'UNIDADES_EN_DESPACHO': 'UNIDADES_DESPACHADAS'
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    if 'FECHA_EMISION' in df.columns:
        df['FECHA_EMISION_DT'] = pd.to_datetime(df['FECHA_EMISION'], format='%d-%m-%Y', errors='coerce')
        if df['FECHA_EMISION_DT'].isna().all():
            df['FECHA_EMISION_DT'] = pd.to_datetime(df['FECHA_EMISION'], errors='coerce')
            
    if 'FECHA_ENTREGA' in df.columns:
        df['FECHA_ENTREGA_DT'] = pd.to_datetime(df['FECHA_ENTREGA'], format='%d-%m-%Y', errors='coerce')
        if df['FECHA_ENTREGA_DT'].isna().all():
            df['FECHA_ENTREGA_DT'] = pd.to_datetime(df['FECHA_ENTREGA'], errors='coerce')

    df = df.dropna(subset=['FECHA_EMISION_DT', 'DESCRIPCION_PRODUCTO'])

    if 'KG_POR_JABA' not in df.columns:
        df['KG_POR_JABA'] = 18

    df['MES'] = df['FECHA_EMISION_DT'].dt.strftime('%Y-%m')
    df['SEMANA'] = df['FECHA_EMISION_DT'].dt.isocalendar().week.astype(int)
    df['TOTAL_KG'] = df['UNIDADES_SOLICITADAS'] * df['KG_POR_JABA']
    df['TONELADAS'] = df['TOTAL_KG'] / 1000.0
    df['VENTA_SOLES'] = df['TOTAL_KG'] * df['PRECIO_KG']

    if 'FORMA_PAGO' not in df.columns:
        df['FORMA_PAGO'] = np.where(df['MES'].isin(['2026-02', '2026-03']), 'Z015', 'Z045')

    df['DIAS_CREDITO'] = np.where(df['FORMA_PAGO'] == 'Z015', 15, 45)
    df['TAMANO_PEDIDO'] = np.where(
        df['UNIDADES_SOLICITADAS'] < 100, '1. Crítico (<100 jabas)',
        np.where(df['UNIDADES_SOLICITADAS'] < 400, '2. Medio (100-399 jabas)', '3. Óptimo (>=400 jabas)')
    )
    return df

# ==============================================================================
# 3. BARRA LATERAL (FILTROS E INGESTA)
# ==============================================================================
with st.sidebar:
    st.header("📂 Origen de Datos")
    uploaded_file = st.file_uploader(
        "Sube tu reporte de Órdenes InRetail (.xls, .xlsx, .csv)",
        type=["xls", "xlsx", "csv"]
    )
    df_raw = load_data(uploaded_file)

    if df_raw.empty:
        st.warning("Sube el archivo 'Ordenes al 06-11-2026 09.39.25 hrs.xls' o colócalo en la raíz de tu repositorio GitHub.")
        st.stop()

    st.divider()
    st.header("🔍 Filtros Interactivos")

    meses_disp = sorted(df_raw['MES'].unique())
    sel_meses = st.multiselect("Mes de Emisión:", options=meses_disp, default=meses_disp)

    prods_disp = sorted(df_raw['DESCRIPCION_PRODUCTO'].unique())
    sel_prods = st.multiselect("Código de Producto (SKU):", options=prods_disp, default=prods_disp)

    pagos_disp = sorted(df_raw['FORMA_PAGO'].unique())
    sel_pagos = st.multiselect("Condición de Pago:", options=pagos_disp, default=pagos_disp)

df = df_raw[
    (df_raw['MES'].isin(sel_meses)) &
    (df_raw['DESCRIPCION_PRODUCTO'].isin(sel_prods)) &
    (df_raw['FORMA_PAGO'].isin(sel_pagos))
].copy()

if df.empty:
    st.error("No hay órdenes para la combinación de filtros seleccionada.")
    st.stop()

# ==============================================================================
# 4. TARJETAS KPI PRINCIPALES
# ==============================================================================
total_tn = df['TONELADAS'].sum()
total_jabas = df['UNIDADES_SOLICITADAS'].sum()
total_soles = df['VENTA_SOLES'].sum()
precio_pond = total_soles / df['TOTAL_KG'].sum() if df['TOTAL_KG'].sum() > 0 else 0
total_ocs = df['NRO_OC'].nunique() if 'NRO_OC' in df.columns else len(df)
ocs_criticas = (df['UNIDADES_SOLICITADAS'] < 100).sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Volumen Total", f"{total_tn:,.1f} Tn", f"{total_jabas:,.0f} jabas")
c2.metric("Facturación Neta", f"S/ {total_soles:,.0f}", f"{total_ocs} OCs emitidas")
c3.metric("Precio Prom. Ponderado", f"S/ {precio_pond:,.2f} /kg", f"Rango: S/ {df['PRECIO_KG'].min():.2f} - S/ {df['PRECIO_KG'].max():.2f}")
c4.metric("Pedidos Chicos (<100 jabas)", f"{ocs_criticas} líneas", f"{(ocs_criticas/len(df))*100:.1f}% del total", delta_color="inverse")
c5.metric("Condición Dominante", "Z045 (45 días)", f"{(df['FORMA_PAGO']=='Z045').mean()*100:.1f}% de líneas")

st.divider()

# ==============================================================================
# 5. PESTAÑAS DEL DASHBOARD
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 1. Curvas de Volumen y Precio",
    "🥑 2. Análisis por Calibre y Elasticidad",
    "🧮 3. Simulador de Cotización y Descuentos",
    "📋 4. Base de Órdenes y Alertas MOQ"
])

with tab1:
    col_vista, _ = st.columns([2, 6])
    with col_vista:
        frecuencia = st.radio("Agrupación Temporal:", ["Semanal", "Mensual"], horizontal=True)

    grp_col = 'SEMANA' if frecuencia == "Semanal" else 'MES'
    df_temp = df.groupby(grp_col).agg(
        Toneladas=('TONELADAS', 'sum'),
        Jabas=('UNIDADES_SOLICITADAS', 'sum'),
        Facturacion=('VENTA_SOLES', 'sum'),
        Kilos=('TOTAL_KG', 'sum')
    ).reset_index()
    df_temp['Precio_Ponderado'] = df_temp['Facturacion'] / df_temp['Kilos']

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader(f"Curva {frecuencia}: Volumen (Tn) vs. Precio Ponderado (S//kg)")
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Bar(
            x=df_temp[grp_col],
            y=df_temp['Toneladas'],
            name='Volumen (Tn)',
            marker_color='#2B6CB0',
            opacity=0.8
        ))
        fig_dual.add_trace(go.Scatter(
            x=df_temp[grp_col],
            y=df_temp['Precio_Ponderado'],
            name='Precio Pond. (S//kg)',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='#E53E3E', width=3),
            marker=dict(size=7)
        ))
        fig_dual.update_layout(
            yaxis=dict(title="Toneladas (Tn)"),
            yaxis2=dict(title="Precio Ponderado (S//kg)", overlaying='y', side='right'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=420,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    with col_g2:
        st.subheader(f"Evolución {frecuencia} de Volumen por Calibre (Tn)")
        df_mix = df.groupby([grp_col, 'DESCRIPCION_PRODUCTO'])['TONELADAS'].sum().reset_index()
        fig_mix = px.bar(
            df_mix,
            x=grp_col,
            y='TONELADAS',
            color='DESCRIPCION_PRODUCTO',
            barmode='stack',
            labels={'TONELADAS': 'Toneladas (Tn)', grp_col: frecuencia, 'DESCRIPCION_PRODUCTO': 'Producto'},
            color_discrete_sequence=px.colors.qualitative.Safe,
            height=420
        )
        fig_mix.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_mix, use_container_width=True)

    st.subheader(f"Tabla Consolidada ({frecuencia})")
    st.dataframe(
        df_temp.style.format({
            'Toneladas': '{:,.1f} Tn',
            'Jabas': '{:,.0f}',
            'Kilos': '{:,.0f} kg',
            'Facturacion': 'S/ {:,.2f}',
            'Precio_Ponderado': 'S/ {:,.2f}'
        }),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    c_e1, c_e2 = st.columns(2)
    with c_e1:
        st.subheader("¿Bajar el precio aumenta el tamaño del pedido?")
        fig_scat = px.scatter(
            df,
            x='PRECIO_KG',
            y='UNIDADES_SOLICITADAS',
            color='DESCRIPCION_PRODUCTO',
            size='TONELADAS',
            hover_data=['FECHA_EMISION', 'NRO_OC', 'FORMA_PAGO'],
            labels={'PRECIO_KG': 'Precio Final Pactado (S//kg)', 'UNIDADES_SOLICITADAS': 'Jabas por Orden de Compra'},
            height=420
        )
        st.plotly_chart(fig_scat, use_container_width=True)

    with c_e2:
        st.subheader("Dispersión Histórica de Precios por Código")
        fig_box = px.box(
            df,
            x='DESCRIPCION_PRODUCTO',
            y='PRECIO_KG',
            color='DESCRIPCION_PRODUCTO',
            points="all",
            labels={'DESCRIPCION_PRODUCTO': 'Producto', 'PRECIO_KG': 'Precio Pactado (S//kg)'},
            height=420
        )
        fig_box.update_layout(showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("Matriz Estratégica por Código de Producto")
    res_sku = df.groupby('DESCRIPCION_PRODUCTO').agg(
        Ordenes=('PRECIO_KG', 'count'),
        Jabas_Totales=('UNIDADES_SOLICITADAS', 'sum'),
        Toneladas=('TONELADAS', 'sum'),
        Facturacion=('VENTA_SOLES', 'sum'),
        Kilos=('TOTAL_KG', 'sum'),
        Precio_Min=('PRECIO_KG', 'min'),
        Precio_Max=('PRECIO_KG', 'max'),
        Jabas_Prom_OC=('UNIDADES_SOLICITADAS', 'mean')
    ).reset_index()
    res_sku['Precio_Ponderado'] = res_sku['Facturacion'] / res_sku['Kilos']
    res_sku['Share_Volumen_%'] = (res_sku['Toneladas'] / res_sku['Toneladas'].sum()) * 100

    st.dataframe(
        res_sku[['DESCRIPCION_PRODUCTO', 'Ordenes', 'Jabas_Totales', 'Toneladas', 'Share_Volumen_%',
                 'Facturacion', 'Precio_Min', 'Precio_Max', 'Precio_Ponderado', 'Jabas_Prom_OC']].style.format({
            'Jabas_Totales': '{:,.0f}',
            'Toneladas': '{:,.1f} Tn',
            'Share_Volumen_%': '{:.1f}%',
            'Facturacion': 'S/ {:,.2f}',
            'Precio_Min': 'S/ {:,.2f}',
            'Precio_Max': 'S/ {:,.2f}',
            'Precio_Ponderado': 'S/ {:,.2f}',
            'Jabas_Prom_OC': '{:,.0f} jabas'
        }),
        use_container_width=True,
        hide_index=True
    )

with tab3:
    st.subheader("🧮 Calculadora de Negociación, Margen Neto y Costo Financiero Z045")
    st.info("Ajusta tus costos de compra del día en el mercado mayorista/acopio y simula qué ocurre si el comprador de InRetail te pide descuento.")

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        sku_sim = st.selectbox("Producto a Cotizar:", options=prods_disp)
        jabas_base = st.number_input("Volumen Semanal Ofertado (Jabas):", min_value=50, max_value=15000, value=2412, step=50)
        costo_mercado = st.number_input("Costo de Compra en Plaza / Campo (S//kg):", min_value=2.0, max_value=20.0, value=9.50, step=0.10)

    with col_p2:
        precio_cotizado = st.number_input("Tu Precio Cotizado a InRetail (S//kg):", min_value=2.0, max_value=25.0, value=11.50, step=0.10)
        precio_objetivo = st.number_input("Precio Objetivo / Contraoferta Comprador (S//kg):", min_value=2.0, max_value=25.0, value=11.00, step=0.10)
        plazo_dias = st.selectbox("Condición de Pago InRetail:", options=[45, 15], index=0, format_func=lambda x: f"Z0{x} ({x} días)")

    with col_p3:
        flete_kg = st.number_input("Flete y Estiba a CD 918 (S//kg):", min_value=0.05, max_value=2.00, value=0.28, step=0.02)
        empaque_kg = st.number_input("Empaque / Jaba / Selección (S//kg):", min_value=0.00, max_value=2.00, value=0.15, step=0.02)
        merma_pct = st.slider("Merma / Rechazo en Rampa (%):", min_value=0.0, max_value=10.0, value=3.0, step=0.5) / 100.0
        tasa_anual = st.slider("Tasa Costo de Capital Anual (%):", min_value=5.0, max_value=35.0, value=18.0, step=1.0) / 100.0

    kilos_base = jabas_base * 18
    costo_fruta_ajustado = costo_mercado / (1.0 - merma_pct)
    costo_financiero_cot = precio_cotizado * (tasa_anual / 360.0) * plazo_dias
    costo_financiero_obj = precio_objetivo * (tasa_anual / 360.0) * plazo_dias

    costo_total_cot = costo_fruta_ajustado + flete_kg + empaque_kg + costo_financiero_cot
    costo_total_obj = costo_fruta_ajustado + flete_kg + empaque_kg + costo_financiero_obj

    margen_kg_cot = precio_cotizado - costo_total_cot
    margen_kg_obj = precio_objetivo - costo_total_obj

    utilidad_total_cot = kilos_base * margen_kg_cot
    utilidad_total_obj = kilos_base * margen_kg_obj

    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Costo Real Puesto en CD (+Financ.)", f"S/ {costo_total_obj:.2f} /kg", f"Incluye S/ {costo_financiero_obj:.2f} de Z0{plazo_dias}")
    k2.metric("Margen Neto (Tu Cotización)", f"S/ {margen_kg_cot:.2f} /kg", f"Utilidad: S/ {utilidad_total_cot:,.0f}")
    k3.metric("Margen Neto (Precio Comprador)", f"S/ {margen_kg_obj:.2f} /kg", f"{margen_kg_obj - margen_kg_cot:+.2f} S//kg vs cotizado")

    if margen_kg_obj <= 0:
        k4.metric("Jabas para Empatar Utilidad", "VENTA A PÉRDIDA", "Rechazar descuento", delta_color="inverse")
        st.error(f"🚨 **ALERTA ROJA:** A S/ {precio_objetivo:.2f}/kg pierdes **S/ {abs(margen_kg_obj):.2f} por cada kilo** entregado. Tu precio piso de equilibrio sin ganar un sol es **S/ {costo_total_obj:.2f}/kg**.")
    else:
        jabas_necesarias = (utilidad_total_cot / margen_kg_obj) / 18.0
        inc_pct = ((jabas_necesarias - jabas_base) / jabas_base) * 100
        k4.metric("Jabas Exigidas al Comprador", f"{jabas_necesarias:,.0f} jabas", f"+{inc_pct:.1f}% más volumen requerido", delta_color="off")
        st.success(f"💡 **ARGUMENTO DE NEGOCIACIÓN:** Si cedes de **S/ {precio_cotizado:.2f}** a **S/ {precio_objetivo:.2f}**, dejas de ganar **S/ {utilidad_total_cot - utilidad_total_obj:,.2f}** en la semana. Para aceptar ese precio sin perder utilidad neta, exígele al comprador un compromiso mínimo de **{jabas_necesarias:,.0f} jabas** (+{jabas_necesarias - jabas_base:,.0f} jabas adicionales).")

with tab4:
    st.subheader("Auditoría de Tamaño de Pedidos (Fuga Logística en CD 918)")
    res_tam = df.groupby('TAMANO_PEDIDO').agg(
        Lineas_OC=('PRECIO_KG', 'count'),
        Jabas=('UNIDADES_SOLICITADAS', 'sum'),
        Toneladas=('TONELADAS', 'sum'),
        Facturacion=('VENTA_SOLES', 'sum')
    ).reset_index()
    st.dataframe(res_tam, use_container_width=True, hide_index=True)

    st.subheader("Detalle Completo de Órdenes Filtradas")
    st.dataframe(df.sort_values('FECHA_EMISION_DT', ascending=False), use_container_width=True, hide_index=True)
