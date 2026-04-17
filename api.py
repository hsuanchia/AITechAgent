import psycopg, json, time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
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


model = SentenceTransformer('BAAI/bge-small-en-v1.5')
tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-base')
reranker = AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-base')
reranker.eval()
generator = pipeline(
    "text2text-generation",
    device='cuda',
    model="google/flan-t5-small",
    max_length=512
)

def fake_stream_answer(text):
    # 模擬逐字輸出（你之後換成 LLM streaming）
    for word in text.split():
        yield word + " "
        time.sleep(0.1)

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

    return StreamingResponse(
        fake_stream_answer(answer),
        media_type="text/plain"
    )