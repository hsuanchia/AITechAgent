import psycopg
from sentence_transformers import SentenceTransformer
from rich.progress import track

if __name__ == "__main__":
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')

    conn = psycopg.connect("dbname=arxiv user=hsuanchia password=hsuanchia host=localhost port=5432")
    cur = conn.cursor()

    cur.execute("SELECT id, title, abstract FROM papers")
    rows = cur.fetchall()

    for row in track(rows, description="Processing papers into embeddings..."):
        paper_id, title, abstract = row
        text = f"Title: {title}\nAbstract: {abstract}"

        emb = model.encode(text, device='cuda', normalize_embeddings=True, show_progress_bar=True).tolist()

        cur.execute(
            "UPDATE papers SET embedding_bge = %s WHERE id = %s",
            (emb, paper_id)
        )

    conn.commit()