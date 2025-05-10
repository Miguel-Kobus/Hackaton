# Cotador de Frete - Supabase

![Logo](assets/logo.png)

## 📋 Descrição

O Cotador de Frete é uma aplicação web desenvolvida em Python com Streamlit que permite aos usuários obter cotações de frete de forma rápida e eficiente. O sistema utiliza dados históricos armazenados no Supabase para estimar valores de frete com base em origem, destino, tipo de carga, peso e modalidade de transporte.

## 🚀 Funcionalidades

- **Autenticação de usuários** - Sistema de login seguro
- **Cotação de fretes** - Estimativa de valores com base em dados históricos
- **Visualização de dados** - Gráficos interativos para análise de tendências
- **Geolocalização** - Cálculo de distâncias entre origem e destino
- **Histórico de cotações** - Acesso a cotações anteriores
- **Interface responsiva** - Experiência otimizada em diferentes dispositivos

## 🛠️ Tecnologias Utilizadas

- **[Python](https://www.python.org/)** - Linguagem de programação principal
- **[Streamlit](https://streamlit.io/)** - Framework para desenvolvimento da interface web
- **[Supabase](https://supabase.io/)** - Banco de dados e autenticação
- **[Pandas](https://pandas.pydata.org/)** - Manipulação e análise de dados
- **[Plotly](https://plotly.com/)** - Visualizações gráficas interativas

## 📦 Estrutura do Projeto

```
cotador_frete_supabase/
├── assets/
│   └── styles.css         # Estilos personalizados
├── utils/
│   ├── geolocalizacao.py  # Funções para cálculo de distâncias
│   ├── login.py           # Sistema de autenticação
│   └── supabase_client.py # Configuração do cliente Supabase
├── cotador_frete.py       # Aplicação principal
└── README.md              # Documentação
```

## 🔧 Instalação e Configuração

### Pré-requisitos

- Python 3.8 ou superior
- Pip (gerenciador de pacotes Python)
- Conta no Supabase

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/cotador_frete_supabase.git
   cd cotador_frete_supabase
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione suas credenciais do Supabase:
     ```
     SUPABASE_URL=sua_url_do_supabase
     SUPABASE_KEY=sua_chave_do_supabase
     ```

### Execução

Para iniciar a aplicação, execute:

```bash
streamlit run cotador_frete.py
```

A aplicação estará disponível em `http://localhost:8501`.

## 📊 Modelo de Dados

O sistema utiliza as seguintes tabelas no Supabase:

- **cotacoes_frete** - Armazena histórico de cotações
- **usuarios** - Informações de usuários e autenticação

## 🔐 Autenticação

O sistema utiliza a autenticação de 2 fatores para gerenciar usuários e sessões. Os usuários precisam fazer login para acessar as funcionalidades de cotação.

## 📈 Algoritmo de Cotação

O algoritmo de cotação considera os seguintes fatores:
- Distância entre origem e destino
- Tipo de carga
- Peso da carga
- Modalidade de transporte
- Dados históricos de cotações similares


## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📞 Contato

Para dúvidas ou sugestões, entre em contato através do email: seu-email@exemplo.com

---

Desenvolvido para o Hackathon Esales 2025 🚀
