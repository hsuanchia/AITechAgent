import psycopg, json
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import pipeline
from rag import rewrite_query, retrieve, build_context
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("config.json") as f:
    config = json.load(f)

model = SentenceTransformer('all-MiniLM-L6-v2')
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-small",
    max_length=512
)
class SearchRequest(BaseModel):
    query: str

@app.post("/search")
def search(req: SearchRequest):
    q = f"%{req.query}%"
    conn = psycopg.connect(**config)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT title, abstract, url
            FROM papers
            WHERE title ILIKE %s OR abstract ILIKE %s
            LIMIT 10
        """, (q, q))
        
        rows = cur.fetchall()

    results = [
        {
            "title": r[0],
            "abstract": r[1],
            "url": r[2]
        }
        for r in rows
    ]

    return {"results": results}

class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
def chat(req: ChatRequest):
    query = req.query

    # RAG Pipeline
    rewriten_query = rewrite_query(query)
    results1 = retrieve(query)
    results2 = retrieve(rewriten_query)
    context = build_context(results1 + results2)

    prompt = f"""
            You are a helpful AI assistant.

            Your job:
            - Explain concepts clearly (not just list papers)
            - Use the context as supporting evidence
            - If the question is general, answer normally
            - If the user asks for papers:
                - Return a list of papers
                - Each paper must include:
                    - Title
                    - Short summary (1-2 sentences)

            Context:
            {context}

            Current Question:
            {query}

            Answer:
            """

    response = generator(prompt)
    answer = response[0]['generated_text']

    return {
        "answer": answer
    }