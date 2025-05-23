# FastAPI em AWS Lambda: Projeto de IA para Detecção e Maturação de Frutas

Este projeto implementa uma API FastAPI hospedada em AWS Lambda para processamento de frutas usando modelos de Inteligência Artificial. A API permite fazer upload de imagens e processá-las através de modelos de IA hospedados em instâncias EC2.

## INFORMAÇÕES SOBRE O TCC
#### Título: Solução de Visão Computacional para controle de validade em mercados.
#### Faculdade: Instituto Mauá de Tecnologia
#### Curso: Ciência da Computação

##### Alunos:
1. Leonardo Guilmo Chin
2. Luigi Guimarães Trevisan
3. Refael Bidetti Baldi Simões Ferreira
4. Rodrigo Diana Siqueira
5. Vitor Moretti Negresiolo

##### Orientadores:
1. Milkes Yone Alvarenga
2. Sandro Martini
3. Gabriel de Souza Lima

## Arquitetura

![Arquitetura](https://app.diagrams.net/?dark=0#G1Bk6VyCvnHJqrIjZAiNT3TO1Xj0ih07Am)

A arquitetura do projeto para a primeira entrega consiste em:

1. **Frontend** - Interface React para visualização dos resultados
2. **API Layer** - API Gateway + endpoints REST implementados com FastAPI
3. **Backend (Lambda)** - Lógica de negócios em FastAPI rodando como função Lambda
4. **Armazenamento** - DynamoDB para metadados e S3 para imagens
5. **Inteligência Artificial** - Modelos de IA rodando em EC2

## Funcionalidades

- **Detecção de Objetos**: Processamento de imagens com modelos de detecção
- **Análise de Maturação**: Avaliação do estágio de maturação em imagens
- **Armazenamento de Resultados**: Persistência de imagens e metadados
- **Consulta de Resultados**: Recuperação de resultados de processamentos anteriores

## Tecnologias Utilizadas

- **Python 3.9**: Linguagem de programação
- **FastAPI**: Framework para APIs
- **AWS Lambda**: Execução serverless
- **API Gateway**: Roteamento de requisições
- **DynamoDB**: Banco de dados NoSQL para metadados
- **S3**: Armazenamento de objetos para imagens
- **EC2**: Hospedagem de modelos de IA
- **Mangum**: Adaptador para AWS Lambda
- **GitHub Actions**: CI/CD automatizado

## Estrutura do Projeto

```
projeto-fastapi-lambda/
├── .github/workflows/           # Configurações do GitHub Actions
├── src/                         # Código-fonte
│   ├── app/                     # Aplicação principal
│   ├── modules/                 # Módulos de funcionalidades
│   └── shared/                  # Código compartilhado
├── tests/                       # Testes automatizados
├── requirements.txt             # Dependências de produção
└── requirements-dev.txt         # Dependências de desenvolvimento
```

## Como executar localmente

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/projeto-fastapi-lambda.git
cd projeto-fastapi-lambda
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements-dev.txt
```

## Variáveis de Ambiente

Configure as seguintes variáveis de ambiente:

- `ENVIRONMENT`: Ambiente de execução (dev, hom, prod)
- `AWS_REGION`: Região da AWS
- `DYNAMODB_TABLE_NAME`: Nome da tabela DynamoDB
- `EC2_IA_ENDPOINT`: Endpoint para o serviço de IA em EC2

## Licença

Este projeto está licenciado sob os termos da licença MIT.