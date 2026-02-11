"""
DASHBOARD INTERATIVO - MÉTRICAS ÁGEIS JIRA
==========================================

Este script cria um dashboard interativo para acompanhamento de métricas ágeis.
Pode ser executado em plataformas gratuitas como Streamlit Cloud, Render, ou Railway.

Autor: Claude - Analista de Dados Ágil
Data: 2026-02-11
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# ============================
# CONFIGURAÇÃO DA PÁGINA
# ============================
st.set_page_config(
    page_title="Dashboard Ágil - TF Serviços & Payments",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# FUNÇÕES DE CARREGAMENTO
# ============================
@st.cache_data
def load_data(uploaded_file=None):
    """Carrega e processa dados do Jira"""
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
    else:
        # Dados de exemplo para demonstração
        st.warning("⚠️ Usando dados de exemplo. Faça upload do seu CSV do Jira na barra lateral.")
        return None
    
    # Processar datas
    df['Created'] = pd.to_datetime(df['Created'], format='%d/%b/%y %H:%M', errors='coerce')
    df['Updated'] = pd.to_datetime(df['Updated'], format='%d/%b/%y %H:%M', errors='coerce')
    df['Resolved'] = pd.to_datetime(df['Resolved'], format='%d/%b/%y %H:%M', errors='coerce')
    
    # Calcular Lead Time
    resolved_df = df[df['Resolved'].notna()].copy()
    resolved_df['Lead_Time_Days'] = (resolved_df['Resolved'] - resolved_df['Created']).dt.total_seconds() / 86400
    
    # Categorizar tipos
    df['Categoria'] = df['Issue Type'].apply(lambda x: 
        'Histórias' if x == 'História' else 
        'Bugs' if 'Bug' in str(x) else 
        'Outros'
    )
    
    return df, resolved_df

# ============================
# SIDEBAR - FILTROS
# ============================
st.sidebar.header("📁 Upload de Dados")
uploaded_file = st.sidebar.file_uploader(
    "Faça upload do CSV exportado do Jira",
    type=['csv'],
    help="Exporte seu relatório do Jira como CSV e faça upload aqui"
)

result = load_data(uploaded_file)
if result is None:
    st.title("📊 Dashboard de Métricas Ágeis")
    st.info("👈 Faça upload do seu arquivo CSV do Jira na barra lateral para começar!")
    st.stop()

df, resolved_df = result

st.sidebar.header("🔍 Filtros")

# Filtro de período
min_date = df['Created'].min().date()
max_date = df['Created'].max().date()
date_range = st.sidebar.date_input(
    "Período",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Filtro de status
status_options = ['Todos'] + list(df['Status'].unique())
selected_status = st.sidebar.multiselect(
    "Status",
    options=status_options,
    default=['Todos']
)

# Filtro de tipo
tipo_options = ['Todos'] + list(df['Categoria'].unique())
selected_tipo = st.sidebar.multiselect(
    "Tipo de Issue",
    options=tipo_options,
    default=['Todos']
)

# Aplicar filtros
df_filtered = df.copy()
if len(date_range) == 2:
    df_filtered = df_filtered[
        (df_filtered['Created'].dt.date >= date_range[0]) &
        (df_filtered['Created'].dt.date <= date_range[1])
    ]

if 'Todos' not in selected_status and selected_status:
    df_filtered = df_filtered[df_filtered['Status'].isin(selected_status)]

if 'Todos' not in selected_tipo and selected_tipo:
    df_filtered = df_filtered[df_filtered['Categoria'].isin(selected_tipo)]

# ============================
# HEADER
# ============================
st.title("📊 Dashboard de Métricas Ágeis")
st.markdown("### Squad TF Serviços & Payments")
st.markdown("---")

# ============================
# MÉTRICAS PRINCIPAIS (KPIs)
# ============================
col1, col2, col3, col4, col5 = st.columns(5)

total_issues = len(df_filtered)
done_issues = len(df_filtered[df_filtered['Status'] == 'Done'])
completion_rate = (done_issues / total_issues * 100) if total_issues > 0 else 0

historias = len(df_filtered[df_filtered['Categoria'] == 'Histórias'])
bugs = len(df_filtered[df_filtered['Categoria'] == 'Bugs'])
ratio_valor_divida = historias / bugs if bugs > 0 else 0

lead_time_median = resolved_df['Lead_Time_Days'].median() if len(resolved_df) > 0 else 0

wip = len(df_filtered[~df_filtered['Status'].isin(['Done', 'Canceled', 'Cancelado'])])

with col1:
    st.metric(
        label="📈 Taxa de Conclusão",
        value=f"{completion_rate:.1f}%",
        delta=f"{done_issues}/{total_issues} issues"
    )

with col2:
    st.metric(
        label="⏱️ Lead Time (mediana)",
        value=f"{lead_time_median:.1f} dias",
        delta="✅ Excelente" if lead_time_median < 10 else "🟡 Regular"
    )

with col3:
    st.metric(
        label="⚖️ Razão Valor/Dívida",
        value=f"{ratio_valor_divida:.2f}",
        delta="Meta: >2.0"
    )

with col4:
    st.metric(
        label="🐛 Taxa de Bugs",
        value=f"{(bugs/total_issues*100):.1f}%",
        delta=f"{bugs} bugs"
    )

with col5:
    st.metric(
        label="🎯 WIP Atual",
        value=f"{wip}",
        delta="issues em progresso"
    )

st.markdown("---")

# ============================
# GRÁFICOS - LINHA 1
# ============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Composição do Trabalho")
    
    categoria_counts = df_filtered['Categoria'].value_counts()
    fig = px.pie(
        values=categoria_counts.values,
        names=categoria_counts.index,
        color_discrete_sequence=['#3498db', '#e74c3c', '#95a5a6'],
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📈 Status das Issues")
    
    status_counts = df_filtered['Status'].value_counts()
    colors = ['#2ecc71' if 'Done' in x else '#e74c3c' if 'Cancel' in x else '#3498db' 
              for x in status_counts.index]
    
    fig = go.Figure(data=[go.Bar(
        x=status_counts.values,
        y=status_counts.index,
        orientation='h',
        marker_color=colors,
        text=status_counts.values,
        textposition='auto'
    )])
    fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

# ============================
# GRÁFICOS - LINHA 2
# ============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Throughput Mensal")
    
    df_filtered['Month'] = df_filtered['Created'].dt.to_period('M').astype(str)
    monthly_counts = df_filtered.groupby('Month').size().reset_index(name='Count')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_counts['Month'],
        y=monthly_counts['Count'],
        marker_color='#3498db',
        name='Issues Criadas'
    ))
    fig.add_trace(go.Scatter(
        x=monthly_counts['Month'],
        y=monthly_counts['Count'],
        mode='lines+markers',
        marker_color='#2c3e50',
        line=dict(width=2),
        name='Tendência'
    ))
    fig.update_layout(height=400, xaxis_title="Mês", yaxis_title="Issues")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("⏱️ Distribuição de Lead Time")
    
    if len(resolved_df) > 0:
        fig = go.Figure()
        fig.add_trace(go.Box(
            y=resolved_df['Lead_Time_Days'],
            name='Lead Time',
            marker_color='#3498db',
            boxmean='sd'
        ))
        fig.add_hline(y=10, line_dash="dash", line_color="green", 
                     annotation_text="Meta: 10 dias")
        fig.update_layout(height=400, yaxis_title="Dias")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de Lead Time disponíveis")

# ============================
# GRÁFICOS - LINHA 3
# ============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("👥 Top Assignees")
    
    assignee_counts = df_filtered['Assignee'].value_counts().head(10)
    
    # Calcular done vs in progress
    assignee_done = []
    assignee_progress = []
    for assignee in assignee_counts.index:
        done = len(df_filtered[(df_filtered['Assignee'] == assignee) & 
                                (df_filtered['Status'] == 'Done')])
        progress = len(df_filtered[(df_filtered['Assignee'] == assignee) & 
                                   (df_filtered['Status'] != 'Done')])
        assignee_done.append(done)
        assignee_progress.append(progress)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[name.split()[0][:15] for name in assignee_counts.index],
        x=assignee_done,
        name='Concluídas',
        orientation='h',
        marker_color='#2ecc71'
    ))
    fig.add_trace(go.Bar(
        y=[name.split()[0][:15] for name in assignee_counts.index],
        x=assignee_progress,
        name='Em Progresso',
        orientation='h',
        marker_color='#3498db'
    ))
    fig.update_layout(height=400, barmode='stack')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🎯 Prioridades")
    
    priority_counts = df_filtered['Priority'].value_counts()
    priority_colors = {
        'Low': '#2ecc71',
        'Medium': '#f39c12',
        'High': '#e67e22',
        'Highest': '#e74c3c'
    }
    colors = [priority_colors.get(p, '#95a5a6') for p in priority_counts.index]
    
    fig = go.Figure(data=[go.Pie(
        labels=priority_counts.index,
        values=priority_counts.values,
        marker_colors=colors
    )])
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# ============================
# GRÁFICO - CUMULATIVE FLOW
# ============================
st.subheader("📈 Cumulative Flow Diagram")

df_sorted = df_filtered.sort_values('Created').reset_index(drop=True)
df_sorted['Cumulative_Total'] = range(1, len(df_sorted) + 1)
df_sorted['Cumulative_Done'] = (df_sorted['Status'] == 'Done').cumsum()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_sorted.index,
    y=df_sorted['Cumulative_Total'],
    fill='tozeroy',
    name='Total Criadas',
    line_color='#3498db',
    fillcolor='rgba(52, 152, 219, 0.3)'
))
fig.add_trace(go.Scatter(
    x=df_sorted.index,
    y=df_sorted['Cumulative_Done'],
    name='Concluídas',
    line_color='#2ecc71',
    line=dict(width=3)
))
fig.update_layout(height=400, xaxis_title="Issues", yaxis_title="Quantidade Acumulada")
st.plotly_chart(fig, use_container_width=True)

# ============================
# TABELA DE DADOS
# ============================
st.markdown("---")
st.subheader("📋 Dados Detalhados")

columns_to_show = ['Issue key', 'Summary', 'Issue Type', 'Status', 'Priority', 
                   'Assignee', 'Created', 'Resolved']
available_columns = [col for col in columns_to_show if col in df_filtered.columns]

st.dataframe(
    df_filtered[available_columns].sort_values('Created', ascending=False),
    use_container_width=True,
    height=400
)

# ============================
# DOWNLOAD
# ============================
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download CSV Filtrado",
        data=csv,
        file_name=f"jira_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

with col2:
    st.info(f"📊 Total de {total_issues} issues no período selecionado")

with col3:
    st.success(f"✅ Dashboard atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ============================
# FOOTER
# ============================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d;'>
    <p>Dashboard desenvolvido com Streamlit • Dados do Jira</p>
    <p>📊 Analista de Dados Ágil • © 2026</p>
</div>
""", unsafe_allow_html=True)
