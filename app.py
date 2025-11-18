import streamlit as st
import pandas as pd
import numpy as np

# --- Configuración de la página ---
# Establece el título de la pestaña, el icono y el modo de diseño (wide utiliza todo el ancho).
st.set_page_config(
    page_title="Dashboard de Vendedores",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Nombre del archivo de datos (DEBE COINCIDIR con el archivo cargado) ---
VENDEDORES_FILE = "vendedores.csv"

# --- Función para cargar y limpiar datos (cacheada para eficiencia) ---
@st.cache_data
def load_data():
    """Carga el archivo CSV, limpia nombres de columnas y convierte tipos de datos."""
    try:
        # 1. Cargar el archivo CSV
        df = pd.read_csv(VENDEDORES_FILE, encoding='utf-8')
        
        # 2. Limpieza de columnas: eliminar espacios y usar mayúsculas
        df.columns = [col.strip().upper().replace(' ', '_') for col in df.columns]

        # 3. Conversión de tipos de datos a numérico
        df['UNIDADES_VENDIDAS'] = pd.to_numeric(df['UNIDADES_VENDIDAS'], errors='coerce')
        df['VENTAS_TOTALES'] = pd.to_numeric(df['VENTAS_TOTALES'], errors='coerce')
        df['PORCENTAJE_DE_VENTAS'] = pd.to_numeric(df['PORCENTAJE_DE_VENTAS'], errors='coerce')
        df['SALARIO'] = pd.to_numeric(df['SALARIO'], errors='coerce')
        
        # 4. Crear columna de nombre completo para filtros
        df['VENDEDOR'] = df['NOMBRE'].astype(str) + ' ' + df['APELLIDO'].astype(str)
        
        # 5. Eliminar filas con valores nulos en las métricas clave
        df.dropna(subset=['UNIDADES_VENDIDAS', 'VENTAS_TOTALES', 'PORCENTAJE_DE_VENTAS'], inplace=True)
        
        return df
    except FileNotFoundError:
        st.error(f"¡Error! No se encontró el archivo de datos: {VENDEDORES_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocurrió un error al cargar o procesar los datos: {e}")
        return pd.DataFrame()

# --- Cargar datos ---
df = load_data()

if not df.empty:
    
    # =========================================================================
    # --- BARRA LATERAL (Sidebar) para Filtros ---
    # =========================================================================
    st.sidebar.header("Opciones de Filtrado")

    # 1. Filtro por Región (Multiselect)
    all_regions = ['TODAS'] + sorted(df['REGION'].unique().tolist())
    selected_regions = st.sidebar.multiselect(
        "Selecciona una o varias Regiones:",
        options=all_regions,
        default=['TODAS'],
    )
    
    # Aplicar filtro de región
    if 'TODAS' in selected_regions:
        df_filtered_region = df.copy()
    else:
        df_filtered_region = df[df['REGION'].isin(selected_regions)]

    # 2. Selector de Vendedor Específico (Selectbox)
    all_sellers = sorted(df_filtered_region['VENDEDOR'].unique().tolist())
    selected_seller = st.sidebar.selectbox(
        "Ver datos de Vendedor Específico:",
        options=['Selecciona un vendedor...'] + all_sellers,
    )

    # --- Títulos y Contenedores Principales ---
    st.title("📈 Dashboard de Análisis de Vendedores")
    st.markdown("Utiliza la barra lateral para filtrar por región y ver el detalle de un vendedor.")
    
    # --- PESTAÑAS (Tabs) para organizar el contenido ---
    tab_dashboard, tab_detail, tab_data = st.tabs(["📊 Resumen y Gráficas", "👤 Detalle del Vendedor", "📋 Tabla Filtrada"])

    with tab_dashboard:
        st.header("Análisis de Desempeño por Región")
        st.markdown(f"**Regiones Incluidas:** `{', '.join(selected_regions)}`")

        # 1. Calcular métricas resumen
        total_ventas = df_filtered_region['VENTAS_TOTALES'].sum()
        total_unidades = df_filtered_region['UNIDADES_VENDIDAS'].sum()
        num_vendedores = df_filtered_region['ID'].nunique()

        # Mostrar KPIs en Columnas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Ventas Totales Filtro (USD)", value=f"${total_ventas:,.0f}")
        
        with col2:
            st.metric(label="Unidades Totales Vendidas", value=f"{total_unidades:,}")
            
        with col3:
             # Identificar al vendedor con mayor venta en el conjunto filtrado
             if not df_filtered_region.empty:
                 max_sales_row = df_filtered_region.loc[df_filtered_region['VENTAS_TOTALES'].idxmax()]
                 st.metric(
                     label="Vendedor con Mayor Venta",
                     value=max_sales_row['VENDEDOR'],
                     delta=f"${max_sales_row['VENTAS_TOTALES']:,.0f}",
                 )
             else:
                 st.metric(label="Vendedor con Mayor Venta", value="N/A", delta="N/A")

        st.markdown("---")
        st.subheader("Gráficas de Desempeño")

        # 2. Agrupar por Región para las gráficas
        df_grouped_region = df_filtered_region.groupby('REGION').agg(
            Total_Unidades=('UNIDADES_VENDIDAS', 'sum'),
            Total_Ventas=('VENTAS_TOTALES', 'sum'),
            Promedio_Porcentaje=('PORCENTAJE_DE_VENTAS', 'mean')
        ).reset_index()

        col_chart_1, col_chart_2 = st.columns(2)

        # Gráfica de Unidades Vendidas
        with col_chart_1:
            st.markdown("##### Unidades Vendidas por Región")
            st.bar_chart(df_grouped_region, x='REGION', y='Total_Unidades', color="#4a7c59")

        # Gráfica de Ventas Totales
        with col_chart_2:
            st.markdown("##### Ventas Totales por Región")
            st.bar_chart(df_grouped_region, x='REGION', y='Total_Ventas', color="#1f77b4")
            
        # Gráfica de Porcentajes de Ventas (Contribución Individual)
        st.markdown("##### Top 10 Vendedores por Contribución (Porcentaje de Ventas)")
        
        # Seleccionar top 10 vendedores para esta métrica
        df_top_sellers = df_filtered_region.sort_values(by='PORCENTAJE_DE_VENTAS', ascending=False).head(10)
        
        st.bar_chart(
            df_top_sellers, 
            x='VENDEDOR', 
            y='PORCENTAJE_DE_VENTAS', 
            color="#d62728",
            height=300
        )
        st.caption("Muestra la contribución del porcentaje de ventas individual para el Top 10 de vendedores.")


   
    with tab_detail:
        if selected_seller != 'Selecciona un vendedor...':
            # Filtrar los datos del vendedor seleccionado
            seller_data = df_filtered_region[df_filtered_region['VENDEDOR'] == selected_seller].iloc[0]
            
            st.header(f"👤 Datos Detallados de {selected_seller}")
            
            col_info, col_metrics = st.columns([1, 2])
            
            with col_info:
                st.subheader("Información Básica")
                st.info(f"ID: **{seller_data['ID']}**")
                st.info(f"Región: **{seller_data['REGION']}**")
                st.info(f"Salario: **${seller_data['SALARIO']:,.0f} USD**")
                
            with col_metrics:
                st.subheader("Métricas de Desempeño")
                
                # Métricas principales
                metric_container = st.container(border=True)
                m_col1, m_col2, m_col3 = metric_container.columns(3)
                
                m_col1.metric("Unidades Vendidas", f"{seller_data['UNIDADES_VENDIDAS']:,.0f}")
                m_col2.metric("Ventas Totales", f"${seller_data['VENTAS_TOTALES']:,.0f}")
                
                # Usa st.progress para el porcentaje de ventas
                st.markdown("##### Progreso de Porcentaje de Ventas")
                st.progress(seller_data['PORCENTAJE_DE_VENTAS'], text=f"{seller_data['PORCENTAJE_DE_VENTAS'] * 100:.2f}% de Contribución")

        else:
            st.info("Por favor, selecciona un vendedor en la barra lateral izquierda para ver su detalle de desempeño.")

   
    with tab_data:
        st.header("Tabla Interactiva de Datos Filtrados")
        st.info("Utiliza los filtros de la barra lateral. Haz clic en los encabezados para ordenar.")

        # Seleccionar y renombrar columnas para una mejor presentación
        columns_to_display = {
            'REGION': 'Región',
            'VENDEDOR': 'Nombre Completo', 
            'ID': 'ID Vendedor', 
            'SALARIO': 'Salario (USD)', 
            'UNIDADES_VENDIDAS': 'Unidades Vendidas', 
            'VENTAS_TOTALES': 'Ventas Totales (USD)', 
            'PORCENTAJE_DE_VENTAS': 'Porcentaje de Ventas'
        }
        df_display = df_filtered_region.rename(columns=columns_to_display)[list(columns_to_display.values())]
        
        # Mostrar el DataFrame con formato numérico
        st.dataframe(
            df_display, 
            use_container_width=True,
            column_config={
                "Salario (USD)": st.column_config.NumberColumn(format="$,.0f"),
                "Ventas Totales (USD)": st.column_config.NumberColumn(format="$,.0f"),
                "Porcentaje de Ventas": st.column_config.NumberColumn(format="%.4f")
            }
        )

# --- Pie de página si el DataFrame está vacío ---
else:
    st.error("No se pudieron cargar los datos. Por favor, verifica el nombre del archivo 'vendedores.csv' y su contenido.")