import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import msal
import os
import unicodedata
from urllib.parse import urlparse
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="KCO Group | Commercial BI",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- NOMBRES DE LISTAS EN SHAREPOINT / MICROSOFT LISTS ---
LIST_FACT_PALTAS    = "factPaltas"
LIST_DIM_PRODUCTOS  = "dimProductos"
LIST_DIM_CLIENTE    = "dimCliente"
LIST_DIM_PROVEEDOR  = "dimProveedor"
LIST_FACT_GASTOS    = "factGastos"
LIST_FACT_ADELANTOS = "factAdelantos"

# --- PALETA CORPORATIVA PREMIUM ---
COLOR_PRIMARY = "#0f3a28"
COLOR_BARRA_CLARA = "#34d399"
COLOR_BARRA_BORDE = "#059669"
COLOR_ACCENT = "#f59e0b"
COLOR_NEUTRAL = "#0f172a"
COLOR_INFO = "#2563eb"
COLOR_MERCADO = "#64748b"
COLOR_DANGER = "#dc2626"

VARIEDAD_COLORS = {
    'PALTA FUERTE A': '#0f3a28',
    'PALTA FUERTE V': '#2563eb',
    'PALTA FUERTE P': '#f59e0b',
    'PALTA FUERTE C': '#7c3aed',
    'PALTA M':        '#10b981',
    '250':            '#0f3a28',
    '280':            '#2563eb',
    '220':            '#f59e0b',
    '200':            '#7c3aed',
    '150':            '#10b981'
}

MESES_DICT = {
    1: '01 - Enero', 2: '02 - Febrero', 3: '03 - Marzo', 4: '04 - Abril',
    5: '05 - Mayo', 6: '06 - Junio', 7: '07 - Julio', 8: '08 - Agosto',
    9: '09 - Setiembre', 10: '10 - Octubre', 11: '11 - Noviembre', 12: '12 - Diciembre'
}

# Índice estacional promedio de demanda en Lima Metropolitana (2024–2026, Base Mayo = 100)
INDICE_ESTACIONAL_LIMA = {
    1: 47.3, 2: 64.7, 3: 86.0, 4: 96.3, 5: 100.0, 6: 91.3,
    7: 73.3, 8: 56.7, 9: 45.3, 10: 32.3, 11: 29.3, 12: 42.7
}

