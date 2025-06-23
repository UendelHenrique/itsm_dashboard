import streamlit as st
import pandas as pd
import sys
import os

print("DEBUG: app.py carregado")

# Adiciona o diretório modules ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.data_processor import DataProcessor
from modules.visualizations import DashboardVisualizations
from config.settings import *

# Configuração da página
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Inicialização das classes
# @st.cache_resource # Removendo o cache para forçar a recarga das classes
def init_components():
    print("DEBUG: init_components chamado")
    processor = DataProcessor()
    visualizer = DashboardVisualizations()
    return processor, visualizer

processor, visualizer = init_components()

# Título principal
st.title("🎯 ITSM Dashboard - Análise de Chamados")
st.markdown("---")

# Sidebar para upload e filtros
st.sidebar.header("📁 Upload de Dados")

# Upload de arquivo
uploaded_file = st.sidebar.file_uploader(
    "Escolha um arquivo CSV",
    type=['csv'],
    help="Faça upload do arquivo CSV exportado do ITSM"
)

# Processamento do arquivo
if uploaded_file is not None:
    try:
        with st.spinner("Processando arquivo..."):
            print(f"DEBUG: Arquivo uploaded: {uploaded_file.name}")
            # Salva arquivo temporariamente
            temp_path = f"data/raw/temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Processa o arquivo
            df = processor.process_csv_file(temp_path)
            
            # Salva na base de dados
            processor.save_to_database(df)
            
            st.sidebar.success(f"✅ Arquivo processado com sucesso!")
            st.sidebar.info(f"📊 {len(df)} registros carregados")
            
            # Remove arquivo temporário
            os.remove(temp_path)
            
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao processar arquivo: {str(e)}")

# Carrega dados da base de dados
try:
    print("DEBUG: Carregando dados da base de dados")
    df = processor.load_from_database()
    
    if df.empty:
        st.warning("⚠️ Nenhum dado encontrado. Faça upload de um arquivo CSV para começar.")
        st.stop()
    
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    st.stop()

# Filtros na sidebar
st.sidebar.header("🔍 Filtros")

