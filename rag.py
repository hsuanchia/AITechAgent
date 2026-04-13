import psycopg
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

conn = psycopg.connect("dbname=arxiv user=xxxxx password=xxxxx host=localhost port=5432")
cur = conn.cursor()

def retrieve(query, top_k=5):
    q_emb = model.encode(query).tolist()

    # 先抓多一點
    cur.execute("""
    SELECT id, title, abstract
    FROM papers
    ORDER BY embedding <-> %s::vector
    LIMIT 20
    """, (q_emb,))
    
    candidates = cur.fetchall()

    # rerank
    pairs = [(query, title + " " + abstract) for _, title, abstract in candidates]
    scores = reranker.predict(pairs)

    # 排序
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

    return [item[0] for item in ranked[:top_k]]

def build_context(results, max_chars=500):
    context = ""
    for i, (_, title, abstract) in enumerate(results):
        abstract = abstract[:max_chars] 
        context += f"[Paper {i+1}]\nTitle: {title}\nSummary: {abstract}\n\n"
    return context

def get_recent_history(chat_history, k=5):
    history_text = ""
    for turn in chat_history[-k:]:
        history_text += f"User: {turn['user']}\n"
        history_text += f"Assistant: {turn['assistant']}\n"
    return history_text

def ask(query):
    results = retrieve(query)
    context = build_context(results)
    history_text = get_recent_history(chat_history)

    prompt = f"""
            You are a helpful AI assistant.

            Depending on the question, follow the instructions:

            1. If the user asks for papers:
            - Return a list of papers
            - Each paper must include:
                - Title
                - Short summary (1-2 sentences)

            2. If the user asks for explanation:
            - Explain clearly in simple terms

            3. Please answer the question more humanly, and avoid being too robotic.

            4. Only if user ask something about the papers, you can use RAG to find relevant papers and use them as context to answer the question.

            5. Otherwise, you can just answer the question based on your knowledge.

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