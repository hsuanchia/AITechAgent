# AITechAgent
# Motivation
> 有鑑於技術的更新速度太快，自己慢慢看花費時間又太長，因此希望建立起一個系統可以透過Agent幫我整理並且回答我問題 
>
> 希望透過這個Project拾回從前學習新技術的心態與衝勁，把自己也做一次技術上的更新><
>
> 預期利用技術: PostgreSQL, RAG, Agents, MCP, FastAPI, React,
# Data
* Public data from [arxiv.org](https://arxiv.org/)
>**Thank you to arXiv for use of its open access interoperability!**
* Use data with cs.AI & cs.LG tag -> May crawling cs.CV in future
* Using paper published from 2025/01 ~ 2026/04
# Codes
```text
AITechAgent/
├── Imgs/                   # Folder containing some image about result or what
|
├── frontend/src/
|   ├── component/
|   |   └── chat.jsx        # API for chat with LLM using RAG
|   |   └── search.jsx      # API for searching in DB using SQL
|   |
|   └── APP.jsx             # Frontend by react
|
├── api.py                  # Api backend -> Use FastAPI
|
├── arxiv.py                # Crawling data from arxiv through arxiv api
|
├── embedding.py            # Transform text into embedding use sentence-transformer
|
├── json2sql.py             # Import raw data(json file) into PostgreSQL
|
├── rag.py                  # Model inferece with RAG
|
└── README.md
```
# Current RAG result
* RAG
    * Current model - google/flan-t5-small
    * Current retrieval strategy - Top-k(k=5) with reranking(top-20)
    * Current embedding model: BAAI/bge-small-en-v1.5
    * Current reranking model: BAAI/bge-reranker-base
* Example 1
<img src="/Imgs/Improve_rag_1.png" width="800">

* Example 2
<img src="/Imgs/Improve_rag_2.png" width="600">

* Example 3
<img src="/Imgs/Improve_rag_3.png" width="400">

# Demo
![AITechAgent Local Demo](/Imgs/Simple_demo_0417.gif)

# To do
* Agent / MCP
* Metadata for PostgreSQL
* Updata database everyday(Crawling from arxiv api and process data into database)
