import psycopg
from sentence_transformers import SentenceTransformer
from rich.progress import track

if __name__ == "__main__":
    model = SentenceTransformer('all-MiniLM-L6-v2')

    conn = psycopg.connect("dbname=arxiv user=hsuanchia password=hsuanchia host=localhost port=5432")
    cur = conn.cursor()

    cur.execute("SELECT id, title, abstract FROM papers")
    rows = cur.fetchall()

    for row in track(rows, description="Processing papers into embeddings..."):
        paper_id, title, abstract = row
        text = title + " " + abstract

        emb = model.encode(text).tolist()

        cur.execute(
            "UPDATE papers SET embedding = %s WHERE id = %s",
            (emb, paper_id)
        )

    conn.commit()