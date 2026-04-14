import psycopg, json
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import pipeline

model = SentenceTransformer('all-MiniLM-L6-v2')
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-small",
    max_length=512
)
chat_history = []

with open("config.json") as f:
    config = json.load(f)
conn = psycopg.connect(**config)
cur = conn.cursor()

def retrieve(query, top_k=5):
    q_emb = model.encode(query).tolist()

    # Grab 20 candidates for better reranking
    cur.execute("""
    SELECT id, title, abstract
    FROM papers
    ORDER BY embedding <-> %s::vector
    LIMIT 20
    """, (q_emb,))
    
    candidates = cur.fetchall()
    keywords = keyword_search(query)
    combine = candidates + keywords

    # rerank
    pairs = [(query, title + " " + abstract) for _, title, abstract in combine]
    scores = reranker.predict(pairs)

    # Sorting
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

    return [item[0] for item in ranked[:top_k]]

def build_context(results, max_chars=500):
    context = []
    for i, (_, title, abstract) in enumerate(results):
        context.append(
            f"[Paper {i+1}] {title}\n"
            f"Key Idea: {abstract[:300]}..."
        )
    return "\n\n".join(context)

def keyword_search(query):
    sql = """
    SELECT id, title, abstract
    FROM papers
    WHERE title ILIKE %s OR abstract ILIKE %s
    LIMIT 20
    """
    cur.execute(sql, (f"%{query}%", f"%{query}%"))
    return cur.fetchall()

def rewrite_query(query):
    prompt = f"""
    Rewrite the user query into a better search query for academic paper retrieval.

    Rules:
    - Use technical keywords
    - Be concise
    - Expand abbreviations if needed

    Query:
    {query}

    Rewritten query:
    """
        
    rewritten = generator(prompt)
    rewrite = rewritten[0]['generated_text']
    return rewrite.strip()

def ask(query):
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
    chat_history.append({
        "user": query,
        "assistant": answer
    })
    return answer

if __name__ == "__main__":
    while True:
        q = input("Ask: ")
        if q == "exit":
            break

        answer = ask(q)
        print("\nAnswer:\n", answer)