# --- ESTILOS CSS UI/UX PREMIUM ---
st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 0px !important;
        z-index: 99 !important;
    }}
    .main {{ 
        background-color: #f8fafc; 
    }}
    .block-container {{
        max-width: 100% !important;
        padding-top: 0.2rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }}

    /* --- SIDEBAR COMPACTO Y BIEN DISTRIBUIDO --- */
    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 0.5rem !important;
    }}
    div[data-testid="stSidebarHeader"] {{
        height: 1.8rem !important;
        padding: 0.2rem 0.6rem !important;
        margin-bottom: -0.4rem !important;
    }}
    section[data-testid="stSidebarUserContent"] {{
        padding-top: 0.2rem !important;
        padding-bottom: 0.8rem !important;
    }}
    section[data-testid="stSidebar"] h3 {{
        margin: 0 0 0.4rem 0 !important;
        padding: 0 !important;
        font-size: 16px !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {{
        gap: 0.5rem !important;
    }}
    section[data-testid="stSidebar"] hr {{
        margin: 0.35rem 0 !important;
    }}

    /* TÍTULOS DE SEGMENTACIÓN */
    .sb-label {{
        font-size: 11.5px;
        font-weight: 700;
        color: #334155;
        margin-top: 4px;
        margin-bottom: 3px;
        display: block;
    }}
    section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] {{
        margin-bottom: 3px !important;
        min-height: 0px !important;
    }}
    section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p {{
        font-size: 11.5px !important;
        font-weight: 700 !important;
        color: #334155 !important;
    }}

    /* INDENTACIÓN Y ANCHO UNIFICADO DE TODOS LOS CUADROS DE VALORES */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
    section[data-testid="stSidebar"] div[data-testid="stPopover"],
    section[data-testid="stSidebar"] div[data-testid="stDateInput"],
    section[data-testid="stSidebar"] div[data-testid="stCheckbox"] {{
        margin-left: 16px !important;
        width: calc(100% - 22px) !important;
    }}

    /* REDUCIR ALTURA (SLIM) Y UNIFICAR ESTILO DE POPOVERS Y SELECTBOX */
    section[data-testid="stSidebar"] button[data-testid="stPopoverButton"] {{
        width: 100% !important;
        min-height: 30px !important;
        height: 30px !important;
        padding: 2px 10px !important;
        justify-content: space-between !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-left: 3px solid {COLOR_PRIMARY} !important;
        font-weight: 600 !important;
        font-size: 11.5px !important;
        color: #0f172a !important;
        border-radius: 5px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }}
    section[data-testid="stSidebar"] button[data-testid="stPopoverButton"] p {{
        font-size: 11.5px !important;
        line-height: 1.1 !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
        min-height: 30px !important;
        height: 30px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-left: 3px solid {COLOR_PRIMARY} !important;
        border-radius: 5px !important;
        font-size: 11.5px !important;
        font-weight: 600 !important;
        color: #0f172a !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div {{
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }}

    /* CHECKBOX "TODO EL RANGO DEL AÑO" EN UNA SOLA FILA */
    section[data-testid="stSidebar"] label[data-testid="stCheckbox"] {{
        min-height: 22px !important;
        padding-top: 2px !important;
    }}
    section[data-testid="stSidebar"] label[data-testid="stCheckbox"] p {{
        font-size: 11px !important;
        white-space: nowrap !important;
        line-height: 1.2 !important;
    }}

    /* NAVEGACIÓN SUPERIOR Y RADIO BUTTONS EN SIDEBAR */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {{
        background: #e2e8f0;
        padding: 3px;
        border-radius: 6px;
        gap: 3px;
    }}
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label {{
        background: transparent;
        padding: 4px 8px !important;
        border-radius: 5px;
        font-weight: 700;
        font-size: 11.5px !important;
        cursor: pointer;
        margin: 0 !important;
        width: 100%;
    }}
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label[data-checked="true"] {{
        background: {COLOR_PRIMARY} !important;
        color: #ffffff !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.15);
    }}
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div > label[data-checked="true"] p {{
        color: #ffffff !important;
    }}

    /* Indentar únicamente el radio de "Agrupación Temporal" */
    section[data-testid="stSidebar"] div[data-testid="stRadio"][aria-label*="Agrupación"] > div {{
        margin-left: 16px !important;
        width: calc(100% - 22px) !important;
    }}

    /* BOTÓN SEMIOOCULTO CON LETRA MÁS PEQUEÑA PARA MODO PRESENTACIÓN */
    section[data-testid="stSidebar"] div[data-testid="stToggle"] {{
        opacity: 0.30;
        transition: opacity 0.25s ease;
        margin-top: 8px;
    }}
    section[data-testid="stSidebar"] div[data-testid="stToggle"]:hover {{
        opacity: 0.95;
    }}
    section[data-testid="stSidebar"] div[data-testid="stToggle"] p {{
        font-size: 9.5px !important;
        color: #64748b !important;
        white-space: nowrap !important;
    }}

    /* COMPACTAR INTERLINEADO INTERNO DE LOS POPOVERS */
    div[data-testid="stPopoverBody"] {{
        padding: 8px 10px !important;
        min-width: 215px !important;
    }}
    div[data-testid="stPopoverBody"] div[data-testid="stVerticalBlock"] {{
        gap: 0.15rem !important;
    }}
    div[data-testid="stPopoverBody"] label[data-testid="stCheckbox"] {{
        padding-top: 1px !important;
        padding-bottom: 1px !important;
        min-height: 22px !important;
    }}
    div[data-testid="stPopoverBody"] label[data-testid="stCheckbox"] p {{
        font-size: 12px !important;
        line-height: 1.2 !important;
    }}
    div[data-testid="stPopoverBody"] button {{
        padding: 2px 7px !important;
        min-height: 24px !important;
        height: 24px !important;
        font-size: 11.5px !important;
        border-radius: 4px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #f8fafc !important;
    }}
    div[data-testid="stPopoverBody"] button:hover {{
        background-color: #e2e8f0 !important;
    }}

    /* BARRA SUPERIOR CON MARGEN DERECHO AMPLIADO PARA EVITAR ICONOS DE GITHUB/SHARE */
    .header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 6px;
        margin-left: 36px;
        margin-right: 265px;
        margin-bottom: 6px;
    }}
    .header-title {{
        font-size: 16.5px;
        font-weight: 800;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 6px;
        white-space: nowrap;
        letter-spacing: -0.3px;
    }}
    .header-meta {{
        color: #64748b;
        font-size: 10.5px;
        text-align: right;
        white-space: nowrap;
        line-height: 1.2;
    }}
    
    .chart-header {{
        font-size: 12px;
        font-weight: 700;
        color: #1e293b;
        margin-top: 3px;
        margin-bottom: 2px;
        display: flex;
        align-items: center;
        gap: 5px;
    }}

    /* TARJETAS KPI DE ALTO IMPACTO */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
        margin-bottom: 8px;
        width: 100%;
    }}
    .kpi-card {{
        background: #ffffff;
        border-radius: 9px;
        padding: 8px 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2e8f0;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.08);
    }}
    .kpi-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2px;
    }}
    .kpi-title {{
        font-size: 9.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #475569;
    }}
    .kpi-badge {{
        font-size: 11px;
        padding: 2px 6px;
        border-radius: 6px;
        font-weight: 600;
    }}
    .kpi-value {{
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.6px;
        line-height: 1.15;
    }}
    .kpi-sub {{
        font-size: 9px;
        font-weight: 600;
        margin-top: 2px;
        display: flex;
        align-items: center;
        gap: 4px;
    }}

    /* VARIANTES DE TARJETAS */
    .kpi-volumen {{
        background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
        border-top: 3.5px solid #10b981;
    }}
    .kpi-volumen .kpi-badge {{ background: #dcfce7; color: #15803d; }}
    .kpi-volumen .kpi-sub {{ color: #16a34a; }}

    .kpi-venta {{
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
        border-top: 3.5px solid #3b82f6;
    }}
    .kpi-venta .kpi-badge {{ background: #dbeafe; color: #1d4ed8; }}
    .kpi-venta .kpi-sub {{ color: #2563eb; }}

    .kpi-precio {{
        background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%);
        border-top: 3.5px solid #f59e0b;
    }}
    .kpi-precio .kpi-badge {{ background: #fef3c7; color: #b45309; }}
    .kpi-precio .kpi-sub {{ color: #d97706; }}

    .kpi-ordenes {{
        background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%);
        border-top: 3.5px solid #8b5cf6;
    }}
    .kpi-ordenes .kpi-badge {{ background: #f3e8ff; color: #6d28d9; }}
    .kpi-ordenes .kpi-sub {{ color: #7c3aed; }}

    .kpi-jabas {{
        background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
        border-top: 3.5px solid #059669;
    }}
    .kpi-jabas .kpi-badge {{ background: #d1fae5; color: #047857; }}
    .kpi-jabas .kpi-sub {{ color: #059669; }}

    .kpi-danger {{
        background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
        border-top: 3.5px solid #dc2626;
    }}
    .kpi-danger .kpi-badge {{ background: #fee2e2; color: #b91c1c; }}
    .kpi-danger .kpi-sub {{ color: #dc2626; }}

    /* INSIGHT CARDS EJECUTIVOS */
    .chart-insight {{
        background-color: #ffffff;
        border-left: 4px solid #059669;
        border-right: 1px solid #e2e8f0;
        border-top: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        padding: 9px 13px;
        border-radius: 7px;
        font-size: 11.5px;
        color: #334155;
        margin-top: 6px;
        margin-bottom: 10px;
        line-height: 1.45;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }}
    .insight-title {{
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 3px;
        display: flex;
        align-items: center;
        gap: 6px;
    }}

    .drilldown-bar {{
        background: #e0f2fe;
        border-left: 3.5px solid #0284c7;
        padding: 5px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        color: #0369a1;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
    }}
    </style>
""", unsafe_allow_html=True)

PLOTLY_CONFIG = {
    'displayModeBar': False,
    'responsive': True
}

if 'drilldown_mes' not in st.session_state:
    st.session_state.drilldown_mes = None
if 'semana_seleccionada' not in st.session_state:
    st.session_state.semana_seleccionada = None

DEFAULT_KG_PER_JABA = 18.0

def normalize_text(val):
    if pd.isna(val):
        return ""
    s = str(val).strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def clean_id_str(val):
    """Normaliza IDs numéricos/texto de SharePoint (ej. 250.0 -> '250', 1 -> '1')."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

def find_col(df, candidates):
    """Busca una columna en el DataFrame ignorando mayúsculas, tildes, espacios y sufijos LookupId."""
    if df.empty:
        return None
    norm_map = {normalize_text(c).replace(" ", ""): c for c in df.columns}
    for cand in candidates:
        key = normalize_text(cand).replace(" ", "")
        if key in norm_map:
            return norm_map[key]
        if (key + "lookupid") in norm_map:
            return norm_map[key + "lookupid"]
    return None

def style_semaphore(val):
    if pd.isna(val):
        return ''
    if val > 2.0:
        return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
    elif val < -2.0:
        return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
    else:
        return 'background-color: #fef9c3; color: #854d0e; font-weight: bold;'

def style_margin_pct(val):
    if pd.isna(val):
        return ''
    if val >= 20.0:
        return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
    elif val < 10.0:
        return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
    else:
        return 'background-color: #fef9c3; color: #854d0e; font-weight: bold;'

# --- CONEXIÓN A MICROSOFT GRAPH API (MISMO ESQUEMA [sharepoint] QUE control-asistencia-kco) ---
def get_graph_token():
    sp = st.secrets["sharepoint"]
    authority = f"https://login.microsoftonline.com/{sp['tenant_id']}"
    app = msal.ConfidentialClientApplication(
        sp["client_id"],
        authority=authority,
        client_credential=sp["client_secret"]
    )
    result = app.acquire_token_silent(["https://graph.microsoft.com/.default"], account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"Error de autenticación Azure AD: {result.get('error_description', result)}")
    return result["access_token"]

def get_sharepoint_site_id(headers):
    sp = st.secrets["sharepoint"]
    parsed = urlparse(sp["site_url"].rstrip("/"))
    site_host = parsed.netloc
    site_path = parsed.path
    url = f"https://graph.microsoft.com/v1.0/sites/{site_host}:{site_path}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]

def fetch_ms_list_df(headers, site_id, list_name, optional=False):
    """
    Lee una lista de SharePoint/Microsoft Lists resolviendo automáticamente
    el mapa displayName -> internalName vía /columns, incluyendo columnas LookupId.
    """
    try:
        cols_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}/columns"
        cols_resp = requests.get(cols_url, headers=headers, timeout=30)
        cols_resp.raise_for_status()
        internal_to_display = {}
        for col in cols_resp.json().get("value", []):
            int_name = col.get("name")
            disp_name = col.get("displayName")
            if int_name and disp_name:
                clean_disp = disp_name.strip()
                internal_to_display[int_name] = clean_disp
                internal_to_display[f"{int_name}LookupId"] = clean_disp

        items_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}/items?expand=fields&$top=500"
        rows = []
        while items_url:
            resp = requests.get(items_url, headers=headers, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            for item in payload.get("value", []):
                fields = item.get("fields", {})
                mapped_row = {"_SP_ITEM_ID": clean_id_str(item.get("id"))}
                for k, v in fields.items():
                    col_label = internal_to_display.get(k, k)
                    if isinstance(v, dict):
                        v = v.get("LookupValue") or v.get("Title") or v.get("Value") or str(v)
                    mapped_row[col_label] = v
                rows.append(mapped_row)
            items_url = payload.get("@odata.nextLink")

        df_out = pd.DataFrame(rows)
        if not df_out.empty:
            df_out = df_out.loc[:, ~df_out.columns.duplicated()]
        return df_out
    except Exception:
        if optional:
            return pd.DataFrame()
        raise

# --- CARGA Y TRANSFORMACIÓN DESDE MICROSOFT LISTS + REPORTE MAYORISTA ---
@st.cache_data(ttl=300)
def load_all_data():
    token = get_graph_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    site_id = get_sharepoint_site_id(headers)

    # Descargar tablas de hechos y dimensiones desde Microsoft Lists
    df_fact     = fetch_ms_list_df(headers, site_id, LIST_FACT_PALTAS)
    df_dim_prod = fetch_ms_list_df(headers, site_id, LIST_DIM_PRODUCTOS)
    df_dim_cli  = fetch_ms_list_df(headers, site_id, LIST_DIM_CLIENTE, optional=True)
    df_dim_prov = fetch_ms_list_df(headers, site_id, LIST_DIM_PROVEEDOR, optional=True)
    df_gastos   = fetch_ms_list_df(headers, site_id, LIST_FACT_GASTOS, optional=True)

    if df_fact.empty:
        raise ValueError(f"La lista '{LIST_FACT_PALTAS}' no devolvió registros.")

    # Detección flexible de columnas en factPaltas
    col_tipo       = find_col(df_fact, ['Tipo'])
    col_cod_prod   = find_col(df_fact, ['CodProducto', 'Cod Producto', 'Producto'])
    col_fecha      = find_col(df_fact, ['Fecha', 'Fecha Emision'])
    col_cant       = find_col(df_fact, ['Cantidad Total', 'CantidadTotal'])
    col_precio     = find_col(df_fact, ['Precio OC', 'PrecioOC'])
    col_costo_prov = find_col(df_fact, ['Costo Proveedor', 'CostoProveedor'])
    col_costo_dev  = find_col(df_fact, ['Costo Proveedor (DEV)', 'Costo Proveedor DEV', 'CostoProveedorDEV'])
    col_jabas_real = find_col(df_fact, ['Jabas'])
    col_peso_jaba  = find_col(df_fact, ['PesoJabaKg', 'Peso Jaba Kg'])
    col_oc         = find_col(df_fact, ['OC', 'Nro OC'])
    col_cliente    = find_col(df_fact, ['Cliente'])
    col_proveedor  = find_col(df_fact, ['Proveedor'])

    faltantes = [
        nombre for nombre, col in [
            ('CodProducto', col_cod_prod),
            ('Fecha', col_fecha),
            ('Cantidad Total', col_cant),
            ('Precio OC', col_precio)
        ] if col is None
    ]
    if faltantes:
        raise KeyError(
            f"No se encontraron las columnas {faltantes} en '{LIST_FACT_PALTAS}'. "
            f"Columnas disponibles detectadas: {list(df_fact.columns)}"
        )

    # Normalizar tipo de operación: 'compra/venta' vs 'devolucion'
    if col_tipo:
        df_fact['TIPO_NORM'] = df_fact[col_tipo].apply(normalize_text)
    else:
        df_fact['TIPO_NORM'] = 'compra/venta'

    # 1. RESOLUCIÓN DE LOOKUP: CodProducto -> dimProductos
    raw_prod_lookup = df_fact[col_cod_prod].apply(clean_id_str)
    if not df_dim_prod.empty:
        col_dim_pk   = find_col(df_dim_prod, ['COD_PRODUCTO', 'CodProducto', 'Title'])
        col_dim_desc = find_col(df_dim_prod, ['DESCRIPCIÓN', 'DESCRIPCION', 'Descripcion'])

        if col_dim_pk:
            df_dim_prod['COD_KEY'] = df_dim_prod[col_dim_pk].apply(clean_id_str)
            map_id_to_cod = dict(zip(df_dim_prod['_SP_ITEM_ID'], df_dim_prod['COD_KEY']))
            df_fact['COD_KEY'] = raw_prod_lookup.apply(
                lambda x: x if x in set(df_dim_prod['COD_KEY']) else map_id_to_cod.get(x, x)
            )
            if col_dim_desc:
                map_desc = dict(zip(df_dim_prod['COD_KEY'], df_dim_prod[col_dim_desc].astype(str).str.strip()))
                df_fact['DESCRIPCION_PRODUCTO'] = df_fact['COD_KEY'].map(map_desc).fillna(df_fact['COD_KEY'])
            else:
                df_fact['DESCRIPCION_PRODUCTO'] = df_fact['COD_KEY']
        else:
            df_fact['COD_KEY'] = raw_prod_lookup
            df_fact['DESCRIPCION_PRODUCTO'] = df_fact['COD_KEY']
    else:
        df_fact['COD_KEY'] = raw_prod_lookup
        df_fact['DESCRIPCION_PRODUCTO'] = df_fact['COD_KEY']

    cod_num = pd.to_numeric(df_fact['COD_KEY'], errors='coerce')
    df_fact['PESO_FRUTO_KG'] = np.where(cod_num > 0, cod_num / 1000.0, np.nan)

    # 2. RESOLUCIÓN DE LOOKUP: Cliente -> dimCliente
    if col_cliente:
        raw_cli_lookup = df_fact[col_cliente].apply(clean_id_str)
        if not df_dim_cli.empty:
            col_cli_rs = find_col(df_dim_cli, ['RAZON_SOCIAL', 'Razon Social', 'Title', 'Cliente'])
            if col_cli_rs:
                df_dim_cli['CLI_NAME'] = df_dim_cli[col_cli_rs].fillna('').astype(str).str.strip()
                map_id_to_cli = dict(zip(df_dim_cli['_SP_ITEM_ID'], df_dim_cli['CLI_NAME']))
                df_fact['CLIENTE'] = raw_cli_lookup.apply(
                    lambda x: x if x in set(df_dim_cli['CLI_NAME']) else map_id_to_cli.get(x, x)
                )
            else:
                df_fact['CLIENTE'] = raw_cli_lookup
        else:
            df_fact['CLIENTE'] = raw_cli_lookup
    else:
        df_fact['CLIENTE'] = ''

    # 3. RESOLUCIÓN DE LOOKUP: Proveedor -> dimProveedor (+ Provincia)
    if col_proveedor:
        raw_prov_lookup = df_fact[col_proveedor].apply(clean_id_str)
        if not df_dim_prov.empty:
            col_prov_rs   = find_col(df_dim_prov, ['RAZON_SOCIAL', 'Razon Social', 'Title', 'Proveedor'])
            col_prov_zona = find_col(df_dim_prov, ['PROVINCIA', 'Provincia'])
            if col_prov_rs:
                df_dim_prov['PROV_NAME'] = df_dim_prov[col_prov_rs].fillna('').astype(str).str.strip()
                map_id_to_prov = dict(zip(df_dim_prov['_SP_ITEM_ID'], df_dim_prov['PROV_NAME']))
                df_fact['PROVEEDOR'] = raw_prov_lookup.apply(
                    lambda x: x if x in set(df_dim_prov['PROV_NAME']) else map_id_to_prov.get(x, x)
                )
                if col_prov_zona:
                    map_prov_zona = dict(zip(df_dim_prov['PROV_NAME'], df_dim_prov[col_prov_zona].fillna('').astype(str).str.strip()))
                    df_fact['PROVINCIA_PROV'] = df_fact['PROVEEDOR'].map(map_prov_zona).fillna('')
                else:
                    df_fact['PROVINCIA_PROV'] = ''
            else:
                df_fact['PROVEEDOR'] = raw_prov_lookup
                df_fact['PROVINCIA_PROV'] = ''
        else:
            df_fact['PROVEEDOR'] = raw_prov_lookup
            df_fact['PROVINCIA_PROV'] = ''
    else:
        df_fact['PROVEEDOR'] = ''
        df_fact['PROVINCIA_PROV'] = ''

    # 4. MAPEO DE FECHAS Y CAMPOS NUMÉRICOS
    df_fact['FECHA_EMISION'] = pd.to_datetime(df_fact[col_fecha], errors='coerce')
    if df_fact['FECHA_EMISION'].dt.tz is not None:
        df_fact['FECHA_EMISION'] = df_fact['FECHA_EMISION'].dt.tz_convert(None)

    df_fact = df_fact.dropna(subset=['FECHA_EMISION']).copy()
    df_fact['AÑO'] = df_fact['FECHA_EMISION'].dt.year
    df_fact['MES_NUM'] = df_fact['FECHA_EMISION'].dt.month
    df_fact['MES_AÑO'] = df_fact['FECHA_EMISION'].dt.strftime('%Y-%m')
    df_fact['SEMANA_AÑO'] = df_fact['FECHA_EMISION'].dt.strftime('%Y-W%V')

    df_fact['KILOS_SOLICITADOS'] = pd.to_numeric(df_fact[col_cant], errors='coerce').fillna(0)
    df_fact['PRECIO_KG'] = pd.to_numeric(df_fact[col_precio], errors='coerce').fillna(0)
    df_fact['COSTO_PROV_UNIT'] = pd.to_numeric(df_fact[col_costo_prov], errors='coerce').fillna(0) if col_costo_prov else 0.0
    df_fact['COSTO_DEV_UNIT'] = pd.to_numeric(df_fact[col_costo_dev], errors='coerce').fillna(0) if col_costo_dev else 0.0

    # Peso por jaba y conteo de jabas (usa Jabas real si existe, si no Cantidad Total / PesoJabaKg)
    if col_peso_jaba:
        peso_jaba_serie = pd.to_numeric(df_fact[col_peso_jaba], errors='coerce')
        df_fact['PESO_JABA_EFECTIVO'] = np.where(peso_jaba_serie > 0, peso_jaba_serie, DEFAULT_KG_PER_JABA)
    else:
        df_fact['PESO_JABA_EFECTIVO'] = DEFAULT_KG_PER_JABA

    jabas_calc = df_fact['KILOS_SOLICITADOS'] / df_fact['PESO_JABA_EFECTIVO']
    if col_jabas_real:
        jabas_list = pd.to_numeric(df_fact[col_jabas_real], errors='coerce')
        df_fact['JABAS_EST'] = np.where(jabas_list > 0, jabas_list, jabas_calc)
    else:
        df_fact['JABAS_EST'] = jabas_calc

    df_fact['FRUTOS_EST'] = np.where(df_fact['PESO_FRUTO_KG'].notna(), df_fact['KILOS_SOLICITADOS'] / df_fact['PESO_FRUTO_KG'], 0)
    df_fact['PRECIO_FRUTO_EST'] = df_fact['PRECIO_KG'] * df_fact['PESO_FRUTO_KG']
    df_fact['NRO_OC'] = df_fact[col_oc].fillna('').astype(str).str.strip() if col_oc else ''

    # Cálculos diferenciados por tipo de operación:
    # - compra/venta: venta = Cantidad Total * Precio OC; costo = Cantidad Total * Costo Proveedor
    # - devolucion: impacto = Cantidad Total * Costo Proveedor (DEV)
    es_dev = df_fact['TIPO_NORM'].str.contains('devolucion', na=False)
    df_fact['ES_DEVOLUCION'] = es_dev
    df_fact['VALOR_COMERCIAL'] = np.where(~es_dev, df_fact['KILOS_SOLICITADOS'] * df_fact['PRECIO_KG'], 0.0)
    df_fact['INVERSION_COMPRA'] = np.where(~es_dev, df_fact['KILOS_SOLICITADOS'] * df_fact['COSTO_PROV_UNIT'], 0.0)
    df_fact['COSTO_DEVOLUCION'] = np.where(es_dev, df_fact['KILOS_SOLICITADOS'] * df_fact['COSTO_DEV_UNIT'], 0.0)

    # 5. PROCESAMIENTO DE factGastos (Fecha, TipoGasto, Descripción, Monto)
    df_gastos_clean = pd.DataFrame(columns=['FECHA_GASTO', 'AÑO', 'MES_NUM', 'MES_AÑO', 'SEMANA_AÑO', 'TIPO_GASTO', 'DESCRIPCION', 'MONTO'])
    if not df_gastos.empty:
        col_g_fecha = find_col(df_gastos, ['Fecha'])
        col_g_tipo  = find_col(df_gastos, ['TipoGasto', 'Tipo Gasto'])
        col_g_desc  = find_col(df_gastos, ['Descripción', 'Descripcion', 'Title'])
        col_g_monto = find_col(df_gastos, ['Monto'])
        if col_g_fecha and col_g_monto:
            df_g = df_gastos.copy()
            df_g['FECHA_GASTO'] = pd.to_datetime(df_g[col_g_fecha], errors='coerce')
            if df_g['FECHA_GASTO'].dt.tz is not None:
                df_g['FECHA_GASTO'] = df_g['FECHA_GASTO'].dt.tz_convert(None)
            df_g = df_g.dropna(subset=['FECHA_GASTO']).copy()
            df_g['AÑO'] = df_g['FECHA_GASTO'].dt.year
            df_g['MES_NUM'] = df_g['FECHA_GASTO'].dt.month
            df_g['MES_AÑO'] = df_g['FECHA_GASTO'].dt.strftime('%Y-%m')
            df_g['SEMANA_AÑO'] = df_g['FECHA_GASTO'].dt.strftime('%Y-W%V')
            df_g['TIPO_GASTO'] = df_g[col_g_tipo].fillna('General').astype(str).str.strip() if col_g_tipo else 'General'
            df_g['DESCRIPCION'] = df_g[col_g_desc].fillna('').astype(str).str.strip() if col_g_desc else ''
            df_g['MONTO'] = pd.to_numeric(df_g[col_g_monto], errors='coerce').fillna(0.0)
            df_gastos_clean = df_g[['FECHA_GASTO', 'AÑO', 'MES_NUM', 'MES_AÑO', 'SEMANA_AÑO', 'TIPO_GASTO', 'DESCRIPCION', 'MONTO']].copy()

    # 6. CARGA DE PRECIOS MAYORISTAS LOCALES (reporte_fuerte.xls)
    df_mercado = pd.DataFrame()
    mkt_file = "reporte_fuerte.xls"
    if os.path.exists(mkt_file):
        try:
            try:
                df_m = pd.read_excel(mkt_file, engine='xlrd')
            except Exception:
                try:
                    df_m = pd.read_excel(mkt_file, engine='calamine')
                except Exception:
                    df_m = pd.read_excel(mkt_file, engine='openpyxl')
            df_m['Fecha'] = pd.to_datetime(df_m['Fecha'], errors='coerce')
            df_m = df_m.dropna(subset=['Fecha', 'Palta Fuerte']).sort_values('Fecha')
            df_m['MES_AÑO'] = df_m['Fecha'].dt.strftime('%Y-%m')
            df_m['SEMANA_AÑO'] = df_m['Fecha'].dt.strftime('%Y-W%V')
            df_mercado = df_m
        except Exception:
            df_mercado = pd.DataFrame()

    timestamp_actualizacion = datetime.now().strftime("%d/%m/%Y %H:%M")
    return df_fact, df_gastos_clean, df_mercado, timestamp_actualizacion

try:
    df_all_raw, df_gastos_raw, df_mercado_raw, update_time = load_all_data()
except Exception as e:
    st.error(f"Error conectando con Microsoft Lists / SharePoint: {e}")
    st.stop()

# --- SIDEBAR: NAVEGACIÓN, PANTALLA COMPLETA, SLICERS UNIFICADOS Y MODO PRIVACIDAD ---
with st.sidebar:
    sb_top1, sb_top2 = st.columns([4.2, 1])
    with sb_top1:
        st.markdown("### 🥑 Control BI")
    with sb_top2:
        components.html("""
            <div style="display: flex; justify-content: flex-end; align-items: center; height: 28px;">
                <button id="fs-btn" onclick="toggleFullScreen()" title="Pantalla Completa" style="
                    background-color: #0f3a28; 
                    color: #ffffff; 
                    border: none; 
                    border-radius: 6px;
                    width: 30px; 
                    height: 26px; 
                    font-size: 13px; 
                    cursor: pointer;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.15); 
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                ">
                    <span id="fs-icon">⛶</span>
                </button>
            </div>
            <script>
                function toggleFullScreen() {
                    var doc = window.parent.document;
                    var btnIcon = document.getElementById("fs-icon");
                    if (!doc.fullscreenElement) {
                        doc.documentElement.requestFullscreen().catch(err => console.log(err));
                        btnIcon.innerText = "🗗";
                    } else {
                        if (doc.exitFullscreen) {
                            doc.exitFullscreen();
                            btnIcon.innerText = "⛶";
                        }
                    }
                }
            </script>
        """, height=30)

    # 0. SELECTOR DE PÁGINAS INTEGRADO EN EL PANEL (4 PÁGINAS)
    vista_activa = st.radio(
        "📑 Navegación",
        options=[
            "📊 Resumen & Evolución",
            "🎯 Benchmark & Previsión",
            "🚛 Logística & Devoluciones",
            "💰 Financiero & Márgenes"
        ],
        label_visibility="collapsed"
    )
    
    st.divider()

    # 1. FILTRO DE AÑO
    años_disponibles = sorted(df_all_raw['AÑO'].dropna().astype(int).unique().tolist(), reverse=True)
    st.markdown('<span class="sb-label">📆 Año Fiscal</span>', unsafe_allow_html=True)
    año_seleccionado = st.selectbox(
        "Año Fiscal",
        options=años_disponibles,
        index=0,
        label_visibility="collapsed"
    )
    
    df_año_all = df_all_raw[df_all_raw['AÑO'] == año_seleccionado]
    
    # 2. SLICER DE MESES
    meses_disp = sorted(df_año_all['MES_NUM'].dropna().astype(int).unique().tolist())
    
    if 'sel_meses' not in st.session_state or st.session_state.get('last_year') != año_seleccionado:
        st.session_state.sel_meses = []
        st.session_state.last_year = año_seleccionado
        st.session_state.drilldown_mes = None
        st.session_state.semana_seleccionada = None

    st.markdown('<span class="sb-label">🗓️ Meses</span>', unsafe_allow_html=True)
    n_meses_sel = len(st.session_state.sel_meses)
    label_meses = "Todos (Sin filtro)" if n_meses_sel == 0 else (
        MESES_DICT.get(st.session_state.sel_meses[0], "") if n_meses_sel == 1 else f"{n_meses_sel} meses sel."
    )
    
    with st.popover(label_meses, use_container_width=True):
        h_m1, h_m2 = st.columns([4, 1.3])
        h_m1.markdown("<span style='font-size:11px; font-weight:700; color:#64748b;'>Seleccionar mes</span>", unsafe_allow_html=True)
        if h_m2.button("🧹", key="btn_clr_meses", help="Borrar selección (Mostrar todos)"):
            st.session_state.sel_meses = []
            for m in meses_disp:
                st.session_state[f"chk_mes_{m}"] = False
            st.rerun()
            
        nuevos_meses = []
        for m in meses_disp:
            checked = st.checkbox(
                MESES_DICT.get(m, f"Mes {m}"),
                value=(m in st.session_state.sel_meses),
                key=f"chk_mes_{m}"
            )
            if checked:
                nuevos_meses.append(m)
        st.session_state.sel_meses = nuevos_meses

    selected_meses = st.session_state.sel_meses if len(st.session_state.sel_meses) > 0 else meses_disp

    # 3. SLICER DE VARIEDAD / CALIBRE
    prods_reales = sorted(df_all_raw['DESCRIPCION_PRODUCTO'].dropna().unique().tolist())
    
    if 'sel_prods' not in st.session_state:
        st.session_state.sel_prods = []

    st.markdown('<span class="sb-label">🏷️ Variedad / Calibre</span>', unsafe_allow_html=True)
    n_prods_sel = len(st.session_state.sel_prods)
    label_prods = "Todas (Sin filtro)" if n_prods_sel == 0 else (
        st.session_state.sel_prods[0] if n_prods_sel == 1 else f"{n_prods_sel} variedades sel."
    )
    
    with st.popover(label_prods, use_container_width=True):
        h_p1, h_p2 = st.columns([4, 1.3])
        h_p1.markdown("<span style='font-size:11px; font-weight:700; color:#64748b;'>Seleccionar calibre</span>", unsafe_allow_html=True)
        if h_p2.button("🧹", key="btn_clr_prods", help="Borrar selección (Mostrar todas)"):
            st.session_state.sel_prods = []
            for p in prods_reales:
                st.session_state[f"chk_prod_{p}"] = False
            st.rerun()
            
        nuevos_prods = []
        for p in prods_reales:
            checked = st.checkbox(
                p,
                value=(p in st.session_state.sel_prods),
                key=f"chk_prod_{p}"
            )
            if checked:
                nuevos_prods.append(p)
        st.session_state.sel_prods = nuevos_prods

    selected_prods = st.session_state.sel_prods if len(st.session_state.sel_prods) > 0 else prods_reales

    # 4. FILTRO TIPO CALENDARIO
    st.markdown('<span class="sb-label">📅 Rango de Fechas</span>', unsafe_allow_html=True)
    min_date_año = df_año_all['FECHA_EMISION'].min().date()
    max_date_año = df_año_all['FECHA_EMISION'].max().date()
    
    ver_todo_rango = st.checkbox("Todo el rango del año", value=True)
    if ver_todo_rango:
        date_range = (min_date_año, max_date_año)
    else:
        date_range = st.date_input(
            "Seleccionar fechas",
            value=(min_date_año, max_date_año),
            min_value=min_date_año,
            max_value=max_date_año,
            label_visibility="collapsed"
        )
    
    # 5. AGRUPACIÓN TEMPORAL BASE
    periodo_seleccionado = st.radio(
        "⏱️ Agrupación Temporal",
        options=["Mensual", "Semanal"],
        horizontal=True
    )

    # 6. BOTÓN SEMIOOCULTO PARA CENSURAR PRECIOS Y MONTOS
    ocultar_precios = st.toggle("👁️‍🗨️ Modo Presentación (Ocultar S/)", value=False)

col_periodo = 'MES_AÑO' if periodo_seleccionado == "Mensual" else 'SEMANA_AÑO'
label_periodo = "Mes" if periodo_seleccionado == "Mensual" else "Semana"

# --- APLICACIÓN DE FILTROS GLOBALES ---
df_all_filtered = df_año_all.copy()
df_all_filtered = df_all_filtered[df_all_filtered['MES_NUM'].isin(selected_meses)]
df_all_filtered = df_all_filtered[df_all_filtered['DESCRIPCION_PRODUCTO'].isin(selected_prods)]

if len(date_range) == 2:
    df_all_filtered = df_all_filtered[
        (df_all_filtered['FECHA_EMISION'].dt.date >= date_range[0]) &
        (df_all_filtered['FECHA_EMISION'].dt.date <= date_range[1])
    ]

# Subconjuntos diferenciados:
# - df: solo compra/venta (mantiene intactas las Páginas 1 y 2)
# - df_dev: solo devoluciones
df = df_all_filtered[~df_all_filtered['ES_DEVOLUCION']].copy()
df_dev = df_all_filtered[df_all_filtered['ES_DEVOLUCION']].copy()

# Filtrar también factGastos con los mismos criterios temporales
df_gastos_filtered = pd.DataFrame(columns=df_gastos_raw.columns)
if not df_gastos_raw.empty:
    df_g_tmp = df_gastos_raw[df_gastos_raw['AÑO'] == año_seleccionado].copy()
    df_g_tmp = df_g_tmp[df_g_tmp['MES_NUM'].isin(selected_meses)]
    if len(date_range) == 2:
        df_g_tmp = df_g_tmp[
            (df_g_tmp['FECHA_GASTO'].dt.date >= date_range[0]) &
            (df_g_tmp['FECHA_GASTO'].dt.date <= date_range[1])
        ]
    df_gastos_filtered = df_g_tmp

if df_all_filtered.empty:
    st.warning("⚠️ No se encontraron registros para la combinación de filtros seleccionada.")
    st.stop()

if periodo_seleccionado == "Semanal":
    st.session_state.drilldown_mes = None

# --- HEADER DESPEJADO ---
st.markdown(f"""
    <div class="header-bar">
        <div class="header-title">
            🥑 KCO Group | Intelligence & Pricing Dashboard ({año_seleccionado})
        </div>
        <div class="header-meta">
            <b>Desarrollado por:</b> Alfredo Huaracha Mendoza &nbsp;|&nbsp; <i>Operations BI</i><br>
            <span style="color: #94a3b8;">🕒 Act: {update_time}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- FRAGMENTO INTERACTIVO PARA TRANSICIÓN FLUIDA ENTRE MESES Y SEMANAS (PÁGINA 1) ---
@st.fragment
def render_evolucion_interactiva(df_base, periodo_sel, año_sel, ocultar_p, col_per, label_per):
    es_vista_mensual = (periodo_sel == "Mensual")
    mes_en_drilldown = st.session_state.drilldown_mes if (es_vista_mensual and st.session_state.drilldown_mes in df_base['MES_AÑO'].unique()) else None
    if es_vista_mensual and not mes_en_drilldown:
        st.session_state.drilldown_mes = None

    if es_vista_mensual and mes_en_drilldown:
        b_c1, b_c2 = st.columns([3.5, 0.8])
        with b_c1:
            st.markdown(f'<div class="drilldown-bar"><span>🔍 Desglose semanal activo del mes: <b>{mes_en_drilldown}</b> (Haz clic en una barra semanal para filtrar la tabla)</span></div>', unsafe_allow_html=True)
        with b_c2:
            if st.button("⬅️ Ver todos los meses", use_container_width=True, type="primary"):
                st.session_state.drilldown_mes = None
                st.session_state.semana_seleccionada = None
                st.rerun(scope="fragment")

    if es_vista_mensual and mes_en_drilldown:
        df_target = df_base[df_base['MES_AÑO'] == mes_en_drilldown].copy()
        col_actual = 'SEMANA_AÑO'
        label_actual = f"Semana de {mes_en_drilldown}"
        sub_titulo = "Volumen (Tn)" if ocultar_p else "Volumen (Tn) vs Precio (S/)"
        titulo_grafico = f"Evolución Semanal de {mes_en_drilldown}: {sub_titulo}"
    else:
        df_target = df_base.copy()
        col_actual = col_per
        label_actual = label_per
        sub_titulo = "Volumen (Tn)" if ocultar_p else "Volumen (Tn) vs Precio Ponderado (S/)"
        titulo_grafico = f"Evolución {periodo_sel} ({año_sel}): {sub_titulo}"

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

    df_detalle_grafico = df_target.copy()
    if periodo_sel == "Semanal" and not mes_en_drilldown:
        if len(df_trend) > 20:
            df_trend = df_trend.tail(20).reset_index(drop=True)
            semanas_visibles = df_trend[col_actual].tolist()
            df_detalle_grafico = df_detalle_grafico[df_detalle_grafico['SEMANA_AÑO'].isin(semanas_visibles)].copy()

    st.markdown(f'<div class="chart-header">📈 {titulo_grafico}</div>', unsafe_allow_html=True)
    fig_dual = go.Figure()

    tiene_ref_mercado = False
    if es_vista_mensual and not mes_en_drilldown and len(df_trend) > 1:
        df_trend['MES_INT'] = df_trend[col_actual].str.split('-').str[1].astype(int)
        df_trend['INDICE_LIMA'] = df_trend['MES_INT'].map(INDICE_ESTACIONAL_LIMA)
        
        suma_indices = df_trend['INDICE_LIMA'].sum()
        if suma_indices > 0:
            factor_escala = df_trend['TN_TOTALES'].sum() / suma_indices
            df_trend['DEMANDA_REF_TN'] = df_trend['INDICE_LIMA'] * factor_escala
            tiene_ref_mercado = True
            
            fig_dual.add_trace(go.Scatter(
                x=df_trend[col_actual],
                y=df_trend['DEMANDA_REF_TN'],
                name='Tendencia Demanda Lima (2024–2026)',
                mode='lines',
                line=dict(color='rgba(100, 116, 139, 0.25)', width=1.2, shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(148, 163, 184, 0.11)',
                hovertemplate="<b>Ref. Estacional Lima</b><br>Ritmo esperado: %{y:.1f} Tn<br>Índice Mercado: %{customdata:.0f}/100<extra></extra>",
                customdata=df_trend['INDICE_LIMA'],
                yaxis='y'
            ))

    hover_barra = (
        f"<b>{label_actual}: %{{x}}</b><br>Volumen: %{{y:.2f}} Tn (%{{customdata[0]:,.0f}} kg)<br>Órdenes: %{{customdata[1]:,}}<extra></extra>"
        if ocultar_p else
        f"<b>{label_actual}: %{{x}}</b><br>Volumen: %{{y:.2f}} Tn (%{{customdata[0]:,.0f}} kg)<br>Venta: S/ %{{customdata[2]:,.2f}}<extra></extra>"
    )

    fig_dual.add_trace(go.Bar(
        x=df_trend[col_actual],
        y=df_trend['TN_TOTALES'],
        name='Volumen KCO (Tn)',
        marker=dict(color=COLOR_BARRA_CLARA, line=dict(color=COLOR_BARRA_BORDE, width=1.2)),
        text=df_trend['TN_TOTALES'].apply(lambda x: f"<b>{x:,.1f} Tn</b>"),
        textposition='outside',
        cliponaxis=False,
        outsidetextfont=dict(color='#065f46', size=9.5, family="Arial"),
        hovertemplate=hover_barra,
        customdata=np.stack((df_trend['KG_TOTALES'], df_trend['ORDENES'], df_trend['VALOR_TOTAL']), axis=-1),
        yaxis='y'
    ))

    anotaciones_totales = []
    lineas_estaciones = []

    if not ocultar_p:
        fig_dual.add_trace(go.Scatter(
            x=df_trend[col_actual],
            y=df_trend['PRECIO_POND'],
            name='Precio Pond (S/)',
            mode='lines+markers',
            marker=dict(size=7, color=COLOR_ACCENT, line=dict(color="#ffffff", width=1.2)),
            line=dict(width=2.6, color=COLOR_ACCENT),
            hovertemplate=f"<b>{label_actual}: %{{x}}</b><br>Precio Pond: <b>S/ %{{y:.2f}} /kg</b><extra></extra>",
            yaxis='y2'
        ))

        for idx_row, row in df_trend.iterrows():
            p_val = row['PRECIO_POND']
            x_val = row[col_actual]
            anotaciones_totales.append(dict(
                x=x_val, y=p_val, xref='x', yref='y2',
                text=f"<b>S/{p_val:.2f}</b>",
                showarrow=True, arrowhead=0, arrowcolor='rgba(0,0,0,0)',
                yshift=11, bgcolor="#fffbeb", bordercolor="#d97706", borderwidth=1, borderpad=2.5,
                font=dict(color="#9a3412", size=8.5, family="Arial")
            ))

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
                x0=ini, x1=fin, y0=-0.28, y1=-0.28,
                line=dict(color="#94a3b8", width=1.2, dash="dot")
            ))
            lineas_estaciones.append(dict(
                type="line", xref="x", yref="paper",
                x0=ini, x1=ini, y0=-0.24, y1=-0.32,
                line=dict(color="#94a3b8", width=1.2)
            ))
            lineas_estaciones.append(dict(
                type="line", xref="x", yref="paper",
                x0=fin, x1=fin, y0=-0.24, y1=-0.32,
                line=dict(color="#94a3b8", width=1.2)
            ))
            
            idx_med = int(round((lista_meses.index(ini) + lista_meses.index(fin)) / 2))
            anotaciones_totales.append(dict(
                x=lista_meses[idx_med], y=-0.44, xref='x', yref='paper',
                text=f"<b>{nombre_est}</b>", showarrow=False,
                font=dict(size=9.5, color=color_txt, family='Arial')
            ))

        agregar_delimitador_estacion(m_verano, "☀️ Verano", "#854d0e")
        agregar_delimitador_estacion(m_otono, "🍂 Otoño", "#9a3412")
        agregar_delimitador_estacion(m_invierno, "❄️ Invierno", "#0369a1")
        agregar_delimitador_estacion(m_primavera, "🌸 Primavera", "#15803d")

    layout_dual = dict(
        autosize=True,
        clickmode='event+select',
        xaxis=dict(
            title='',
            tickangle=-32 if (periodo_sel == "Semanal" or mes_en_drilldown) else 0,
            tickfont=dict(size=9, color="#1e293b"),
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(title='Volumen (Tn)', showgrid=False, titlefont=dict(size=9.5), tickfont=dict(size=8.5)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9)),
        template='plotly_white',
        shapes=lineas_estaciones,
        annotations=anotaciones_totales,
        height=245,
        margin=dict(t=18, b=75 if (es_vista_mensual and not mes_en_drilldown) else 25, l=8, r=8)
    )
    if not ocultar_p:
        layout_dual['yaxis2'] = dict(title='Precio S/ /kg', overlaying='y', side='right', showgrid=True, titlefont=dict(size=9.5), tickfont=dict(size=8.5))

    fig_dual.update_layout(**layout_dual)

    chart_key = "grafico_mensual_click" if not mes_en_drilldown else f"grafico_semanal_{mes_en_drilldown}"
    chart_event = st.plotly_chart(fig_dual, use_container_width=True, config=PLOTLY_CONFIG, key=chart_key, on_select="rerun", selection_mode="points")

    if es_vista_mensual and not mes_en_drilldown:
        st.session_state.semana_seleccionada = None
        if chart_event:
            pts = chart_event.get("selection", {}).get("points", [])
            mes_detectado = None
            if pts:
                idx = pts[0].get("point_index")
                if idx is not None and 0 <= idx < len(df_trend):
                    mes_detectado = df_trend[col_actual].iloc[idx]
                if not mes_detectado:
                    x_val = str(pts[0].get("x", "")).strip()
                    if x_val in df_trend[col_actual].values:
                        mes_detectado = x_val
            if mes_detectado and mes_detectado in df_base['MES_AÑO'].unique():
                st.session_state.drilldown_mes = mes_detectado
                st.session_state.semana_seleccionada = None
                st.rerun(scope="fragment")
    else:
        if chart_event is not None and "selection" in chart_event:
            pts = chart_event.get("selection", {}).get("points", [])
            if pts:
                sem_detectada = None
                idx = pts[0].get("point_index")
                if idx is not None and 0 <= idx < len(df_trend):
                    sem_detectada = df_trend[col_actual].iloc[idx]
                if not sem_detectada:
                    x_val = str(pts[0].get("x", "")).strip()
                    if x_val in df_trend[col_actual].values:
                        sem_detectada = x_val
                st.session_state.semana_seleccionada = sem_detectada
            else:
                st.session_state.semana_seleccionada = None

    sem_activa = st.session_state.semana_seleccionada
    if sem_activa and sem_activa in df_detalle_grafico['SEMANA_AÑO'].values:
        df_detalle_grafico = df_detalle_grafico[df_detalle_grafico['SEMANA_AÑO'] == sem_activa].copy()
        etiqueta_filtro_tabla = f"Semana {sem_activa}"
    else:
        st.session_state.semana_seleccionada = None
        etiqueta_filtro_tabla = f"Mes {mes_en_drilldown}" if mes_en_drilldown else f"Vista {periodo_sel}"

    with st.expander("📋 Ver detalle de órdenes filtradas", expanded=False):
        st.caption(f"Filtro activo: **{etiqueta_filtro_tabla}** — **{len(df_detalle_grafico):,}** registros")
        df_tabla_det = df_detalle_grafico.sort_values(by=['FECHA_EMISION', 'NRO_OC'], ascending=[False, False]).copy()
        
        dias_es = {0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue', 4: 'Vie', 5: 'Sáb', 6: 'Dom'}
        df_tabla_det['FECHA_STR'] = df_tabla_det['FECHA_EMISION'].dt.strftime('%d/%m/%Y')
        df_tabla_det['DIA_SEM'] = df_tabla_det['FECHA_EMISION'].dt.dayofweek.map(dias_es)
        
        total_kg_sub = df_tabla_det['KILOS_SOLICITADOS'].sum()
        df_tabla_det['PART_KG_PCT'] = (df_tabla_det['KILOS_SOLICITADOS'] / total_kg_sub * 100) if total_kg_sub > 0 else 0

        tiene_cliente = 'CLIENTE' in df_tabla_det.columns and (df_tabla_det['CLIENTE'] != '').any()

        if ocultar_p:
            cols_base = ['FECHA_STR', 'DIA_SEM', 'NRO_OC'] + (['CLIENTE'] if tiene_cliente else []) + ['DESCRIPCION_PRODUCTO', 'KILOS_SOLICITADOS', 'PART_KG_PCT', 'JABAS_EST', 'FRUTOS_EST']
            nombres_base = ['Fecha', 'Día', 'N° OC'] + (['Cliente'] if tiene_cliente else []) + ['Variedad / Calibre', 'Kilos (kg)', '% Part.', 'Jabas Est.', 'Frutos Est.']
            df_show = df_tabla_det[cols_base].copy()
            df_show.columns = nombres_base
            st.dataframe(
                df_show.style.format({
                    'Kilos (kg)': '{:,.0f}',
                    '% Part.': '{:.1f}%',
                    'Jabas Est.': '{:,.1f}',
                    'Frutos Est.': '{:,.0f}'
                }),
                use_container_width=True, height=220, hide_index=True
            )
        else:
            cols_base = ['FECHA_STR', 'DIA_SEM', 'NRO_OC'] + (['CLIENTE'] if tiene_cliente else []) + ['DESCRIPCION_PRODUCTO', 'KILOS_SOLICITADOS', 'PART_KG_PCT', 'PRECIO_KG', 'VALOR_COMERCIAL', 'JABAS_EST', 'FRUTOS_EST']
            nombres_base = ['Fecha', 'Día', 'N° OC'] + (['Cliente'] if tiene_cliente else []) + ['Variedad / Calibre', 'Kilos (kg)', '% Part.', 'Precio (S/ /kg)', 'Valor Total (S/)', 'Jabas Est.', 'Frutos Est.']
            df_show = df_tabla_det[cols_base].copy()
            df_show.columns = nombres_base
            st.dataframe(
                df_show.style.format({
                    'Kilos (kg)': '{:,.0f}',
                    '% Part.': '{:.1f}%',
                    'Precio (S/ /kg)': 'S/ {:.2f}',
                    'Valor Total (S/)': 'S/ {:,.2f}',
                    'Jabas Est.': '{:,.1f}',
                    'Frutos Est.': '{:,.0f}'
                }),
                use_container_width=True, height=220, hide_index=True
            )

    max_vol_row = df_trend.loc[df_trend['KG_TOTALES'].idxmax()]
    max_p_row = df_trend.loc[df_trend['PRECIO_POND'].idxmax()]
    var_p_txt = f"({max_p_row['VAR_PRECIO_PCT']:+.1f}% vs periodo previo)" if pd.notna(max_p_row['VAR_PRECIO_PCT']) else ""
    
    insight_mercado_txt = ""
    if tiene_ref_mercado:
        df_trend['BRECHA_ESTACIONAL'] = df_trend['TN_TOTALES'] - df_trend['DEMANDA_REF_TN']
        mes_sobre = df_trend.loc[df_trend['BRECHA_ESTACIONAL'].idxmax()]
        mes_bajo = df_trend.loc[df_trend['BRECHA_ESTACIONAL'].idxmin()]
        insight_mercado_txt = f"<br>• <b>Alineación vs Demanda Lima:</b> Superas con mayor holgura el ritmo estacional en <b>{mes_sobre[col_actual]}</b> (+{mes_sobre['BRECHA_ESTACIONAL']:.1f} Tn sobre la curva referencial), mientras que la mayor oportunidad de captura de volumen está en <b>{mes_bajo[col_actual]}</b> ({mes_bajo['BRECHA_ESTACIONAL']:.1f} Tn vs tendencia)."

    insight_precio_linea = (
        f"• <b>Presión de Precios:</b> Información económica oculta en modo presentación."
        if ocultar_p else
        f"• <b>Presión de Precios:</b> La cotización ponderada más elevada se registró en <b>{max_p_row[col_actual]}</b> alcanzando <b>S/ {max_p_row['PRECIO_POND']:.2f} /kg</b> {var_p_txt}, coincidiendo con la contracción de oferta mayorista."
    )
    st.markdown(f"""
        <div class="chart-insight">
            <div class="insight-title">💡 Diagnóstico Operativo & Estacionalidad ({label_actual}):</div>
            • <b>Pico de Abastecimiento:</b> El mayor volumen se concentró en <b>{max_vol_row[col_actual]}</b> con <b>{max_vol_row['TN_TOTALES']:.1f} Tn</b> ({max_vol_row['ORDENES']} OCs despachadas).<br>
            {insight_precio_linea}{insight_mercado_txt}
        </div>
    """, unsafe_allow_html=True)

# ==========================================================
# HOJA 1: RESUMEN EJECUTIVO & EVOLUCIÓN
# ==========================================================
if vista_activa == "📊 Resumen & Evolución":
    if df.empty:
        st.warning("⚠️ No se encontraron órdenes de compra/venta para los filtros seleccionados.")
        st.stop()

    total_kg = df['KILOS_SOLICITADOS'].sum()
    valor_comercial_total = df['VALOR_COMERCIAL'].sum()
    precio_ponderado_total = valor_comercial_total / total_kg if total_kg > 0 else 0
    total_ocs = df['NRO_OC'].nunique()
    kg_promedio_oc = total_kg / total_ocs if total_ocs > 0 else 0
    total_jabas_est = df['JABAS_EST'].sum()
    peso_jaba_prom = df['PESO_JABA_EFECTIVO'].mean() if not df.empty else DEFAULT_KG_PER_JABA

    disp_facturacion = "S/ ••••••" if ocultar_precios else f"S/ {valor_comercial_total:,.0f}"
    disp_fact_sub = "Dato reservado" if ocultar_precios else "Venta total pactada"
    disp_precio = "S/ •.••" if ocultar_precios else f"S/ {precio_ponderado_total:.2f}"
    disp_precio_sub = "Dato reservado" if ocultar_precios else "Por kg promedio"

    st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card kpi-volumen">
                <div class="kpi-top">
                    <span class="kpi-title">Volumen Solicitado</span>
                    <span class="kpi-badge">📦 Kg</span>
                </div>
                <div class="kpi-value">{total_kg:,.0f} kg</div>
                <div class="kpi-sub">Total: <b>{total_kg/1000:,.1f} Tn</b></div>
            </div>
            <div class="kpi-card kpi-venta">
                <div class="kpi-top">
                    <span class="kpi-title">Facturación Bruta</span>
                    <span class="kpi-badge">💰 PEN</span>
                </div>
                <div class="kpi-value">{disp_facturacion}</div>
                <div class="kpi-sub">{disp_fact_sub}</div>
            </div>
            <div class="kpi-card kpi-precio">
                <div class="kpi-top">
                    <span class="kpi-title">Precio Ponderado</span>
                    <span class="kpi-badge">🏷️ Margen</span>
                </div>
                <div class="kpi-value">{disp_precio}</div>
                <div class="kpi-sub">{disp_precio_sub}</div>
            </div>
            <div class="kpi-card kpi-ordenes">
                <div class="kpi-top">
                    <span class="kpi-title">Órdenes Despachadas</span>
                    <span class="kpi-badge">📋 OCs</span>
                </div>
                <div class="kpi-value">{total_ocs:,}</div>
                <div class="kpi-sub">Promedio: <b>{kg_promedio_oc:,.0f} kg/OC</b></div>
            </div>
            <div class="kpi-card kpi-jabas">
                <div class="kpi-top">
                    <span class="kpi-title">Jabas Estimadas</span>
                    <span class="kpi-badge">🚛 Logística</span>
                </div>
                <div class="kpi-value">{total_jabas_est:,.0f}</div>
                <div class="kpi-sub">Ratio: {peso_jaba_prom:.0f} kg / jaba</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    render_evolucion_interactiva(df, periodo_seleccionado, año_seleccionado, ocultar_precios, col_periodo, label_periodo)

    df_trend_base = df.groupby(col_periodo).agg(
        KG_TOTALES=('KILOS_SOLICITADOS', 'sum'),
        VALOR_TOTAL=('VALOR_COMERCIAL', 'sum'),
        ORDENES=('NRO_OC', 'nunique')
    ).reset_index()
    df_trend_base['PRECIO_POND'] = df_trend_base['VALOR_TOTAL'] / df_trend_base['KG_TOTALES']
    df_trend_base['VAR_KG_PCT'] = df_trend_base['KG_TOTALES'].pct_change() * 100
    df_trend_base['VAR_PRECIO_PCT'] = df_trend_base['PRECIO_POND'].pct_change() * 100
    df_trend_base['VAR_VALOR_PCT'] = df_trend_base['VALOR_TOTAL'].pct_change() * 100

    col_mix, col_matriz = st.columns([1, 1.35])
    
    with col_mix:
        st.markdown('<div class="chart-header">🥑 Mix & Concentración por Variedad</div>', unsafe_allow_html=True)
        df_prod = df.groupby('DESCRIPCION_PRODUCTO').agg(
            VALOR=('VALOR_COMERCIAL', 'sum'),
            KG=('KILOS_SOLICITADOS', 'sum'),
            ORDENES=('NRO_OC', 'nunique')
        ).reset_index().sort_values(by='KG' if ocultar_precios else 'VALOR', ascending=False)
        
        valor_target_total = df['VALOR_COMERCIAL'].sum()
        kg_target_total = df['KILOS_SOLICITADOS'].sum()
        df_prod['PRECIO_POND'] = df_prod['VALOR'] / df_prod['KG']
        df_prod['PART_VALOR'] = (df_prod['VALOR'] / valor_target_total) * 100 if valor_target_total > 0 else 0
        df_prod['PART_KG'] = (df_prod['KG'] / kg_target_total) * 100 if kg_target_total > 0 else 0
        
        pie_colors = [VARIEDAD_COLORS.get(prod, '#0f3a28') for prod in df_prod['DESCRIPCION_PRODUCTO']]
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=df_prod['DESCRIPCION_PRODUCTO'],
            values=df_prod['KG'] if ocultar_precios else df_prod['VALOR'],
            hole=0.45,
            marker=dict(colors=pie_colors),
            textposition='inside',
            textinfo='percent+label',
            insidetextfont=dict(color='#ffffff', size=9, family="Arial"),
            hoverinfo='label+percent' if ocultar_precios else 'label+percent+value'
        )])
        
        fig_pie.update_layout(
            autosize=True,
            template='plotly_white',
            showlegend=False,
            height=225,
            margin=dict(t=5, b=5, l=5, r=5)
        )
        st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CONFIG)

        top_prod = df_prod.iloc[0]
        insight_mix_txt = (
            f"La variedad <b>{top_prod['DESCRIPCION_PRODUCTO']}</b> lidera el abastecimiento concentrando el <b>{top_prod['PART_KG']:.1f}%</b> del volumen total despachado ({top_prod['KG']:,.0f} kg)."
            if ocultar_precios else
            f"La variedad <b>{top_prod['DESCRIPCION_PRODUCTO']}</b> lidera la facturación representando el <b>{top_prod['PART_VALOR']:.1f}%</b> del valor bruto (S/ {top_prod['VALOR']:,.0f}) con un precio ponderado de <b>S/ {top_prod['PRECIO_POND']:.2f}/kg</b>."
        )
        st.markdown(f"""
            <div class="chart-insight" style="margin-top: 4px;">
                <div class="insight-title">📌 Concentración de Portafolio:</div>
                {insight_mix_txt}
            </div>
        """, unsafe_allow_html=True)

    with col_matriz:
        st.markdown(f'<div class="chart-header">📋 Variación Periódica ({label_periodo})</div>', unsafe_allow_html=True)
        if ocultar_precios:
            df_var_display = df_trend_base[[col_periodo, 'KG_TOTALES', 'VAR_KG_PCT', 'ORDENES']].copy()
            df_var_display.columns = [label_periodo, 'Kilos', 'Var Kg %', 'OCs']
            st.dataframe(
                df_var_display.style.format({
                    'Kilos': '{:,.0f}',
                    'Var Kg %': '{:+.1f}%',
                    'OCs': '{:,}'
                })
                .map(style_semaphore, subset=['Var Kg %'])
                .highlight_null(color='#f1f5f9'),
                use_container_width=True, height=225, hide_index=True
            )
            st.markdown("""
                <div class="chart-insight" style="margin-top: 4px;">
                    <div class="insight-title">📊 Auditoría de Volumen:</div>
                    Seguimiento interperiódico de kilogramos despachados y frecuencia de órdenes de compra (columnas financieras ocultas).
                </div>
            """, unsafe_allow_html=True)
        else:
            df_var_display = df_trend_base[[col_periodo, 'KG_TOTALES', 'VAR_KG_PCT', 'PRECIO_POND', 'VAR_PRECIO_PCT', 'VALOR_TOTAL', 'VAR_VALOR_PCT', 'ORDENES']].copy()
            df_var_display.columns = [label_periodo, 'Kilos', 'Var %', 'P. Pond', 'Var P %', 'Venta (S/)', 'Var V %', 'OCs']
            st.dataframe(
                df_var_display.style.format({
                    'Kilos': '{:,.0f}',
                    'Var %': '{:+.1f}%',
                    'P. Pond': 'S/ {:.2f}',
                    'Var P %': '{:+.1f}%',
                    'Venta (S/)': 'S/ {:,.0f}',
                    'Var V %': '{:+.1f}%',
                    'OCs': '{:,}'
                })
                .map(style_semaphore, subset=['Var %', 'Var P %', 'Var V %'])
                .highlight_null(color='#f1f5f9'),
                use_container_width=True, height=225, hide_index=True
            )
            prom_var_precio = df_trend_base['VAR_PRECIO_PCT'].mean()
            var_m_txt = f"{prom_var_precio:+.1f}%" if pd.notna(prom_var_precio) else "N/A"
            st.markdown(f"""
                <div class="chart-insight" style="margin-top: 4px;">
                    <div class="insight-title">📊 Auditoría de Desempeño:</div>
                    La volatilidad interperiódica promedio de precio fue de <b>{var_m_txt}</b>. Las celdas en verde reflejan ventanas de captura de mayor margen por kilogramo despachado frente al periodo previo.
                </div>
            """, unsafe_allow_html=True)

# ==========================================================
# HOJA 2: BENCHMARK & PREVISIÓN
# ==========================================================
elif vista_activa == "🎯 Benchmark & Previsión":
    if df.empty:
        st.warning("⚠️ No se encontraron órdenes de compra/venta para los filtros seleccionados.")
        st.stop()

    total_kg = df['KILOS_SOLICITADOS'].sum()
    valor_comercial_total = df['VALOR_COMERCIAL'].sum()
    precio_ponderado_total = valor_comercial_total / total_kg if total_kg > 0 else 0
    total_ocs = df['NRO_OC'].nunique()
    kg_promedio_oc = total_kg / total_ocs if total_ocs > 0 else 0
    total_jabas_est = df['JABAS_EST'].sum()
    peso_jaba_prom = df['PESO_JABA_EFECTIVO'].mean() if not df.empty else DEFAULT_KG_PER_JABA

    disp_facturacion = "S/ ••••••" if ocultar_precios else f"S/ {valor_comercial_total:,.0f}"
    disp_fact_sub = "Dato reservado" if ocultar_precios else "Venta total pactada"
    disp_precio = "S/ •.••" if ocultar_precios else f"S/ {precio_ponderado_total:.2f}"
    disp_precio_sub = "Dato reservado" if ocultar_precios else "Por kg promedio"

    st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card kpi-volumen">
                <div class="kpi-top">
                    <span class="kpi-title">Volumen Solicitado</span>
                    <span class="kpi-badge">📦 Kg</span>
                </div>
                <div class="kpi-value">{total_kg:,.0f} kg</div>
                <div class="kpi-sub">Total: <b>{total_kg/1000:,.1f} Tn</b></div>
            </div>
            <div class="kpi-card kpi-venta">
                <div class="kpi-top">
                    <span class="kpi-title">Facturación Bruta</span>
                    <span class="kpi-badge">💰 PEN</span>
                </div>
                <div class="kpi-value">{disp_facturacion}</div>
                <div class="kpi-sub">{disp_fact_sub}</div>
            </div>
            <div class="kpi-card kpi-precio">
                <div class="kpi-top">
                    <span class="kpi-title">Precio Ponderado</span>
                    <span class="kpi-badge">🏷️ Margen</span>
                </div>
                <div class="kpi-value">{disp_precio}</div>
                <div class="kpi-sub">{disp_precio_sub}</div>
            </div>
            <div class="kpi-card kpi-ordenes">
                <div class="kpi-top">
                    <span class="kpi-title">Órdenes Despachadas</span>
                    <span class="kpi-badge">📋 OCs</span>
                </div>
                <div class="kpi-value">{total_ocs:,}</div>
                <div class="kpi-sub">Promedio: <b>{kg_promedio_oc:,.0f} kg/OC</b></div>
            </div>
            <div class="kpi-card kpi-jabas">
                <div class="kpi-top">
                    <span class="kpi-title">Jabas Estimadas</span>
                    <span class="kpi-badge">🚛 Logística</span>
                </div>
                <div class="kpi-value">{total_jabas_est:,.0f}</div>
                <div class="kpi-sub">Ratio: {peso_jaba_prom:.0f} kg / jaba</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if ocultar_precios:
        st.info("🔒 **Modo Presentación Activo:** Los comparativos de precios mayoristas, márgenes y bandas de negociación están ocultos. Desactiva el modo en el panel lateral para visualizar esta sección.")
    else:
        meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Dic']

        if not df_mercado_raw.empty:
            df_m = df_mercado_raw.copy()
            df_m['AÑO'] = df_m['Fecha'].dt.year
            df_m['MES'] = df_m['Fecha'].dt.month
            
            mkt_mensual = df_m.groupby(['AÑO', 'MES'])['Palta Fuerte'].mean().unstack(level=0)
            mkt_2025 = [mkt_mensual[2025].get(i, np.nan) if 2025 in mkt_mensual else np.nan for i in range(1, 13)]
            mkt_2026_real = [mkt_mensual[2026].get(i, np.nan) if 2026 in mkt_mensual else np.nan for i in range(1, 13)]
            
            df_kco = df_all_raw[(df_all_raw['AÑO'] == año_seleccionado) & (~df_all_raw['ES_DEVOLUCION'])].copy()
            df_kco['MES'] = df_kco['FECHA_EMISION'].dt.month
            kco_mensual = df_kco.groupby('MES').agg(
                KILOS=('KILOS_SOLICITADOS', 'sum'),
                VALOR=('VALOR_COMERCIAL', 'sum')
            ).reset_index()
            kco_mensual['PRECIO_POND'] = kco_mensual['VALOR'] / kco_mensual['KILOS']
            kco_dict = dict(zip(kco_mensual['MES'], kco_mensual['PRECIO_POND']))
            kco_2026_real = [kco_dict.get(i, np.nan) for i in range(1, 13)]

            # Previsión Dic 2026
            factor_estacional_dic = (mkt_2025[11] - mkt_2025[10]) / mkt_2025[10] if pd.notna(mkt_2025[10]) and pd.notna(mkt_2025[11]) else -0.20
            mkt_nov_val = mkt_2026_real[10] if pd.notna(mkt_2026_real[10]) else 8.59
            mkt_dic_pred = round(mkt_nov_val * (1 + factor_estacional_dic), 2)
            
            kco_nov_val = kco_2026_real[10] if pd.notna(kco_2026_real[10]) else 11.00
            spread_historico = np.nanmean(np.array(kco_2026_real[:11]) - np.array(mkt_2026_real[:11]))
            if pd.isna(spread_historico):
                spread_historico = 2.74
            kco_dic_pred = round(mkt_dic_pred + (spread_historico * 0.95), 2)

            text_mkt_intercalado = [f"<b>S/{val:.2f}</b>" if (pd.notna(val) and ((idx+1)%2 != 0 or (idx+1)==11)) else "" for idx, val in enumerate(mkt_2026_real[:11])]
            text_kco_intercalado = [f"<b>S/{val:.2f}</b>" if (pd.notna(val) and ((idx+1)%2 == 0 or (idx+1)==11)) else "" for idx, val in enumerate(kco_2026_real[:11])]

            st.markdown('<div class="chart-header">🎯 Comparativo Anual de Precios: Mayorista vs KCO Retail & Previsión a Diciembre</div>', unsafe_allow_html=True)
            fig_anual = go.Figure()

            fig_anual.add_trace(go.Scatter(
                x=meses_nombres, y=mkt_2025, name='Mayorista 2025',
                mode='lines+markers', line=dict(color='#cbd5e1', width=1.5, dash='dot'),
                marker=dict(size=4, color='#cbd5e1'), hovertemplate="<b>%{x} (2025)</b>: S/ %{y:.2f}<extra></extra>"
            ))
            fig_anual.add_trace(go.Scatter(
                x=meses_nombres[:11], y=mkt_2026_real[:11], name='Mayorista 2026',
                mode='lines+markers+text', text=text_mkt_intercalado, textposition='bottom center',
                textfont=dict(color='#475569', size=9.5, family='Arial'),
                line=dict(color='#475569', width=2.2), marker=dict(size=6, color='#475569'),
                hovertemplate="<b>%{x} Mayorista</b>: S/ %{y:.2f}<extra></extra>"
            ))
            fig_anual.add_trace(go.Scatter(
                x=['Nov', 'Dic'], y=[mkt_nov_val, mkt_dic_pred], name='Mayorista (Dic Proy)',
                mode='lines+markers+text', text=["", f"<b>S/{mkt_dic_pred:.2f}*</b>"], textposition='bottom center',
                textfont=dict(color='#64748b', size=9.5, family='Arial'), line=dict(color='#64748b', width=2, dash='dash'),
                marker=dict(size=7, symbol='diamond', color='#64748b'), hovertemplate="<b>Dic Proy Mayorista</b>: S/ %{y:.2f}<extra></extra>"
            ))
            fig_anual.add_trace(go.Scatter(
                x=meses_nombres[:11], y=kco_2026_real[:11], name='KCO Venta 2026',
                mode='lines+markers+text', text=text_kco_intercalado, textposition='top center',
                textfont=dict(color='#0f3a28', size=9.5, family='Arial'),
                line=dict(color='#0f3a28', width=2.8), marker=dict(size=7, color='#0f3a28'),
                hovertemplate="<b>%{x} KCO</b>: S/ %{y:.2f}<extra></extra>"
            ))
            fig_anual.add_trace(go.Scatter(
                x=['Nov', 'Dic'], y=[kco_nov_val, kco_dic_pred], name='KCO (Dic Proy)',
                mode='lines+markers+text', text=["", f"<b>S/{kco_dic_pred:.2f}*</b>"], textposition='top center',
                textfont=dict(color='#d97706', size=10, family='Arial'), line=dict(color='#d97706', width=2.5, dash='dash'),
                marker=dict(size=8, symbol='star', color='#d97706'), hovertemplate="<b>Dic Cotización Sugerida</b>: S/ %{y:.2f}<extra></extra>"
            ))

            fig_anual.update_layout(
                autosize=True, template='plotly_white', height=215,
                xaxis=dict(title='', categoryorder='array', categoryarray=meses_nombres, tickfont=dict(size=9, color='#1e293b')),
                yaxis=dict(title='Precio S/ /kg', gridcolor='#f1f5f9', zeroline=False, titlefont=dict(size=9), tickfont=dict(size=8.5)),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=9)),
                margin=dict(t=25, b=20, l=8, r=8)
            )
            st.plotly_chart(fig_anual, use_container_width=True, config=PLOTLY_CONFIG)

            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                st.markdown(f'<div class="kpi-card kpi-ordenes"><div class="kpi-title">Mayorista (Nov Real ➔ Dic Proy)</div><div class="kpi-value" style="font-size:16px;">S/ {mkt_nov_val:.2f} ➔ S/ {mkt_dic_pred:.2f}</div><div class="kpi-sub">Ajuste estacional (-20.1%)</div></div>', unsafe_allow_html=True)
            with c_p2:
                st.markdown(f'<div class="kpi-card kpi-volumen"><div class="kpi-title">KCO Venta Cliente (Nov Real)</div><div class="kpi-value" style="font-size:16px;">S/ {kco_nov_val:.2f} /kg</div><div class="kpi-sub">Ponderado consolidado</div></div>', unsafe_allow_html=True)
            with c_p3:
                st.markdown(f'<div class="kpi-card kpi-precio"><div class="kpi-title">KCO Sugerido (Dic Proy)</div><div class="kpi-value" style="font-size:16px;">S/ {kco_dic_pred:.2f} /kg</div><div class="kpi-sub">Rango: S/ {kco_dic_pred - 0.30:.2f} - S/ {kco_dic_pred + 0.30:.2f}</div></div>', unsafe_allow_html=True)

            st.markdown(f"""
                <div class="chart-insight">
                    <div class="insight-title">💡 Estrategia de Pricing Proyectada (Diciembre):</div>
                    El ingreso de fruta temprana de valles costeros empuja a la baja el costo mayorista hacia <b>S/ {mkt_dic_pred:.2f} /kg</b>. Mantener la cotización objetivo al cliente en <b>S/ {kco_dic_pred:.2f} /kg</b> protege tu spread comercial promedio de <b>S/ {spread_historico:.2f}/kg</b> frente a competidores directos.
                </div>
            """, unsafe_allow_html=True)

            col_b1, col_b2 = st.columns([1.1, 1.4])
            with col_b1:
                st.markdown('<div class="chart-header">🎯 Banda de Negociación por Variedad</div>', unsafe_allow_html=True)
                df_banda = df.groupby('DESCRIPCION_PRODUCTO').agg(PRECIO_MIN=('PRECIO_KG', 'min'), PRECIO_MAX=('PRECIO_KG', 'max'), KILOS=('KILOS_SOLICITADOS', 'sum'), VALOR=('VALOR_COMERCIAL', 'sum')).reset_index()
                df_banda['PRECIO_POND'] = df_banda['VALOR'] / df_banda['KILOS']
                
                fig_banda = go.Figure()
                fig_banda.add_trace(go.Bar(
                    name='Rango Min-Max', x=df_banda['DESCRIPCION_PRODUCTO'], y=df_banda['PRECIO_MAX'] - df_banda['PRECIO_MIN'], base=df_banda['PRECIO_MIN'],
                    marker_color='rgba(15, 58, 40, 0.22)', hovertemplate="<b>%{x}</b><br>Piso: S/ %{base:.2f}<br>Techo: S/ %{customdata:.2f}<extra></extra>", customdata=df_banda['PRECIO_MAX']
                ))
                fig_banda.add_trace(go.Scatter(
                    name='Precio Pond', x=df_banda['DESCRIPCION_PRODUCTO'], y=df_banda['PRECIO_POND'], mode='markers+text',
                    text=df_banda['PRECIO_POND'].apply(lambda x: f"<b>S/{x:.2f}</b>"), textposition='top center', textfont=dict(color='#0f172a', size=8.5),
                    marker=dict(size=7, color=COLOR_ACCENT, symbol='diamond')
                ))
                fig_banda.update_layout(autosize=True, template='plotly_white', height=205, showlegend=False, yaxis=dict(title='Precio S/ /kg', titlefont=dict(size=8.5), tickfont=dict(size=8)), xaxis=dict(tickfont=dict(size=8)), margin=dict(t=10, b=15, l=8, r=8))
                st.plotly_chart(fig_banda, use_container_width=True, config=PLOTLY_CONFIG)

                spread_max_var = (df_banda['PRECIO_MAX'] - df_banda['PRECIO_MIN']).max()
                st.markdown(f"""
                    <div class="chart-insight" style="margin-top: 4px;">
                        <div class="insight-title">🎯 Dispersión de Precios:</div>
                        La dispersión máxima pactada entre piso y techo alcanza <b>S/ {spread_max_var:.2f}/kg</b>. Los diamantes representan el precio real ponderado por volumen.
                    </div>
                """, unsafe_allow_html=True)

            df_prod_trend = df.groupby(['DESCRIPCION_PRODUCTO', col_periodo]).agg(KG=('KILOS_SOLICITADOS', 'sum'), VALOR=('VALOR_COMERCIAL', 'sum')).reset_index()
            df_prod_trend['PRECIO_POND'] = df_prod_trend['VALOR'] / df_prod_trend['KG']
            df_prod_trend = df_prod_trend.sort_values(by=['DESCRIPCION_PRODUCTO', col_periodo])
            df_prod_trend['PRECIO_PREV'] = df_prod_trend.groupby('DESCRIPCION_PRODUCTO')['PRECIO_POND'].shift(1)
            df_prod_trend['VAR_PRECIO_PCT'] = ((df_prod_trend['PRECIO_POND'] - df_prod_trend['PRECIO_PREV']) / df_prod_trend['PRECIO_PREV']) * 100
            df_prod_trend['DIF_SOLES'] = df_prod_trend['PRECIO_POND'] - df_prod_trend['PRECIO_PREV']
            df_changes = df_prod_trend[df_prod_trend['VAR_PRECIO_PCT'].notna() & (df_prod_trend['VAR_PRECIO_PCT'] != 0)].copy()

            with col_b2:
                st.markdown('<div class="chart-header">📊 Historial de Variaciones de Precio (%)</div>', unsafe_allow_html=True)
                if not df_changes.empty:
                    fig_var = px.bar(
                        df_changes.tail(15), x=col_periodo, y='VAR_PRECIO_PCT', color='VAR_PRECIO_PCT',
                        text=df_changes.tail(15)['VAR_PRECIO_PCT'].apply(lambda x: f"<b>{x:+.1f}%</b>"),
                        color_continuous_scale='RdYlGn', custom_data=['DESCRIPCION_PRODUCTO', 'PRECIO_PREV', 'PRECIO_POND']
                    )
                    fig_var.update_traces(textposition='outside', outsidetextfont=dict(color='#0f172a', size=8.5))
                    fig_var.update_layout(autosize=True, template='plotly_white', height=205, coloraxis_showscale=False, yaxis=dict(title='Var %', titlefont=dict(size=8.5), tickfont=dict(size=8)), xaxis=dict(title='', tickangle=-30, tickfont=dict(size=8)), margin=dict(t=10, b=15, l=8, r=8))
                    st.plotly_chart(fig_var, use_container_width=True, config=PLOTLY_CONFIG)
                else:
                    st.info("Sin variaciones en el periodo.")

                st.markdown(f"""
                    <div class="chart-insight" style="margin-top: 4px;">
                        <div class="insight-title">📈 Sensibilidad de Cotización:</div>
                        Monitorea los ajustes directos acordados en órdenes consecutivas. Las barras rojas identifican concesiones de precio y las verdes incrementos netos.
                    </div>
                """, unsafe_allow_html=True)

            with st.expander("📋 Ver Matriz Histórica de Cambios de Precio"):
                if not df_changes.empty:
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
                        use_container_width=True, height=210, hide_index=True
                    )
                else:
                    st.info("No hay variaciones de precios registradas en el rango seleccionado.")

# ==========================================================
# HOJA 3: LOGÍSTICA & DEVOLUCIONES
# ==========================================================
elif vista_activa == "🚛 Logística & Devoluciones":
    jabas_despachadas = df['JABAS_EST'].sum()
    kg_despachados = df['KILOS_SOLICITADOS'].sum()
    inversion_total = df['INVERSION_COMPRA'].sum()
    costo_compra_prom = inversion_total / kg_despachados if kg_despachados > 0 else 0

    kg_devueltos = df_dev['KILOS_SOLICITADOS'].sum()
    jabas_devueltas = df_dev['JABAS_EST'].sum()
    costo_dev_total = df_dev['COSTO_DEVOLUCION'].sum()
    tasa_dev_pct = (kg_devueltos / kg_despachados * 100) if kg_despachados > 0 else 0.0

    disp_inv = "S/ ••••••" if ocultar_precios else f"S/ {inversion_total:,.0f}"
    disp_costo_u = "S/ •.•• /kg" if ocultar_precios else f"S/ {costo_compra_prom:.2f} /kg"
    disp_dev_costo = "Dato reservado" if ocultar_precios else f"Impacto: S/ {costo_dev_total:,.0f}"

    st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card kpi-jabas">
                <div class="kpi-top">
                    <span class="kpi-title">Jabas Despachadas</span>
                    <span class="kpi-badge">📦 Carga</span>
                </div>
                <div class="kpi-value">{jabas_despachadas:,.0f}</div>
                <div class="kpi-sub">Volumen: <b>{kg_despachados:,.0f} kg</b></div>
            </div>
            <div class="kpi-card kpi-venta">
                <div class="kpi-top">
                    <span class="kpi-title">Inversión en Compra</span>
                    <span class="kpi-badge">💵 Capital</span>
                </div>
                <div class="kpi-value">{disp_inv}</div>
                <div class="kpi-sub">Compra directa proveedor</div>
            </div>
            <div class="kpi-card kpi-precio">
                <div class="kpi-top">
                    <span class="kpi-title">Costo Prom. Compra</span>
                    <span class="kpi-badge">⚖️ Unitario</span>
                </div>
                <div class="kpi-value">{disp_costo_u}</div>
                <div class="kpi-sub">Ponderado por kg</div>
            </div>
            <div class="kpi-card kpi-danger">
                <div class="kpi-top">
                    <span class="kpi-title">Volumen Devuelto</span>
                    <span class="kpi-badge">↩️ Merma</span>
                </div>
                <div class="kpi-value">{kg_devueltos:,.0f} kg</div>
                <div class="kpi-sub">Equiv: <b>{jabas_devueltas:,.1f} jabas</b></div>
            </div>
            <div class="kpi-card kpi-ordenes">
                <div class="kpi-top">
                    <span class="kpi-title">Tasa de Devolución</span>
                    <span class="kpi-badge">📉 Calidad</span>
                </div>
                <div class="kpi-value">{tasa_dev_pct:.2f}%</div>
                <div class="kpi-sub">{disp_dev_costo}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 1. GRÁFICO SUPERIOR: CONTROL LOGÍSTICO DE JABAS POR SEMANA (APILADO POR PRODUCTO)
    st.markdown('<div class="chart-header">🚛 Control Logístico: Jabas Despachadas por Semana y Variedad</div>', unsafe_allow_html=True)
    if not df.empty:
        df_jabas_sem = df.groupby(['SEMANA_AÑO', 'DESCRIPCION_PRODUCTO']).agg(
            JABAS=('JABAS_EST', 'sum'),
            KG=('KILOS_SOLICITADOS', 'sum')
        ).reset_index().sort_values('SEMANA_AÑO')

        semanas_unicas = sorted(df_jabas_sem['SEMANA_AÑO'].unique().tolist())
        if len(semanas_unicas) > 24:
            semanas_vis = semanas_unicas[-24:]
            df_jabas_sem = df_jabas_sem[df_jabas_sem['SEMANA_AÑO'].isin(semanas_vis)]

        tot_sem = df_jabas_sem.groupby('SEMANA_AÑO')['JABAS'].sum().reset_index()
        prom_jabas_sem = tot_sem['JABAS'].mean()

        fig_jabas = px.bar(
            df_jabas_sem,
            x='SEMANA_AÑO',
            y='JABAS',
            color='DESCRIPCION_PRODUCTO',
            color_discrete_map=VARIEDAD_COLORS,
            custom_data=['KG']
        )
        fig_jabas.update_traces(
            hovertemplate="<b>%{x}</b><br>Producto: %{fullData.name}<br>Jabas: %{y:,.1f}<br>Kilos: %{customdata[0]:,.0f} kg<extra></extra>"
        )
        fig_jabas.add_trace(go.Scatter(
            x=tot_sem['SEMANA_AÑO'],
            y=tot_sem['JABAS'],
            mode='text',
            text=tot_sem['JABAS'].apply(lambda x: f"<b>{x:,.0f}</b>"),
            textposition='top center',
            textfont=dict(color='#0f172a', size=8.5),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig_jabas.add_hline(
            y=prom_jabas_sem,
            line_dash="dot",
            line_color="#d97706",
            annotation_text=f"Prom: {prom_jabas_sem:,.0f} jabas/sem",
            annotation_position="top left",
            annotation_font=dict(size=9, color="#b45309")
        )
        fig_jabas.update_layout(
            barmode='stack',
            autosize=True,
            template='plotly_white',
            height=245,
            xaxis=dict(title='', tickangle=-30, tickfont=dict(size=8.5)),
            yaxis=dict(title='Jabas Despachadas', titlefont=dict(size=9), tickfont=dict(size=8.5)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title='', font=dict(size=8.5)),
            margin=dict(t=22, b=28, l=8, r=8)
        )
        st.plotly_chart(fig_jabas, use_container_width=True, config=PLOTLY_CONFIG)

        pico_sem = tot_sem.loc[tot_sem['JABAS'].idxmax()]
        st.markdown(f"""
            <div class="chart-insight">
                <div class="insight-title">📦 Ritmo de Despacho Semanal:</div>
                El flujo logístico promedio es de <b>{prom_jabas_sem:,.0f} jabas por semana</b>, alcanzando su pico máximo en <b>{pico_sem['SEMANA_AÑO']}</b> con <b>{pico_sem['JABAS']:,.0f} jabas</b> movilizadas.
            </div>
        """, unsafe_allow_html=True)

    # 2. FILA INFERIOR: INVERSIÓN POR PRODUCTO + CONTROL DE DEVOLUCIONES
    col_inv, col_dev = st.columns([1.05, 1.35])

    with col_inv:
        st.markdown('<div class="chart-header">💵 Inversión en Compra por Producto</div>', unsafe_allow_html=True)
        df_inv_prod = df.groupby('DESCRIPCION_PRODUCTO').agg(
            INVERSION=('INVERSION_COMPRA', 'sum'),
            KG=('KILOS_SOLICITADOS', 'sum'),
            JABAS=('JABAS_EST', 'sum')
        ).reset_index()
        df_inv_prod['COSTO_UNIT'] = np.where(df_inv_prod['KG'] > 0, df_inv_prod['INVERSION'] / df_inv_prod['KG'], 0)
        df_inv_prod = df_inv_prod.sort_values(by='JABAS' if ocultar_precios else 'INVERSION', ascending=True)

        if ocultar_precios:
            fig_inv = go.Figure(go.Bar(
                x=df_inv_prod['JABAS'],
                y=df_inv_prod['DESCRIPCION_PRODUCTO'],
                orientation='h',
                marker_color=[VARIEDAD_COLORS.get(p, COLOR_PRIMARY) for p in df_inv_prod['DESCRIPCION_PRODUCTO']],
                text=df_inv_prod['JABAS'].apply(lambda x: f"<b>{x:,.0f} jabas</b>"),
                textposition='outside',
                cliponaxis=False
            ))
            fig_inv.update_layout(
                autosize=True, template='plotly_white', height=225,
                xaxis=dict(title='Jabas', tickfont=dict(size=8.5)),
                yaxis=dict(title='', tickfont=dict(size=8.5)),
                margin=dict(t=10, b=20, l=8, r=55)
            )
            st.plotly_chart(fig_inv, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            fig_inv = go.Figure(go.Bar(
                x=df_inv_prod['INVERSION'],
                y=df_inv_prod['DESCRIPCION_PRODUCTO'],
                orientation='h',
                marker_color=[VARIEDAD_COLORS.get(p, COLOR_PRIMARY) for p in df_inv_prod['DESCRIPCION_PRODUCTO']],
                text=df_inv_prod.apply(lambda r: f"<b>S/ {r['INVERSION']:,.0f}</b> (S/{r['COSTO_UNIT']:.2f}/kg)", axis=1),
                textposition='outside',
                cliponaxis=False,
                textfont=dict(size=8.5, color='#0f172a'),
                hovertemplate="<b>%{y}</b><br>Inversión: S/ %{x:,.2f}<br>Jabas: %{customdata[0]:,.0f}<br>Kilos: %{customdata[1]:,.0f} kg<extra></extra>",
                customdata=np.stack((df_inv_prod['JABAS'], df_inv_prod['KG']), axis=-1)
            ))
            fig_inv.update_layout(
                autosize=True, template='plotly_white', height=225,
                xaxis=dict(title='Inversión (S/)', tickfont=dict(size=8.5)),
                yaxis=dict(title='', tickfont=dict(size=8.5)),
                margin=dict(t=10, b=20, l=8, r=95)
            )
            st.plotly_chart(fig_inv, use_container_width=True, config=PLOTLY_CONFIG)

        top_inv = df_inv_prod.iloc[-1]
        part_inv = (top_inv['INVERSION'] / inversion_total * 100) if inversion_total > 0 else 0
        txt_inv_ins = (
            f"El calibre <b>{top_inv['DESCRIPCION_PRODUCTO']}</b> concentra el mayor movimiento físico con <b>{top_inv['JABAS']:,.0f} jabas</b>."
            if ocultar_precios else
            f"<b>{top_inv['DESCRIPCION_PRODUCTO']}</b> absorbe el <b>{part_inv:.1f}%</b> del capital invertido (<b>S/ {top_inv['INVERSION']:,.0f}</b>) a un costo promedio de <b>S/ {top_inv['COSTO_UNIT']:.2f}/kg</b>."
        )
        st.markdown(f"""
            <div class="chart-insight" style="margin-top: 4px;">
                <div class="insight-title">💼 Asignación de Capital por Calibre:</div>
                {txt_inv_ins}
            </div>
        """, unsafe_allow_html=True)

    with col_dev:
        st.markdown('<div class="chart-header">↩️ Control de Devoluciones (Por Producto y Proveedor)</div>', unsafe_allow_html=True)
        if df_dev.empty:
            st.success("✅ No se registran devoluciones en el rango y filtros seleccionados.")
            st.markdown("""
                <div class="chart-insight" style="margin-top: 4px;">
                    <div class="insight-title">🛡️ Calidad de Entrega:</div>
                    0% de merma por devoluciones en el periodo analizado.
                </div>
            """, unsafe_allow_html=True)
        else:
            df_dev_grp = df_dev.groupby(['DESCRIPCION_PRODUCTO', 'PROVEEDOR']).agg(
                KG_DEV=('KILOS_SOLICITADOS', 'sum'),
                JABAS_DEV=('JABAS_EST', 'sum'),
                COSTO_DEV=('COSTO_DEVOLUCION', 'sum'),
                DOCS=('NRO_OC', 'count')
            ).reset_index().sort_values(by='COSTO_DEV' if not ocultar_precios else 'KG_DEV', ascending=False)

            if ocultar_precios:
                tbl_dev = df_dev_grp[['DESCRIPCION_PRODUCTO', 'PROVEEDOR', 'KG_DEV', 'JABAS_DEV', 'DOCS']].copy()
                tbl_dev.columns = ['Producto', 'Proveedor', 'Kg Devueltos', 'Jabas Dev.', 'Registros']
                st.dataframe(
                    tbl_dev.style.format({'Kg Devueltos': '{:,.0f}', 'Jabas Dev.': '{:,.1f}', 'Registros': '{:,}'}),
                    use_container_width=True, height=225, hide_index=True
                )
            else:
                tbl_dev = df_dev_grp[['DESCRIPCION_PRODUCTO', 'PROVEEDOR', 'KG_DEV', 'JABAS_DEV', 'COSTO_DEV']].copy()
                tbl_dev.columns = ['Producto', 'Proveedor', 'Kg Devueltos', 'Jabas Dev.', 'Costo DEV (S/)']
                st.dataframe(
                    tbl_dev.style.format({'Kg Devueltos': '{:,.0f}', 'Jabas Dev.': '{:,.1f}', 'Costo DEV (S/)': 'S/ {:,.2f}'}),
                    use_container_width=True, height=225, hide_index=True
                )

            peor_dev = df_dev_grp.iloc[0]
            txt_dev_ins = (
                f"Mayor incidencia en <b>{peor_dev['DESCRIPCION_PRODUCTO']}</b> (Proveedor: <b>{peor_dev['PROVEEDOR'] or 'N/E'}</b>) con <b>{peor_dev['KG_DEV']:,.0f} kg</b> devueltos."
                if ocultar_precios else
                f"Mayor impacto en <b>{peor_dev['DESCRIPCION_PRODUCTO']}</b> (Proveedor: <b>{peor_dev['PROVEEDOR'] or 'N/E'}</b>) con <b>{peor_dev['KG_DEV']:,.0f} kg</b> y un costo asumido de <b>S/ {peor_dev['COSTO_DEV']:,.2f}</b>."
            )
            st.markdown(f"""
                <div class="chart-insight" style="margin-top: 4px;">
                    <div class="insight-title">⚠️ Foco de Devoluciones:</div>
                    {txt_dev_ins}
                </div>
            """, unsafe_allow_html=True)

    # 3. EXPANDER DE DETALLE DE DEVOLUCIONES
    if not df_dev.empty:
        with st.expander("📋 Ver detalle línea por línea de devoluciones", expanded=False):
            df_dev_det = df_dev.sort_values('FECHA_EMISION', ascending=False).copy()
            df_dev_det['FECHA_STR'] = df_dev_det['FECHA_EMISION'].dt.strftime('%d/%m/%Y')
            if ocultar_precios:
                d_show = df_dev_det[['FECHA_STR', 'NRO_OC', 'CLIENTE', 'PROVEEDOR', 'DESCRIPCION_PRODUCTO', 'KILOS_SOLICITADOS', 'JABAS_EST']].copy()
                d_show.columns = ['Fecha', 'N° OC', 'Cliente', 'Proveedor', 'Producto', 'Kilos Dev.', 'Jabas']
                st.dataframe(d_show.style.format({'Kilos Dev.': '{:,.0f}', 'Jabas': '{:,.1f}'}), use_container_width=True, height=200, hide_index=True)
            else:
                d_show = df_dev_det[['FECHA_STR', 'NRO_OC', 'CLIENTE', 'PROVEEDOR', 'DESCRIPCION_PRODUCTO', 'KILOS_SOLICITADOS', 'COSTO_DEV_UNIT', 'COSTO_DEVOLUCION']].copy()
                d_show.columns = ['Fecha', 'N° OC', 'Cliente', 'Proveedor', 'Producto', 'Kilos Dev.', 'Costo Unit. DEV', 'Costo Total DEV']
                st.dataframe(d_show.style.format({'Kilos Dev.': '{:,.0f}', 'Costo Unit. DEV': 'S/ {:.2f}', 'Costo Total DEV': 'S/ {:,.2f}'}), use_container_width=True, height=200, hide_index=True)

# ==========================================================
# HOJA 4: FINANCIERO & MÁRGENES
# ==========================================================
else:
    if ocultar_precios:
        st.info("🔒 **Modo Presentación Activo:** Los estados de resultados, cascada de utilidad, márgenes y costos están ocultos. Desactiva el modo en el panel lateral para visualizar esta sección.")
    else:
        venta_bruta = df['VALOR_COMERCIAL'].sum()
        costo_mercaderia = df['INVERSION_COMPRA'].sum()
        impacto_devoluciones = df_dev['COSTO_DEVOLUCION'].sum()
        gastos_operativos = df_gastos_filtered['MONTO'].sum() if not df_gastos_filtered.empty else 0.0

        utilidad_bruta_fruta = venta_bruta - costo_mercaderia - impacto_devoluciones
        utilidad_neta = utilidad_bruta_fruta - gastos_operativos
        margen_neto_pct = (utilidad_neta / venta_bruta * 100) if venta_bruta > 0 else 0.0
        margen_bruto_pct = (utilidad_bruta_fruta / venta_bruta * 100) if venta_bruta > 0 else 0.0

        st.markdown(f"""
            <div class="kpi-grid">
                <div class="kpi-card kpi-venta">
                    <div class="kpi-top">
                        <span class="kpi-title">Venta Bruta</span>
                        <span class="kpi-badge">💰 Ingreso</span>
                    </div>
                    <div class="kpi-value">S/ {venta_bruta:,.0f}</div>
                    <div class="kpi-sub">100.0% facturación</div>
                </div>
                <div class="kpi-card kpi-precio">
                    <div class="kpi-top">
                        <span class="kpi-title">Costo Proveedor</span>
                        <span class="kpi-badge">🌱 COGS</span>
                    </div>
                    <div class="kpi-value">S/ {costo_mercaderia:,.0f}</div>
                    <div class="kpi-sub">{(costo_mercaderia/venta_bruta*100 if venta_bruta>0 else 0):.1f}% de la venta</div>
                </div>
                <div class="kpi-card kpi-danger">
                    <div class="kpi-top">
                        <span class="kpi-title">Devoluciones (DEV)</span>
                        <span class="kpi-badge">↩️ Pérdida</span>
                    </div>
                    <div class="kpi-value">S/ {impacto_devoluciones:,.0f}</div>
                    <div class="kpi-sub">{(impacto_devoluciones/venta_bruta*100 if venta_bruta>0 else 0):.2f}% de la venta</div>
                </div>
                <div class="kpi-card kpi-ordenes">
                    <div class="kpi-top">
                        <span class="kpi-title">Gastos Operativos</span>
                        <span class="kpi-badge">🧾 OpEx</span>
                    </div>
                    <div class="kpi-value">S/ {gastos_operativos:,.0f}</div>
                    <div class="kpi-sub">Lista factGastos</div>
                </div>
                <div class="kpi-card kpi-volumen">
                    <div class="kpi-top">
                        <span class="kpi-title">Utilidad Neta</span>
                        <span class="kpi-badge">📈 {margen_neto_pct:.1f}%</span>
                    </div>
                    <div class="kpi-value">S/ {utilidad_neta:,.0f}</div>
                    <div class="kpi-sub">Margen Fruta: <b>{margen_bruto_pct:.1f}%</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 1. FILA SUPERIOR: GRÁFICO DE CASCADA (WATERFALL) + MARGEN % POR PRODUCTO
        col_wf, col_mp = st.columns([1.25, 1])

        with col_wf:
            st.markdown('<div class="chart-header">🌊 Cascada de Resultados Financieros (S/)</div>', unsafe_allow_html=True)
            fig_wf = go.Figure(go.Waterfall(
                name="P&L KCO",
                orientation="v",
                measure=["absolute", "relative", "relative", "subtotal", "relative", "total"],
                x=["Venta Bruta", "Costo Proveedor", "Devoluciones", "Margen Fruta", "Gastos Op.", "Utilidad Neta"],
                textposition="outside",
                text=[
                    f"<b>S/ {venta_bruta:,.0f}</b>",
                    f"<b>-S/ {costo_mercaderia:,.0f}</b>",
                    f"<b>-S/ {impacto_devoluciones:,.0f}</b>",
                    f"<b>S/ {utilidad_bruta_fruta:,.0f}</b>",
                    f"<b>-S/ {gastos_operativos:,.0f}</b>",
                    f"<b>S/ {utilidad_neta:,.0f}</b>"
                ],
                textfont=dict(size=8.5, family="Arial"),
                y=[venta_bruta, -costo_mercaderia, -impacto_devoluciones, 0, -gastos_operativos, 0],
                connector={"line": {"color": "#94a3b8", "width": 1, "dash": "dot"}},
                increasing={"marker": {"color": "#10b981"}},
                decreasing={"marker": {"color": "#ef4444"}},
                totals={"marker": {"color": COLOR_PRIMARY}}
            ))
            fig_wf.update_layout(
                autosize=True,
                template='plotly_white',
                height=245,
                showlegend=False,
                yaxis=dict(title='Soles (S/)', titlefont=dict(size=9), tickfont=dict(size=8.5)),
                xaxis=dict(tickfont=dict(size=8.5)),
                margin=dict(t=22, b=20, l=8, r=8)
            )
            st.plotly_chart(fig_wf, use_container_width=True, config=PLOTLY_CONFIG)

        with col_mp:
            st.markdown('<div class="chart-header">🏷️ Margen Bruto % por Producto</div>', unsafe_allow_html=True)
            df_rent_v = df.groupby('DESCRIPCION_PRODUCTO').agg(
                KG_VENTA=('KILOS_SOLICITADOS', 'sum'),
                JABAS=('JABAS_EST', 'sum'),
                VENTA=('VALOR_COMERCIAL', 'sum'),
                COSTO=('INVERSION_COMPRA', 'sum')
            ).reset_index()

            df_rent_d = df_dev.groupby('DESCRIPCION_PRODUCTO').agg(
                COSTO_DEV=('COSTO_DEVOLUCION', 'sum')
            ).reset_index() if not df_dev.empty else pd.DataFrame(columns=['DESCRIPCION_PRODUCTO', 'COSTO_DEV'])

            df_rent = pd.merge(df_rent_v, df_rent_d, on='DESCRIPCION_PRODUCTO', how='left').fillna({'COSTO_DEV': 0.0})
            df_rent['UTILIDAD'] = df_rent['VENTA'] - df_rent['COSTO'] - df_rent['COSTO_DEV']
            df_rent['MARGEN_PCT'] = np.where(df_rent['VENTA'] > 0, (df_rent['UTILIDAD'] / df_rent['VENTA']) * 100, 0.0)
            df_rent['PRECIO_PROM'] = np.where(df_rent['KG_VENTA'] > 0, df_rent['VENTA'] / df_rent['KG_VENTA'], 0.0)
            df_rent['COSTO_PROM'] = np.where(df_rent['KG_VENTA'] > 0, df_rent['COSTO'] / df_rent['KG_VENTA'], 0.0)
            df_rent = df_rent.sort_values('MARGEN_PCT', ascending=True)

            fig_mp = go.Figure(go.Bar(
                x=df_rent['MARGEN_PCT'],
                y=df_rent['DESCRIPCION_PRODUCTO'],
                orientation='h',
                marker_color=[VARIEDAD_COLORS.get(p, COLOR_PRIMARY) for p in df_rent['DESCRIPCION_PRODUCTO']],
                text=df_rent.apply(lambda r: f"<b>{r['MARGEN_PCT']:.1f}%</b> (S/ {r['UTILIDAD']:,.0f})", axis=1),
                textposition='outside',
                cliponaxis=False,
                textfont=dict(size=8.5, color='#0f172a')
            ))
            fig_mp.update_layout(
                autosize=True,
                template='plotly_white',
                height=245,
                xaxis=dict(title='Margen %', titlefont=dict(size=9), tickfont=dict(size=8.5)),
                yaxis=dict(title='', tickfont=dict(size=8.5)),
                margin=dict(t=22, b=20, l=8, r=85)
            )
            st.plotly_chart(fig_mp, use_container_width=True, config=PLOTLY_CONFIG)

        # 2. FILA INFERIOR: EVOLUTIVO DEL MARGEN + TABLA DE RENTABILIDAD POR PRODUCTO
        col_ev, col_tbl = st.columns([1.15, 1.35])

        with col_ev:
            st.markdown(f'<div class="chart-header">📈 Evolutivo del Margen ({label_periodo})</div>', unsafe_allow_html=True)
            ev_v = df.groupby(col_periodo).agg(VENTA=('VALOR_COMERCIAL', 'sum'), COSTO=('INVERSION_COMPRA', 'sum')).reset_index()
            ev_d = df_dev.groupby(col_periodo).agg(COSTO_DEV=('COSTO_DEVOLUCION', 'sum')).reset_index() if not df_dev.empty else pd.DataFrame(columns=[col_periodo, 'COSTO_DEV'])
            ev_g = df_gastos_filtered.groupby(col_periodo).agg(GASTO=('MONTO', 'sum')).reset_index() if not df_gastos_filtered.empty else pd.DataFrame(columns=[col_periodo, 'GASTO'])

            df_ev_m = ev_v.merge(ev_d, on=col_periodo, how='left').merge(ev_g, on=col_periodo, how='left').fillna(0.0).sort_values(col_periodo)
            df_ev_m['UTILIDAD_NETA'] = df_ev_m['VENTA'] - df_ev_m['COSTO'] - df_ev_m['COSTO_DEV'] - df_ev_m['GASTO']
            df_ev_m['MARGEN_PCT'] = np.where(df_ev_m['VENTA'] > 0, (df_ev_m['UTILIDAD_NETA'] / df_ev_m['VENTA']) * 100, 0.0)

            fig_ev = go.Figure()
            fig_ev.add_trace(go.Bar(
                x=df_ev_m[col_periodo],
                y=df_ev_m['UTILIDAD_NETA'],
                name='Utilidad Neta (S/)',
                marker=dict(color=COLOR_BARRA_CLARA, line=dict(color=COLOR_BARRA_BORDE, width=1.1)),
                text=df_ev_m['UTILIDAD_NETA'].apply(lambda x: f"<b>S/{x:,.0f}</b>"),
                textposition='outside',
                cliponaxis=False,
                textfont=dict(size=8, color='#065f46'),
                yaxis='y'
            ))
            fig_ev.add_trace(go.Scatter(
                x=df_ev_m[col_periodo],
                y=df_ev_m['MARGEN_PCT'],
                name='Margen Neto %',
                mode='lines+markers+text',
                text=df_ev_m['MARGEN_PCT'].apply(lambda x: f"{x:.1f}%"),
                textposition='top center',
                textfont=dict(size=8, color='#9a3412'),
                line=dict(color=COLOR_ACCENT, width=2.4),
                marker=dict(size=6, color=COLOR_ACCENT),
                yaxis='y2'
            ))
            fig_ev.update_layout(
                autosize=True,
                template='plotly_white',
                height=230,
                xaxis=dict(title='', tickangle=-30 if periodo_seleccionado == "Semanal" else 0, tickfont=dict(size=8.5)),
                yaxis=dict(title='Utilidad (S/)', showgrid=False, titlefont=dict(size=9), tickfont=dict(size=8)),
                yaxis2=dict(title='Margen %', overlaying='y', side='right', showgrid=True, titlefont=dict(size=9), tickfont=dict(size=8)),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=8.5)),
                margin=dict(t=22, b=25, l=8, r=8)
            )
            st.plotly_chart(fig_ev, use_container_width=True, config=PLOTLY_CONFIG)

        with col_tbl:
            st.markdown('<div class="chart-header">📋 Tabla de Rentabilidad por Producto</div>', unsafe_allow_html=True)
            df_rent_tbl = df_rent.sort_values('UTILIDAD', ascending=False)[
                ['DESCRIPCION_PRODUCTO', 'KG_VENTA', 'PRECIO_PROM', 'COSTO_PROM', 'VENTA', 'COSTO', 'COSTO_DEV', 'UTILIDAD', 'MARGEN_PCT']
            ].copy()
            df_rent_tbl.columns = ['Producto', 'Kilos', 'P. Venta', 'C. Compra', 'Venta (S/)', 'Costo (S/)', 'Dev. (S/)', 'Utilidad (S/)', 'Margen %']
            st.dataframe(
                df_rent_tbl.style.format({
                    'Kilos': '{:,.0f}',
                    'P. Venta': 'S/ {:.2f}',
                    'C. Compra': 'S/ {:.2f}',
                    'Venta (S/)': 'S/ {:,.0f}',
                    'Costo (S/)': 'S/ {:,.0f}',
                    'Dev. (S/)': 'S/ {:,.0f}',
                    'Utilidad (S/)': 'S/ {:,.0f}',
                    'Margen %': '{:.1f}%'
                }).map(style_margin_pct, subset=['Margen %']),
                use_container_width=True, height=230, hide_index=True
            )

        # INSIGHT FINANCIERO EJECUTIVO
        top_rent = df_rent.sort_values('UTILIDAD', ascending=False).iloc[0]
        mejor_pct = df_rent.sort_values('MARGEN_PCT', ascending=False).iloc[0]
        st.markdown(f"""
            <div class="chart-insight">
                <div class="insight-title">💡 Diagnóstico Financiero & Rentabilidad:</div>
                • <b>Generador Principal de Caja:</b> <b>{top_rent['DESCRIPCION_PRODUCTO']}</b> aporta la mayor utilidad absoluta con <b>S/ {top_rent['UTILIDAD']:,.2f}</b>, mientras que <b>{mejor_pct['DESCRIPCION_PRODUCTO']}</b> logra el mayor margen porcentual (<b>{mejor_pct['MARGEN_PCT']:.1f}%</b>).<br>
                • <b>Estructura de Costos y Gastos:</b> El costo directo de fruta absorbe el <b>{(costo_mercaderia/venta_bruta*100 if venta_bruta>0 else 0):.1f}%</b> de la venta, las devoluciones representan <b>S/ {impacto_devoluciones:,.2f}</b> y los gastos operativos de <code>factGastos</code> suman <b>S/ {gastos_operativos:,.2f}</b>, dejando un margen neto consolidado de <b>{margen_neto_pct:.1f}%</b>.
            </div>
        """, unsafe_allow_html=True)

        # EXPANDER CON DESGLOSE DE GASTOS OPERATIVOS (factGastos)
        with st.expander("🧾 Ver detalle de Gastos Operativos (factGastos)", expanded=False):
            if df_gastos_filtered.empty:
                st.info("No hay gastos operativos registrados en factGastos para el periodo filtrado.")
            else:
                g_show = df_gastos_filtered.sort_values('FECHA_GASTO', ascending=False)[['FECHA_GASTO', 'TIPO_GASTO', 'DESCRIPCION', 'MONTO']].copy()
                g_show['FECHA_GASTO'] = g_show['FECHA_GASTO'].dt.strftime('%d/%m/%Y')
                g_show.columns = ['Fecha', 'Tipo de Gasto', 'Descripción', 'Monto (S/)']
                st.dataframe(
                    g_show.style.format({'Monto (S/)': 'S/ {:,.2f}'}),
                    use_container_width=True, height=200, hide_index=True
                )