# Filtro por período - AGORA USA 'Data fechamento'
if 'Data fechamento' in df.columns:
    print("DEBUG: Aplicando filtro de data")
    df['Data fechamento'] = pd.to_datetime(df['Data fechamento'], errors='coerce')
    dates = df['Data fechamento'].dropna()
    
    if not dates.empty:
        min_date = dates.min().date()
        max_date = dates.max().date()
        
        date_range = st.sidebar.date_input(
            "Período (Data de Fechamento)",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            # Ajusta end_date para incluir o dia inteiro
            end_date_inclusive = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            df = df[
                (df['Data fechamento'] >= pd.to_datetime(start_date)) & 
                (df['Data fechamento'] <= end_date_inclusive)
            ]

# Filtro por categoria
if 'Categoria' in df.columns:
    print("DEBUG: Aplicando filtro de categoria")
    categories = ['Todas'] + sorted(df['Categoria'].dropna().unique().tolist())
    selected_category = st.sidebar.selectbox("Categoria", categories)
    
    if selected_category != 'Todas':
        df = df[df['Categoria'] == selected_category]

# Filtro por analista
if 'Analista Responsável' in df.columns:
    print("DEBUG: Aplicando filtro de analista")
    analysts = ['Todos'] + sorted(df['Analista Responsável'].dropna().unique().tolist())
    selected_analyst = st.sidebar.selectbox("Analista", analysts)
    
    if selected_analyst != 'Todos':
        df = df[df['Analista Responsável'] == selected_analyst]

# Filtro por status
if 'Flag Em Aberto' in df.columns:
    print("DEBUG: Aplicando filtro de status")
    status_options = ['Todos'] + sorted(df['Flag Em Aberto'].dropna().unique().tolist())
    selected_status = st.sidebar.selectbox("Status", status_options)
    
    if selected_status != 'Todos':
        df = df[df['Flag Em Aberto'] == selected_status]

# Calcula KPIs
print("DEBUG: Calculando KPIs")
kpis = processor.calculate_kpis(df)

# Exibe KPIs principais
st.header("📈 Indicadores Principais")
visualizer.create_kpi_cards(kpis)

st.markdown("---")

# Layout em colunas para gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Distribuição por Categoria")
    print("DEBUG: Criando gráfico de categoria")
    category_chart = visualizer.create_category_chart(df)
    if category_chart:
        st.plotly_chart(category_chart, use_container_width=True)
    else:
        st.info("Dados insuficientes para este gráfico")

with col2:
    st.subheader("⏰ Chamados por Período")
    print("DEBUG: Criando gráfico de timeline")
    timeline_chart = visualizer.create_timeline_chart(df)
    if timeline_chart:
        st.plotly_chart(timeline_chart, use_container_width=True)
    else:
        st.info("Dados insuficientes para este gráfico")

# Segunda linha de gráficos
col3, col4 = st.columns(2)

with col3:
    st.subheader("👥 Produtividade - Encerrados por Analista")
    print("DEBUG: Criando gráfico de performance do analista")
    analyst_chart = visualizer.create_analyst_performance_chart(df)
    if analyst_chart:
        st.plotly_chart(analyst_chart, use_container_width=True)
    else:
        st.info("Dados insuficientes para este gráfico")

with col4:
    st.subheader("🎯 Cumprimento de SLA")
    print("DEBUG: Criando gráfico de SLA")
    sla_chart = visualizer.create_sla_chart(df)
    if sla_chart:
        st.plotly_chart(sla_chart, use_container_width=True)
    else:
        st.info("Dados insuficientes para este gráfico")

# Terceira linha de gráficos
col5, col6 = st.columns(2)

with col5:
    st.subheader("⚡ Chamados por Prioridade")
    print("DEBUG: Criando gráfico de prioridade")
    priority_chart = visualizer.create_priority_chart(df)
    if priority_chart:
        st.plotly_chart(priority_chart, use_container_width=True)
    else:
        st.info("Dados insuficientes para este gráfico")

with col6:
    st.subheader("😊 Grau de Satisfação")
    print("DEBUG: Criando gráfico de satisfação")
    satisfaction_chart = visualizer.create_satisfaction_chart(df)
    if satisfaction_chart:
        st.plotly_chart(satisfaction_chart, use_container_width=True)
    else:
        st.info("Dados de satisfação não disponíveis")

# Nova seção: Produtividade Diária
st.markdown("---")
st.subheader("📈 Produtividade Diária por Analista")
print("DEBUG: Criando gráfico de produtividade diária do analista")
daily_productivity_chart = visualizer.create_analyst_daily_productivity(df)
if daily_productivity_chart:
    st.plotly_chart(daily_productivity_chart, use_container_width=True)
else:
    st.info("Dados insuficientes para este gráfico")

# Seção de tempo de resolução
st.subheader("⏱️ Distribuição do Tempo de Resolução")
print("DEBUG: Criando gráfico de tempo de resolução")
resolution_chart = visualizer.create_resolution_time_chart(df)
if resolution_chart:
    st.plotly_chart(resolution_chart, use_container_width=True)
else:
    st.info("Dados insuficientes para este gráfico")

# Tabela de dados detalhados
st.markdown("---")
st.header("📋 Dados Detalhados")

# Seleção de colunas para exibir
if not df.empty:
    all_columns = df.columns.tolist()
    default_columns = [
        'PK Dataset Chamados', 'Analista Responsável', 'Categoria', 
        'Data criação', 'Data fechamento', 'Status (descrição)' , 'Prioridade', 'Título requisição'
    ]
    
    # Filtra apenas colunas que existem no DataFrame
    available_default_columns = [col for col in default_columns if col in all_columns]
    
    selected_columns = st.multiselect(
        "Selecione as colunas para exibir:",
        all_columns,
        default=available_default_columns[:8]  # Limita a 8 colunas por padrão
    )
    
    if selected_columns:
        # Exibe tabela paginada
        page_size = 50
        total_rows = len(df)
        total_pages = (total_rows - 1) // page_size + 1
        
        if total_pages > 1:
            page = st.number_input(
                f"Página (1 a {total_pages})",
                min_value=1,
                max_value=total_pages,
                value=1
            )
            
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            
            st.write(f"Exibindo registros {start_idx + 1} a {end_idx} de {total_rows}")
            st.dataframe(df[selected_columns].iloc[start_idx:end_idx], use_container_width=True)
        else:
            st.dataframe(df[selected_columns], use_container_width=True)
    
    # Botão para download
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download dos dados filtrados (CSV)",
        data=csv,
        file_name=f"itsm_dados_filtrados_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# Informações do sistema
st.markdown("---")
with st.expander("ℹ️ Informações do Sistema"):
    stats = processor.get_summary_stats(df)
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.metric("Total de Registros", f"{stats.get('total_registros', 0):,}")
        st.metric("Categorias Únicas", stats.get('categorias_unicas', 0))
    
    with col_info2:
        st.metric("Analistas Únicos", stats.get('analistas_unicos', 0))
        st.metric("Grupos Solucionadores", stats.get('grupos_solucionadores', 0))
    
    with col_info3:
        if stats.get('periodo_inicio'):
            st.metric("Período Início", stats['periodo_inicio'])
        if stats.get('periodo_fim'):
            st.metric("Período Fim", stats['periodo_fim'])

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>ITSM Dashboard - Desenvolvido para análise de dados de chamados de TI</p>
    </div>
    """,
    unsafe_allow_html=True
)



