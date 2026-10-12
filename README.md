# Busca semântica de PDF

Aplicação de linha de comando para indexar `document.pdf` e responder perguntas usando somente os trechos recuperados desse arquivo. A ingestão e a busca usam embeddings Gemini e a mesma collection PostgreSQL/pgVector; as respostas também são geradas pelo Gemini.

## Requisitos

- Python 3.10 ou superior
- Docker com o plugin Docker Compose
- Uma chave de API Gemini com acesso aos modelos escolhidos
- Um arquivo PDF chamado `document.pdf` na raiz do projeto

Os valores iniciais em `.env.example` são `models/gemini-embedding-001` para embeddings e `gemini-2.5-flash` para respostas. O identificador do modelo de embedding determina a dimensão dos vetores armazenados.

## Configuração

Na raiz do projeto, crie um ambiente virtual, ative-o e instale as dependências:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edite `.env` e defina `GEMINI_API_KEY`. A URL padrão do banco é `postgresql+psycopg://postgres:postgres@localhost:5432/semantic_search`; atualize-a se mudar as configurações do serviço no Compose.

| Variável | Descrição |
| --- | --- |
| `GEMINI_API_KEY` | Chave da API Gemini (obrigatória) |
| `GEMINI_EMBEDDING_MODEL` | Modelo de embeddings (padrão: `models/gemini-embedding-001`) |
| `GEMINI_CHAT_MODEL` | Modelo de resposta (padrão: `gemini-2.5-flash`) |
| `DATABASE_URL` | URL SQLAlchemy/psycopg para PostgreSQL (obrigatória) |
| `PGVECTOR_COLLECTION` | Nome da collection vetorial (padrão: `pdf_documents`) |

O arquivo `.env` e `document.pdf` são locais e não devem ser adicionados ao controle de versão.

## Execução

Coloque o documento a ser indexado na raiz como `document.pdf`. Suba o banco e aguarde a inicialização:

```bash
docker compose up -d
docker compose ps
```

Faça a ingestão e inicie o chat:

```bash
python src/ingest.py
python src/chat.py
```

No chat, digite uma pergunta e pressione Enter. Para sair, use `Ctrl+C`. O programa recupera até 10 chunks e, se não encontrar evidência explícita no contexto, responde `Não tenho informações necessárias para responder sua pergunta.`.

Para parar o banco sem apagar os dados, execute `docker compose down`. Os vetores persistem no volume `postgres_data`.

## Reingestão e troca do modelo de embeddings

Cada execução de `python src/ingest.py` substitui os vetores da collection configurada pelo conteúdo atual de `document.pdf`. Se o modelo de embeddings for alterado para um que produza vetores com dimensão diferente, a ingestão informa a incompatibilidade. Remova a collection antes de tentar novamente ou, para apagar todo o estado local do banco, execute:

```bash
docker compose down -v
docker compose up -d
python src/ingest.py
```

`docker compose down -v` apaga permanentemente os dados do volume local, inclusive todas as collections.

## Testes

Com o ambiente virtual ativado, execute todos os testes:

```bash
python -m pytest
```

Os testes unitários não precisam do PostgreSQL. O teste de integração PostgreSQL/pgVector é ignorado automaticamente quando o banco não está acessível; para executá-lo, suba o serviço com `docker compose up -d`.

Para executar um arquivo de teste específico, por exemplo:

```bash
python -m pytest tests/test_ingest.py
```
