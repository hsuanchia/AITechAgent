import psycopg, json, torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# model = SentenceTransformer('all-MiniLM-L6-v2')
# reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

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
chat_history = []

with open("config.json") as f:
    config = json.load(f)
conn = psycopg.connect(**config)
cur = conn.cursor()

def retrieve(query, top_k=5):
    q_emb = model.encode(query, device='cuda', normalize_embeddings=True).tolist()

    # Grab 50 candidates for better reranking 
    # <=> means cosine similarity for pgvector 
    # <-> means euclidean distance
    cur.execute("""
    SELECT id, title, abstract
    FROM papers
    ORDER BY embedding_bge <-> %s::vector 
    LIMIT 20
    """, (q_emb,))
    
    candidates = cur.fetchall()
    keywords = keyword_search(query)
    combine = candidates + keywords

    # Rerank
    # print("Reranking...")
    pairs = [(query, title + "\n" + abstract) for _, title, abstract in combine]
    with torch.no_grad():
        inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
        scores = reranker(**inputs, return_dict=True).logits.view(-1, ).float()

    # scores = reranker.predict(pairs)

    # Sorting
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

    return [item[0] for item in ranked[:top_k]]

def build_context(results, max_chars=300):
    context = []
    for i, (_, title, abstract) in enumerate(results):
        context.append(
            f"[Paper {i+1}] {title}\n"
            f"Abstract: {abstract[:max_chars]}..."
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

def reasoning(context, query):
    prompt = f"""
    Extract structured insights from the context.

    Output format:
    - Key methods:
    - Key findings:
    - Relevant concepts:
    - Important differences:

    Context:
    {context}

    Question:
    {query}

    Answer:
    """

    response = generator(prompt)
    answer = response[0]['generated_text']
    return answer

def ask(query):
    print("Rewriting query...")
    rewriten_query = rewrite_query(query)
    print("Retrieving papers...")
    results1 = retrieve(query)
    results2 = retrieve(rewriten_query)
    print("Building context...")
    context = build_context(results1 + results2)
    print("Context:\n", context, "\n")
    print("Reasoning...")
    reason = reasoning(context, query)
    print(f"Reasoning:\n{reason}\n")

    prompt = f"""
            You are a helpful AI assistant.

            Your job:
            - Explain concepts clearly (not just list papers)
            - Please answer the current question with some details or summaries, not just a short answer. 

            Instruction:
            - You MUST reorganize the information into a new structure
            - You MUST explain in your own words
            - DO NOT reuse sentence structures from context or insights
            - Expand each idea with explanation

            Context:
            {context}

            Structured Insights:
            {reasoning}

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