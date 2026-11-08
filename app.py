import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import glob
import os
from datetime import datetime

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO (MODO CLARO FORZADO)
# ==============================================================================
st.set_page_config(
    page_title="Control Pricing & Volumen - InRetail 2026",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Forzar fondo claro y textos legibles */
    .stApp {
        background-color: #FFFFFF;
        color: #1A202C;
    }
    .reportview-container .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
    .main-title {
        font-size: 26px;
        font-weight: 800;
        color: #1B365D;
        margin-bottom: 2px;
    }
    .sub-title {
        font-size: 13px;
        color: #4A5568;
        margin-bottom: 16px;
    }
    /* Estilo de tarjetas métricas */
    div[data-testid="metric-container"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 12px 16px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🥑 Control Maestro de Pricing, Volumen y OCs - InRetail 2026</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Carga directa desde GitHub | Curvas de volumen (Kg, Tn), Precios Ponderados, Auditoría de OCs y Simulador de Descuento.</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. CARGA AUTOMÁTICA DEL ARCHIVO (CON DETECCIÓN DE 30 COLUMNAS)
# ==============================================================================
@st.cache_data
def load_data(uploaded_file=None):
    df = None
    file_used = "Archivo subido manualmente"
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            file_used = uploaded_file.name
        except Exception as e:
            st.error(f"Error al leer archivo subido: {e}")
            return pd.DataFrame(), ""
    else:
        # Busca automáticamente en la raíz del repositorio de GitHub
        candidates = glob.glob("*.xls") + glob.glob("*.xlsx") + glob.glob("*.csv")
        # Excluir temporales de Excel
        candidates = [c for c in candidates if not os.path.basename(c).startswith("~$")]
        
        # Priorizar archivo de órdenes de compra
        priority = sorted(candidates, key=lambda x: (
            0 if "Ordenes" in x or "ordenes" in x else 1,
            -os.path.getmtime(x) if os.path.exists(x) else 0
        ))
        
        for cand in priority:
            try:
                if cand.endswith('.csv'):
                    df = pd.read_csv(cand)
                else:
                    df = pd.read_excel(cand)
                if df is not None and not df.empty and ('DESCRIPCION_PRODUCTO' in df.columns or 'NRO_OC' in df.columns):
                    file_used = cand
                    break
            except Exception:
                continue

    if df is None or df.empty:
        return pd.DataFrame(), ""

    # Mapeo y normalización para el archivo en bruto de 30 columnas
    col_map = {
        'PRECIO_FINAL_CON_IMP': 'PRECIO_KG',
        'PRECIO_FINAL_NETO': 'PRECIO_KG',
        'PRECIO_FINAL_KG': 'PRECIO_KG',
        'PRECIO_LISTA': 'PRECIO_LISTA_KG',
        'SKU_EMPAQUE': 'KG_POR_JABA',
        'PESO KG/JABA': 'KG_POR_JABA',
        'UNIDADES_EN_DESPACHO': 'UNIDADES_DESPACHADAS'
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Tratamiento de fechas
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

    # Variables operativas y comerciales calculadas
    df['MES'] = df['FECHA_EMISION_DT'].dt.strftime('%Y-%m')
    df['SEMANA'] = df['FECHA_EMISION_DT'].dt.isocalendar().week.astype(int)
    df['TOTAL_KG'] = df['UNIDADES_SOLICITADAS'] * df['KG_POR_JABA']
    df['TONELADAS'] = df['TOTAL_KG'] / 1000.0
    df['VENTA_SOLES'] = df['TOTAL_KG'] * df['PRECIO_KG']

    # Condición de pago
    if 'FORMA_PAGO' not in df.columns or df['FORMA_PAGO'].isna().all():
        df['FORMA_PAGO'] = np.where(df['MES'].isin(['2026-02', '2026-03']), 'Z015', 'Z045')
    else:
        df['FORMA_PAGO'] = df['FORMA_PAGO'].fillna('Z045')

    df['DIAS_CREDITO'] = np.where(df['FORMA_PAGO'] == 'Z015', 15, 45)
    df['TAMANO_PEDIDO'] = np.where(
        df['UNIDADES_SOLICITADAS'] < 100, '1. Crítico (<100 jabas)',
        np.where(df['UNIDADES_SOLICITADAS'] < 400, '2. Medio (100-399 jabas)', '3. Óptimo (>=400 jabas)')
    )
    return df, file_used

# ==============================================================================
# 3. BARRA LATERAL (ORIGEN + FILTROS DINÁMICOS)
# ==============================================================================
with st.sidebar:
    st.header("📂 Origen de Datos")
    uploaded_file = st.file_uploader(
        "Subir otro archivo (opcional):",
        type=["xls", "xlsx", "csv"],
        help="El sistema lee automáticamente el archivo .xls de tu repositorio. Usa esto solo si tienes un archivo nuevo no subido a GitHub."
    )
    df_raw, source_name = load_data(uploaded_file)

    if df_raw.empty:
        st.error("No se encontró ningún archivo en el repositorio. Sube un archivo para comenzar.")
        st.stop()

    st.success(f"Archivo cargado: `{os.path.basename(source_name)}`\n\nTotal filas: **{len(df_raw)}**")

    st.divider()
    st.header("🔍 Filtros Dinámicos")

    # 1. Filtro de Mes
    meses_disp = sorted(df_raw['MES'].unique())
    sel_meses = st.multiselect("📅 Filtrar por Mes:", options=meses_disp, default=meses_disp)

    # 2. Filtro de Semana (dependiente de los meses elegidos)
    df_f_mes = df_raw[df_raw['MES'].isin(sel_meses)] if sel_meses else df_raw
    semanas_disp = sorted(df_f_mes['SEMANA'].unique())
    sel_semanas = st.multiselect("🗓️ Filtrar por Semana Nº:", options=semanas_disp, default=semanas_disp)

    # 3. Filtro de Producto / SKU
    prods_disp = sorted(df_raw['DESCRIPCION_PRODUCTO'].unique())
    sel_prods = st.multiselect("🥑 Filtrar por Producto (Calibre):", options=prods_disp, default=prods_disp)

    # 4. Filtro de Condición de Pago
    pagos_disp = sorted(df_raw['FORMA_PAGO'].unique())
    sel_pagos = st.multiselect("💳 Condición de Pago:", options=pagos_disp, default=pagos_disp)

# Aplicación de los filtros
df = df_raw[
    (df_raw['MES'].isin(sel_meses)) &
    (df_raw['SEMANA'].isin(sel_semanas)) &
    (df_raw['DESCRIPCION_PRODUCTO'].isin(sel_prods)) &
    (df_raw['FORMA_PAGO'].isin(sel_pagos))
].copy()

if df.empty:
    st.warning("No hay órdenes que coincidan con la combinación de filtros seleccionada.")
    st.stop()

# ==============================================================================
# 4. TARJETAS KPI RESUMEN EJECUTIVO
# ==============================================================================
total_tn = df['TONELADAS'].sum()
total_kg = df['TOTAL_KG'].sum()
total_jabas = df['UNIDADES_SOLICITADAS'].sum()
total_soles = df['VENTA_SOLES'].sum()
precio_pond = (total_soles / total_kg) if total_kg > 0 else 0
total_ocs = df['NRO_OC'].nunique() if 'NRO_OC' in df.columns else len(df)
ocs_criticas = (df['UNIDADES_SOLICITADAS'] < 100).sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Volumen Total", f"{total_tn:,.1f} Tn", f"{total_kg:,.0f} Kg")
c2.metric("Jabas Totales", f"{total_jabas:,.0f} jabas", f"Prom: {total_jabas/total_ocs:,.0f} jaba/OC")
c3.metric("Facturación Neta", f"S/ {total_soles:,.2f}", f"{total_ocs} OCs únicas")
c4.metric("Precio Prom. Ponderado", f"S/ {precio_pond:.2f} /kg", f"Mín: {df['PRECIO_KG'].min():.2f} | Máx: {df['PRECIO_KG'].max():.2f}")
c5.metric("Órdenes <100 jabas", f"{ocs_criticas} OCs", f"{(ocs_criticas/len(df))*100:.1f}% del total", delta_color="inverse")

st.divider()

# ==============================================================================
# 5. PESTAÑAS PRINCIPALES DEL DASHBOARD
# ==============================================================================
tab_vol, tab_precios, tab_ocs, tab_simulador, tab_datos = st.tabs([
    "📊 1. Curvas de Volumen & Ventas (Kg, Tn, S/)",
    "💰 2. Curvas de Precios Ponderados (Mes y Semana)",
    "📦 3. Auditoría de Órdenes (OCs) y Frecuencia",
    "🧮 4. Simulador de Cotización y Descuentos",
    "📋 5. Datos Filtrados (Descarga CSV)"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: CURVAS DE VOLUMEN Y VENTAS
# ------------------------------------------------------------------------------
with tab_vol:
    st.subheader("Curvas de Volumen y Facturación Neta")
    col_ctrl1, col_ctrl2 = st.columns([2, 4])
    with col_ctrl1:
        frec_v = st.radio("Frecuencia de Agrupación:", ["Semanal", "Mensual"], horizontal=True, key="frec_v")
    with col_ctrl2:
        unit_v = st.radio("Unidad de Medida:", ["Toneladas (Tn)", "Kilos (Kg)", "Jabas"], horizontal=True, key="unit_v")

    time_col = 'SEMANA' if frec_v == "Semanal" else 'MES'
    y_col = 'TONELADAS' if unit_v == "Toneladas (Tn)" else ('TOTAL_KG' if unit_v == "Kilos (Kg)" else 'UNIDADES_SOLICITADAS')

    df_vt = df.groupby(time_col).agg(
        Volumen=(y_col, 'sum'),
        Facturacion=('VENTA_SOLES', 'sum'),
        Kilos=('TOTAL_KG', 'sum'),
        Jabas=('UNIDADES_SOLICITADAS', 'sum')
    ).reset_index()
    df_vt['Precio_Ponderado'] = df_vt['Facturacion'] / df_vt['Kilos']

    cv1, cv2 = st.columns(2)
    with cv1:
        st.markdown(f"**Curva {frec_v}: {unit_v} vs. Facturación (S/)**")
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Bar(
            x=df_vt[time_col],
            y=df_vt['Volumen'],
            name=unit_v,
            marker_color='#2B6CB0',
            opacity=0.85
        ))
        fig_dual.add_trace(go.Scatter(
            x=df_vt[time_col],
            y=df_vt['Facturacion'],
            name="Facturación (S/)",
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='#38A169', width=3),
            marker=dict(size=6)
        ))
        fig_dual.update_layout(
            yaxis=dict(title=unit_v),
            yaxis2=dict(title="Facturación Neta (S/)", overlaying='y', side='right'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=420,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    with cv2:
        st.markdown(f"**Composición de Volumen por Calibre ({frec_v})**")
        df_mix = df.groupby([time_col, 'DESCRIPCION_PRODUCTO'])[y_col].sum().reset_index()
        fig_mix = px.bar(
            df_mix,
            x=time_col,
            y=y_col,
            color='DESCRIPCION_PRODUCTO',
            barmode='stack',
            labels={y_col: unit_v, time_col: frec_v, 'DESCRIPCION_PRODUCTO': 'Calibre'},
            color_discrete_sequence=px.colors.qualitative.Safe,
            height=420
        )
        fig_mix.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_mix, use_container_width=True)

    st.markdown(f"**Tabla Consolidada de Volumen ({frec_v})**")
    st.dataframe(
        df_vt.style.format({
            'Volumen': '{:,.2f}' if unit_v == "Toneladas (Tn)" else '{:,.0f}',
            'Facturacion': 'S/ {:,.2f}',
            'Kilos': '{:,.0f} kg',
            'Jabas': '{:,.0f}',
            'Precio_Ponderado': 'S/ {:,.2f} /kg'
        }),
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------------------------------------------
# PESTAÑA 2: CURVAS DE PRECIOS PONDERADOS
# ------------------------------------------------------------------------------
with tab_precios:
    st.subheader("Curvas de Precios Ponderados (S//kg)")

    df_p_m = df.groupby('MES').agg(
        Facturacion=('VENTA_SOLES', 'sum'),
        Kilos=('TOTAL_KG', 'sum'),
        Toneladas=('TONELADAS', 'sum')
    ).reset_index()
    df_p_m['Precio_Ponderado'] = df_p_m['Facturacion'] / df_p_m['Kilos']

    df_p_s = df.groupby('SEMANA').agg(
        Facturacion=('VENTA_SOLES', 'sum'),
        Kilos=('TOTAL_KG', 'sum'),
        Toneladas=('TONELADAS', 'sum')
    ).reset_index()
    df_p_s['Precio_Ponderado'] = df_p_s['Facturacion'] / df_p_s['Kilos']

    cp1, cp2 = st.columns(2)
    with cp1:
        st.markdown("**1. Curva Mensual: Precio Ponderado (S//kg) vs. Toneladas (Tn)**")
        fig_pm = go.Figure()
        fig_pm.add_trace(go.Bar(
            x=df_p_m['MES'],
            y=df_p_m['Toneladas'],
            name='Volumen (Tn)',
            marker_color='#CBD5E0',
            opacity=0.75
        ))
        fig_pm.add_trace(go.Scatter(
            x=df_p_m['MES'],
            y=df_p_m['Precio_Ponderado'],
            name='Precio Pond. (S//kg)',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='#E53E3E', width=3.5),
            marker=dict(size=8)
        ))
        fig_pm.update_layout(
            yaxis=dict(title="Toneladas (Tn)"),
            yaxis2=dict(title="Precio Promedio Ponderado (S//kg)", overlaying='y', side='right'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_pm, use_container_width=True)

    with cp2:
        st.markdown("**2. Curva Semanal de Precio Ponderado (S//kg)**")
        fig_ps = px.line(
            df_p_s,
            x='SEMANA',
            y='Precio_Ponderado',
            markers=True,
            labels={'SEMANA': 'Semana Nº', 'Precio_Ponderado': 'Precio Ponderado (S//kg)'},
            height=400
        )
        fig_ps.update_traces(line_color='#805AD5', line_width=3)
        fig_ps.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_ps, use_container_width=True)

    st.markdown("**3. Evolución de Precio por Calibre / Producto (S//kg)**")
    df_p_sku = df.groupby(['SEMANA', 'DESCRIPCION_PRODUCTO']).apply(
        lambda g: g['VENTA_SOLES'].sum() / g['TOTAL_KG'].sum()
    ).reset_index(name='Precio_Pond')

    fig_sku_p = px.line(
        df_p_sku,
        x='SEMANA',
        y='Precio_Pond',
        color='DESCRIPCION_PRODUCTO',
        markers=True,
        labels={'SEMANA': 'Semana Nº', 'Precio_Pond': 'Precio (S//kg)', 'DESCRIPCION_PRODUCTO': 'Calibre'},
        height=400
    )
    fig_sku_p.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_sku_p, use_container_width=True)

    st.markdown("**Matriz Mensual de Precios por Calibre (S//kg)**")
    piv_v = df.pivot_table(index='MES', columns='DESCRIPCION_PRODUCTO', values='VENTA_SOLES', aggfunc='sum')
    piv_k = df.pivot_table(index='MES', columns='DESCRIPCION_PRODUCTO', values='TOTAL_KG', aggfunc='sum')
    matriz_p = (piv_v / piv_k).round(2)
    st.dataframe(matriz_p.style.format("S/ {:,.2f}", na_rep="-"), use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA 3: ANÁLISIS DE ÓRDENES DE COMPRA (OCS)
# ------------------------------------------------------------------------------
with tab_ocs:
    st.subheader("Auditoría de Órdenes de Compra (OCs) y Frecuencia")
    co1, co2 = st.columns(2)

    with co1:
        st.markdown("**Cantidad de OCs Emitidas por Mes**")
        df_oc_m = df.groupby('MES').agg(
            OCs_Unicas=('NRO_OC', 'nunique'),
            Lineas=('PRECIO_KG', 'count'),
            Jabas=('UNIDADES_SOLICITADAS', 'sum')
        ).reset_index()
        fig_oc_bar = px.bar(
            df_oc_m,
            x='MES',
            y='OCs_Unicas',
            text='OCs_Unicas',
            labels={'MES': 'Mes', 'OCs_Unicas': 'Cantidad de OCs'},
            color_discrete_sequence=['#3182CE'],
            height=380
        )
        fig_oc_bar.update_traces(textposition='outside')
        fig_oc_bar.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_oc_bar, use_container_width=True)

    with co2:
        st.markdown("**Fuga Logística: Tamaño de Pedido por OC**")
        df_tam = df.groupby('TAMANO_PEDIDO').agg(
            Lineas=('PRECIO_KG', 'count'),
            Jabas=('UNIDADES_SOLICITADAS', 'sum')
        ).reset_index()
        fig_tam_pie = px.pie(
            df_tam,
            names='TAMANO_PEDIDO',
            values='Lineas',
            hole=0.4,
            color='TAMANO_PEDIDO',
            color_discrete_map={
                '1. Crítico (<100 jabas)': '#E53E3E',
                '2. Medio (100-399 jabas)': '#DD6B20',
                '3. Óptimo (>=400 jabas)': '#38A169'
            },
            height=380
        )
        fig_tam_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_tam_pie, use_container_width=True)

    st.markdown("**Dispersión: ¿Bajar precio incrementa las jabas por orden?**")
    fig_scat = px.scatter(
        df,
        x='PRECIO_KG',
        y='UNIDADES_SOLICITADAS',
        color='DESCRIPCION_PRODUCTO',
        size='TONELADAS',
        hover_data=['NRO_OC', 'FECHA_EMISION', 'FORMA_PAGO'],
        labels={'PRECIO_KG': 'Precio Final (S//kg)', 'UNIDADES_SOLICITADAS': 'Jabas en la Orden'},
        height=400
    )
    st.plotly_chart(fig_scat, use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA 4: SIMULADOR DE NEGOCIACIÓN Y DESCUENTOS
# ------------------------------------------------------------------------------
with tab_simulador:
    st.subheader("Calculadora de Negociación para Distribuidor")
    st.info("Simula qué ocurre si el comprador de InRetail te pide descuento y calcula el costo financiero de Z045 (45 días de crédito).")

    s1, s2, s3 = st.columns(3)
    with s1:
        sim_sku = st.selectbox("Calibre / SKU a Cotizar:", options=prods_disp, index=0)
        sim_jabas = st.number_input("Volumen Semanal Ofertado (Jabas):", min_value=10, max_value=25000, value=2400, step=100)
        sim_costo = st.number_input("Costo de Compra en Plaza/Campo (S//kg):", min_value=1.0, max_value=25.0, value=9.50, step=0.10)

    with s2:
        sim_p_cot = st.number_input("Tu Precio Cotizado a InRetail (S//kg):", min_value=1.0, max_value=30.0, value=11.50, step=0.10)
        sim_p_obj = st.number_input("Precio Objetivo / Contraoferta (S//kg):", min_value=1.0, max_value=30.0, value=11.00, step=0.10)
        sim_plazo = st.selectbox("Condición de Pago:", options=[45, 15], index=0, format_func=lambda x: f"Z0{x} ({x} días de crédito)")

    with s3:
        sim_flete = st.number_input("Flete + Estiba a CD 918 (S//kg):", min_value=0.05, max_value=2.0, value=0.28, step=0.02)
        sim_empaque = st.number_input("Empaque / Jaba / Selección (S//kg):", min_value=0.0, max_value=2.0, value=0.15, step=0.02)
        sim_merma = st.slider("Merma / Rechazo en Rampa (%):", 0.0, 10.0, 3.0, 0.5) / 100.0
        sim_tasa = st.slider("Tasa Anual Financiamiento (%):", 5.0, 35.0, 18.0, 1.0) / 100.0

    kilos_s = sim_jabas * 18
    costo_fruta_aj = sim_costo / (1.0 - sim_merma)
    financ_cot = sim_p_cot * (sim_tasa / 360.0) * sim_plazo
    financ_obj = sim_p_obj * (sim_tasa / 360.0) * sim_plazo

    costo_tot_cot = costo_fruta_aj + sim_flete + sim_empaque + financ_cot
    costo_tot_obj = costo_fruta_aj + sim_flete + sim_empaque + financ_obj

    margen_cot = sim_p_cot - costo_tot_cot
    margen_obj = sim_p_obj - costo_tot_obj

    utilidad_cot = kilos_s * margen_cot
    utilidad_obj = kilos_s * margen_obj

    st.divider()
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Costo Real CD (+Financ. Z045)", f"S/ {costo_tot_obj:.2f} /kg", f"Financiamiento: S/ {financ_obj:.2f}/kg")
    r2.metric("Margen Neto (Tu Cotización)", f"S/ {margen_cot:.2f} /kg", f"Utilidad: S/ {utilidad_cot:,.0f}")
    r3.metric("Margen Neto (Precio Comprador)", f"S/ {margen_obj:.2f} /kg", f"{margen_obj - margen_cot:+.2f} S//kg")

    if margen_obj <= 0:
        r4.metric("Jabas Necesarias", "VENTA A PÉRDIDA", "Rechazar descuento", delta_color="inverse")
        st.error(f"🚨 **ALERTA CRÍTICA:** A S/ {sim_p_obj:.2f}/kg vendes a pérdida (pierdes S/ {abs(margen_obj):.2f}/kg). Tu punto de equilibrio mínimo es **S/ {costo_tot_obj:.2f}/kg**.")
    else:
        jabas_req = (utilidad_cot / margen_obj) / 18.0
        inc_req = ((jabas_req - sim_jabas) / sim_jabas) * 100
        r4.metric("Jabas Exigidas para Empatar", f"{jabas_req:,.0f} jabas", f"+{inc_req:.1f}% volumen adicional")
        st.success(f"💡 **ARGUMENTO DE NEGOCIACIÓN:** Si aceptas bajar de S/ {sim_p_cot:.2f} a S/ {sim_p_obj:.2f}, tu ganancia semanal cae en **S/ {utilidad_cot - utilidad_obj:,.2f}**. Para mantener tu utilidad, exige al comprador un compromiso de **{jabas_req:,.0f} jabas** (+{jabas_req - sim_jabas:,.0f} jabas).")

# ------------------------------------------------------------------------------
# PESTAÑA 5: DATOS FILTRADOS Y EXPORTACIÓN
# ------------------------------------------------------------------------------
with tab_datos:
    st.subheader("Visualizador de Datos")
    cols_mostrar = [
        'NRO_OC', 'FECHA_EMISION', 'FECHA_ENTREGA', 'MES', 'SEMANA',
        'DESCRIPCION_PRODUCTO', 'UNIDADES_SOLICITADAS', 'TOTAL_KG', 'TONELADAS',
        'PRECIO_KG', 'VENTA_SOLES', 'FORMA_PAGO', 'TAMANO_PEDIDO'
    ]
    cols_existentes = [c for c in cols_mostrar if c in df.columns]

    st.dataframe(
        df[cols_existentes].sort_values('FECHA_EMISION_DT', ascending=False).style.format({
            'UNIDADES_SOLICITADAS': '{:,.0f}',
            'TOTAL_KG': '{:,.0f} kg',
            'TONELADAS': '{:,.2f} Tn',
            'PRECIO_KG': 'S/ {:,.2f}',
            'VENTA_SOLES': 'S/ {:,.2f}'
        }),
        use_container_width=True,
        hide_index=True
    )

    csv_bytes = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Base Filtrada en CSV",
        data=csv_bytes,
        file_name=f"ordenes_inretail_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
