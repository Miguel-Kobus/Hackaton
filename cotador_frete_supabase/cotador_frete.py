
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import datetime
from utils.supabase_client import supabase
from utils.login import autenticar_usuario
from utils.geolocalizacao import calcular_distancia_km

# Configuração da página
st.set_page_config(
    page_title="Cotador de Frete",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Carregar CSS personalizado
with open('assets/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Autenticação
usuario = autenticar_usuario()
if not usuario:
    st.stop()

# Carregar dados históricos da tabela 'cotacoes_frete'
@st.cache_data
def carregar_dados():
    resp = supabase.table("cotacoes_frete").select("*").execute()
    df = pd.DataFrame(resp.data)
    df["valor_frete"] = df["valor_frete"].astype(float)
    df["data_cotacao"] = pd.to_datetime(df["data_cotacao"], errors="coerce")
    
    # Calcular distância para cotações sem distância
    sem_distancia = df[pd.isna(df["distancia_km"]) | (df["distancia_km"] == 0)]
    for index, row in sem_distancia.iterrows():
        origem = row["origem_cidade"]
        destino = row["destino_cidade"]
        distancia = calcular_distancia_km(origem, destino)
        if distancia:
            supabase.table("cotacoes_frete").update({"distancia_km": distancia}).eq("id_cotacao", row["id_cotacao"]).execute()
    
    # Recarregar dados com distâncias atualizadas
    resp = supabase.table("cotacoes_frete").select("*").execute()
    df = pd.DataFrame(resp.data)
    df["valor_frete"] = df["valor_frete"].astype(float)
    df["data_cotacao"] = pd.to_datetime(df["data_cotacao"], errors="coerce")
    
    return df.dropna(subset=["data_cotacao"])

def estimar_frete(df, origem, destino, tipo_carga, peso, modalidade):
    filtro = (
        (df["origem_cidade"] == origem)
        & (df["destino_cidade"] == destino)
        & (df["tipo_carga"] == tipo_carga)
        & (df["modalidade"] == modalidade)
    )
    similares = df[filtro]
    
    if similares.empty:
        return None, None, None, None
    
    # 1. Peso baseado na média ponderada dos últimos 6 meses
    data_atual = pd.Timestamp.now()
    seis_meses = data_atual - pd.DateOffset(months=6)
    
    # Adicionar peso para dados mais recentes
    similares['peso_temporal'] = 1 + (data_atual - similares['data_cotacao']).dt.days / 180
    
    # Calcular médias ponderadas
    media_valor_kg = ((similares['valor_frete'] / similares['peso_kg']) * similares['peso_temporal']).sum() / similares['peso_temporal'].sum()
    prazo = (similares['prazo_entrega_dias'] * similares['peso_temporal']).sum() / similares['peso_temporal'].sum()
    
    # 2. Ajuste sazonal (exemplo: alta temporada)
    mes_atual = data_atual.month
    alta_temporada = [11, 12, 1, 2]  # Dezembro, Janeiro, Fevereiro
    if mes_atual in alta_temporada:
        media_valor_kg *= 1.15  # Aumento de 15% na alta temporada
    
    # 3. Ajuste por distância
    # Aqui você pode implementar uma API de distância ou uma tabela de distância entre cidades
    # Por enquanto, usaremos um fator de ajuste baseado na média de distância
    distancia_media = similares['distancia_km'].mean()
    if pd.notna(distancia_media):
        media_valor_kg *= 1 + (distancia_media / 1000) * 0.05  # Ajuste de 5% por cada 1000km
    
    # 4. Cálculo final
    estimativa = media_valor_kg * peso
    
    # 5. Seleção da transportadora
    # Considera a transportadora mais frequente nos últimos 3 meses
    tres_meses = data_atual - pd.DateOffset(months=3)
    recentes = similares[similares['data_cotacao'] >= tres_meses]
    if not recentes.empty:
        transportadora = recentes['transportadora'].mode().iloc[0]
    else:
        transportadora = similares['transportadora'].mode().iloc[0]
    
    # 6. Intervalo de confiança
    desvio_padrao = (similares['valor_frete'] / similares['peso_kg']).std()
    intervalo_confianca = 1.96 * desvio_padrao / len(similares)**0.5
    
    return (
        round(estimativa, 2),
        round(prazo),
        transportadora,
        similares,
        {
            'intervalo_confianca': round(intervalo_confianca * peso, 2),
            'n_amostras': len(similares),
            'periodo': f"{seis_meses.strftime('%Y-%m')} até {data_atual.strftime('%Y-%m')}",
            'distancia_media': round(distancia_media, 2) if pd.notna(distancia_media) else None
        }
    )

# Carregar dados
with st.spinner('Carregando dados históricos...'):
    df = carregar_dados()

# Cabeçalho com animação
st.markdown("""
<div style="text-align: center; padding: 20px 0;">    
    <h1 style="font-size: 3rem; margin-bottom: 10px;">🚚 Cotador de Frete</h1>
    <p style="font-size: 1.2rem; color: #64748b; margin-bottom: 30px;">Sistema inteligente para estimativa de fretes com base em dados históricos</p>
</div>
""", unsafe_allow_html=True)

# Container principal
with st.container():
    # Dados da cotação em um card
    st.markdown("""<div class="icon">📋</div> <span style="font-size: 1.3rem; font-weight: 600;">Dados da Cotação</span>""", unsafe_allow_html=True)
    
    # Layout em colunas com espaçamento adequado
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        origem = st.selectbox(
            "Cidade de Origem", 
            options=sorted(df["origem_cidade"].unique()),
            help="Selecione a cidade de origem da carga"
        )
    
    with col2:
        destino = st.selectbox(
            "Cidade de Destino", 
            options=sorted(df["destino_cidade"].unique()),
            help="Selecione a cidade de destino da carga"
        )
    
    with col3:
        tipo_carga = st.selectbox(
            "Tipo de Carga", 
            options=sorted(df["tipo_carga"].unique()),
            help="Selecione o tipo de carga a ser transportada"
        )
    
    col4, col5 = st.columns([1, 1])
    
    with col4:
        peso = st.number_input(
            "Peso (kg)", 
            min_value=1, 
            max_value=20000, 
            value=1000,
            help="Informe o peso da carga em quilogramas"
        )
    
    with col5:
        modalidade = st.selectbox(
            "Modalidade", 
            options=sorted(df["modalidade"].unique()),
            help="Selecione a modalidade de transporte"
        )
    
    # Adicionar linha separadora
    st.markdown("<hr style='margin: 30px 0; opacity: 0.2;'>", unsafe_allow_html=True)

# Botão de calcular com estilo e feedback visual
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
with btn_col2:
    calcular = st.button("Calcular Cotação", use_container_width=True)

if calcular:
    # Efeito de carregamento
    with st.spinner('Calculando a melhor cotação para você...'):
        # Simular processamento (opcional)
        time.sleep(0.8)
        
        # Calcular cotação
        valor, prazo, transportadora, similares, metricas = estimar_frete(df, origem, destino, tipo_carga, peso, modalidade)
    
    if valor is not None:
        # Container de resultado com estilo personalizado
        st.markdown('<div class="resultado-cotacao">', unsafe_allow_html=True)
        
        # Título do resultado
        st.markdown("<h2 style='text-align: center; margin-bottom: 25px; color: #1e40af;'>Resultado da Cotação</h2>", unsafe_allow_html=True)
        
        # Valores principais em cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
                <div style="font-size: 2.5rem; font-weight: 700; color: #2563eb; margin-bottom: 10px;">💰</div>
                <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: #64748b; margin-bottom: 5px;">Valor Estimado</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #0f172a;">R$ {valor:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
                <div style="font-size: 2.5rem; font-weight: 700; color: #2563eb; margin-bottom: 10px;">🗓️</div>
                <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: #64748b; margin-bottom: 5px;">Prazo de Entrega</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #0f172a;">{prazo} dias</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 15px; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
                <div style="font-size: 2.5rem; font-weight: 700; color: #2563eb; margin-bottom: 10px;">🚚</div>
                <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: #64748b; margin-bottom: 5px;">Transportadora</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #0f172a;">{transportadora}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Informações adicionais
        st.markdown("<h3 style='margin-top: 30px; margin-bottom: 15px; font-size: 1.2rem;'>Informações Adicionais</h3>", unsafe_allow_html=True)
        
        # Métricas em formato de grid
        col1, col2 = st.columns(2)
        
        col1.metric(
            "Intervalo de Confiança", 
            f"± R$ {metricas['intervalo_confianca']:,.2f}",
            help="Margem de erro da estimativa com 95% de confiança"
        )
        
        col2.metric(
            "Nº de Amostras", 
            metricas['n_amostras'],
            help="Quantidade de cotações similares utilizadas para o cálculo"
        )

        col3, col4 = st.columns(2)
        
        col3.metric(
            "Distância Média", 
            f"{metricas['distancia_media']:.0f} km" if metricas['distancia_media'] else "Não disponível",
            help="Distância média entre origem e destino"
        )
        
        col4.metric(
            "Período Analisado", 
            metricas['periodo'],
            help="Período considerado para análise dos dados históricos"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Registrar cotação no banco de dados
        cotacao = {
            "usuario": usuario,
            "origem": origem,
            "destino": destino,
            "tipo_carga": tipo_carga,
            "peso": peso,
            "modalidade": modalidade,
            "transportadora": transportadora,
            "valor": valor,
            "prazo": prazo,
            "n_amostras": metricas['n_amostras'],
            "periodo_analise": metricas['periodo'],
            "data_cotacao": datetime.datetime.now().isoformat()
        }
        
        with st.spinner('Salvando cotação...'):
            supabase.table("cotacoes_realizadas").insert(cotacao).execute()
        
        # Seção de gráficos com tabs para diferentes visualizações
        st.markdown("<hr style='margin: 30px 0; opacity: 0.2;'>", unsafe_allow_html=True)
        st.markdown("""<div class="icon">📈</div> <span style="font-size: 1.3rem; font-weight: 600;">Análise Histórica</span>""", unsafe_allow_html=True)
        
        # Criar tabs para diferentes visualizações
        tab1, tab2 = st.tabs(["Evolução de Preços", "Análise Detalhada"])
        
        with tab1:
            # Preparar dados para o gráfico
            grafico = similares.sort_values("data_cotacao")
            
            # Gráfico com Plotly (mais interativo e bonito)
            fig = px.line(
                grafico, 
                x="data_cotacao", 
                y="valor_frete",
                markers=True,
                title=f"Evolução dos Valores de Frete: {origem} → {destino}",
                labels={
                    "data_cotacao": "Data da Cotação",
                    "valor_frete": "Valor do Frete (R$)"
                },
                template="plotly_white"
            )
            
            # Personalizar o gráfico
            fig.update_traces(line=dict(color='#2563eb', width=3), marker=dict(size=8, color='#1e40af'))
            fig.update_layout(
                title_font=dict(size=20, color='#1e40af'),
                xaxis_title_font=dict(size=14),
                yaxis_title_font=dict(size=14),
                hoverlabel=dict(bgcolor="white", font_size=14),
                height=500
            )
            
            # Exibir o gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Adicionar insights sobre a evolução dos preços
            if len(grafico) > 1:
                variacao = ((grafico['valor_frete'].iloc[-1] - grafico['valor_frete'].iloc[0]) / grafico['valor_frete'].iloc[0]) * 100
                periodo = (grafico['data_cotacao'].iloc[-1] - grafico['data_cotacao'].iloc[0]).days
                
                st.info(
                    f"**Insights:** No período de {periodo} dias, o valor do frete {'aumentou' if variacao > 0 else 'diminuiu'} "
                    f"**{abs(variacao):.1f}%**. A média de valor por kg é de **R$ {(grafico['valor_frete'] / grafico['peso_kg']).mean():.2f}/kg**."
                )
        
        with tab2:
            # Tabela de dados com estilização
            st.markdown("### Cotações Similares Detalhadas")
            
            # Selecionar e formatar colunas relevantes
            colunas = ['data_cotacao', 'transportadora', 'valor_frete', 'peso_kg', 'prazo_entrega_dias', 'distancia_km']
            tabela = similares[colunas].copy()
            
            # Formatar colunas
            tabela['data_cotacao'] = tabela['data_cotacao'].dt.strftime('%d/%m/%Y')
            tabela['valor_frete'] = tabela['valor_frete'].apply(lambda x: f"R$ {x:,.2f}")
            tabela['valor_por_kg'] = (similares['valor_frete'] / similares['peso_kg']).apply(lambda x: f"R$ {x:.2f}/kg")
            
            # Renomear colunas para exibição
            tabela.columns = ['Data', 'Transportadora', 'Valor Total', 'Peso (kg)', 'Prazo (dias)', 'Distância (km)', 'Valor por kg']
            
            # Exibir tabela estilizada
            st.dataframe(tabela, use_container_width=True)

    else:
        # Mensagem de erro estilizada
        st.markdown("""
        <div style="background-color: #fee2e2; border-left: 5px solid #ef4444; padding: 20px; border-radius: 8px; margin: 25px 0;">
            <h3 style="margin-top: 0; color: #b91c1c; display: flex; align-items: center; font-size: 1.2rem;">
                <span style="font-size: 1.5rem; margin-right: 10px;">⚠️</span> Nenhum dado encontrado
            </h3>
            <p style="margin-bottom: 0; color: #7f1d1d;">Não encontramos cotações similares para os critérios informados. Tente ajustar os parâmetros da sua busca.</p>
            <ul style="margin-top: 15px; color: #7f1d1d;">
                <li>Experimente selecionar outro tipo de carga</li>
                <li>Verifique se a modalidade selecionada é comum para esta rota</li>
                <li>Tente uma rota mais popular (origem/destino)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
