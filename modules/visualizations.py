import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from config.settings import COLORS, SLA_COLORS, PRIORITY_COLORS, SATISFACTION_COLORS

print("DEBUG: visualizations.py carregado")

class DashboardVisualizations:
    def create_kpi_cards(self, kpis):
        print("DEBUG: Criando cartões KPI")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Total de Chamados", value=f"{kpis.get(\"total_chamados\", 0):,}")
        with col2:
            st.metric(label="Chamados Abertos", value=f"{kpis.get(\"chamados_abertos\", 0):,}")
        with col3:
            st.metric(label="SLA Atendido", value=f"{kpis.get(\"sla_atendido_percent\", 0):.1f}%")
        with col4:
            st.metric(label="Tempo Médio (h)", value=f"{kpis.get(\"tempo_medio_resolucao\", 0):.1f}")

    def create_category_chart(self, df):
        print("DEBUG: Criando gráfico de categoria")
        if df.empty or "Categoria" not in df.columns:
            return None
        category_counts = df["Categoria"].value_counts().reset_index()
        category_counts.columns = ["Categoria", "Quantidade"]
        fig = px.pie(category_counts, values="Quantidade", names="Categoria", title="Distribuição por Categoria",
                     color="Categoria", color_discrete_map=COLORS)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        return fig

    def create_timeline_chart(self, df):
        print("DEBUG: Criando gráfico de timeline")
        if df.empty or "Data fechamento" not in df.columns:
            return None
        df_filtered = df.dropna(subset=["Data fechamento"])
        if df_filtered.empty:
            return None
        
        # Agrupar por dia e contar chamados
        daily_counts = df_filtered["Data fechamento"].dt.date.value_counts().sort_index().reset_index()
        daily_counts.columns = ["Data", "Quantidade"]
        
        fig = px.line(daily_counts, x="Data", y="Quantidade", title="Chamados por Dia")
        fig.update_xaxes(rangeslider_visible=True)
        return fig

    def create_analyst_performance_chart(self, df):
        print("DEBUG: Criando gráfico de performance do analista")
        if df.empty or "Analista Responsável" not in df.columns:
            return None
        analyst_counts = df["Analista Responsável"].value_counts().reset_index()
        analyst_counts.columns = ["Analista", "Chamados Encerrados"]
        fig = px.bar(analyst_counts.head(10), x="Analista", y="Chamados Encerrados", 
                     title="Top 10 Analistas por Chamados Encerrados",
                     color="Chamados Encerrados", color_continuous_scale=px.colors.sequential.Plasma)
        return fig

    def create_sla_chart(self, df):
        print("DEBUG: Criando gráfico de SLA")
        if df.empty or "SLA Atendido" not in df.columns:
            return None
        sla_counts = df["SLA Atendido"].value_counts(normalize=True).reset_index()
        sla_counts.columns = ["SLA Atendido", "Percentual"]
        sla_counts["Percentual"] = sla_counts["Percentual"] * 100
        fig = px.pie(sla_counts, values="Percentual", names="SLA Atendido", title="Cumprimento de SLA",
                     color="SLA Atendido", color_discrete_map=SLA_COLORS)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        return fig

    def create_priority_chart(self, df):
        print("DEBUG: Criando gráfico de prioridade")
        if df.empty or "Prioridade" not in df.columns:
            return None
        priority_order = ["P1", "P2", "P3", "P4"]
        priority_counts = df["Prioridade"].value_counts().reindex(priority_order).fillna(0).reset_index()
        priority_counts.columns = ["Prioridade", "Quantidade"]
        fig = px.bar(priority_counts, x="Prioridade", y="Quantidade", title="Chamados por Prioridade",
                     color="Prioridade", color_discrete_map=PRIORITY_COLORS)
        return fig

    def create_satisfaction_chart(self, df):
        print("DEBUG: Criando gráfico de satisfação")
        if df.empty or "Grau de Satisfação" not in df.columns:
            return None
        satisfaction_order = ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo"]
        satisfaction_counts = df["Grau de Satisfação"].value_counts().reindex(satisfaction_order).fillna(0).reset_index()
        satisfaction_counts.columns = ["Grau de Satisfação", "Quantidade"]
        fig = px.bar(satisfaction_counts, x="Grau de Satisfação", y="Quantidade", title="Grau de Satisfação",
                     color="Grau de Satisfação", color_discrete_map=SATISFACTION_COLORS)
        return fig

    def create_analyst_daily_productivity(self, df):
        print("DEBUG: Criando gráfico de produtividade diária do analista")
        if df.empty or "Data fechamento" not in df.columns or "Analista Responsável" not in df.columns:
            return None
        
        df_filtered = df.dropna(subset=["Data fechamento", "Analista Responsável"])
        if df_filtered.empty:
            return None

        daily_productivity = df_filtered.groupby([df_filtered["Data fechamento"].dt.date, "Analista Responsável"]).size().reset_index(name="Chamados Encerrados")
        daily_productivity.columns = ["Data", "Analista Responsável", "Chamados Encerrados"]
        
        fig = px.line(daily_productivity, x="Data", y="Chamados Encerrados", color="Analista Responsável",
                      title="Produtividade Diária por Analista")
        fig.update_xaxes(rangeslider_visible=True)
        return fig

    def create_resolution_time_chart(self, df):
        print("DEBUG: Criando gráfico de tempo de resolução")
        if df.empty or "Tempo de Resolução (horas)" not in df.columns:
            return None
        
        fig = px.histogram(df, x="Tempo de Resolução (horas)", nbins=20, title="Distribuição do Tempo de Resolução (horas)")
        fig.update_layout(xaxis_title="Tempo de Resolução (horas)", yaxis_title="Número de Chamados")
        return fig


