# IS-Final - Integração de Sistemas

Projeto desenvolvido no âmbito da unidade curricular de **Integração de Sistemas**, da Licenciatura em Engenharia Informática do Instituto Politécnico de Viana do Castelo.

A aplicação integra diferentes mecanismos de comunicação e processamento de dados - **REST, gRPC, GraphQL e RabbitMQ** - numa arquitetura baseada em contentores Docker. O sistema permite carregar ficheiros CSV/XSD, processar dados de vendas, converter CSV para XML, enriquecer registos com coordenadas geográficas, consultar e ordenar XML e visualizar localizações num mapa interativo.

**Autor:** Luís Filipe Esteves Dias - n.º 29404  
**Ano letivo:** 2024/2025

---

## Funcionalidades

- Upload de ficheiros CSV e XSD através do frontend.
- Processamento assíncrono de CSV com RabbitMQ e um worker dedicado.
- Armazenamento de dados em PostgreSQL.
- Conversão de ficheiros CSV para XML através de gRPC.
- Enriquecimento de registos sem coordenadas com a API Nominatim.
- Pesquisa de texto em ficheiros XML.
- Ordenação de XML por campo, em ordem ascendente ou descendente.
- Listagem dos ficheiros CSV e XML disponíveis nos volumes Docker.
- Consulta de dados através de GraphQL.
- Pesquisa de clientes por cidade num mapa Leaflet.
- Atualização da localização de um cliente através do mapa e reverse geocoding com Nominatim.

---

## Arquitetura

O projeto está dividido em serviços independentes, executados através de Docker Compose.

```mermaid
flowchart LR
    UI[Frontend\nNext.js / React] --> REST[REST API\nDjango REST Framework]
    UI --> GQL[GraphQL Server\nDjango / Graphene]

    REST --> GRPC[gRPC Server\nPython]
    REST --> MQ[RabbitMQ]
    MQ --> WORKER[CSV Worker\nPython / Pandas]

    WORKER --> DB[(PostgreSQL)]
    GQL --> DB
    GRPC --> DB

    GRPC --> CSV[(CSV Volume)]
    GRPC --> XML[(XML Volume)]
    GRPC --> NOM[Nominatim API]
    GQL --> NOM
