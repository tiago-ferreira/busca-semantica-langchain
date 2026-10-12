# Proposal

## Why

O repositório ainda não implementa o desafio de ingestão e busca semântica, portanto não há um fluxo executável para consultar o conteúdo de um PDF. Esta mudança entrega um caminho local reproduzível para indexar um documento e responder perguntas com evidências recuperadas, sem recorrer a conhecimento externo.

## What Changes

- Adicionar uma aplicação Python com LangChain para carregar `document.pdf`, dividi-lo em chunks de 1.000 caracteres com sobreposição de 150 e persistir embeddings no PostgreSQL com pgVector.
- Adicionar uma interface CLI que recupera até 10 trechos relevantes e usa um modelo OpenAI para responder somente com base no contexto, incluindo a resposta definida para informação ausente.
- Fornecer configuração de ambiente documentada, dependências e execução local do PostgreSQL/pgVector com Docker Compose.
- Documentar preparação, ingestão e uso do chat; tratar incompatibilidade de dimensão de embeddings após troca de modelo, exigindo recriação da collection.

## Capabilities

### New Capabilities
- `pdf-semantic-search`: Ingestão de PDF, indexação vetorial e perguntas via CLI com respostas fundamentadas no conteúdo recuperado.

### Modified Capabilities
- Nenhuma.

## Impact

- Novo código em `src/` para ingestão, busca e interação CLI; arquivos de configuração/dependências, Docker Compose e README na raiz.
- Integração com OpenAI para embeddings e LLM, PostgreSQL com pgVector, LangChain e carregamento de PDF.
- `document.pdf` será uma entrada fornecida pelo usuário na raiz do projeto; não há PDF nem implementação existentes neste repositório.
