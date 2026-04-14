import json, psycopg
from rich.progress import track

with open("config.json") as f:
    config = json.load(f)

conn = psycopg.connect(**config)
cur = conn.cursor()

def insert_paper(paper):
    # insert paper
    cur.execute("""
        INSERT INTO papers (id, title, abstract, published, url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (
        paper["id"],
        paper["title"],
        paper["abstract"],
        paper["published"],
        paper["url"]
    ))

    # authors
    for author in paper["authors"]:
        cur.execute("""
            INSERT INTO authors (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
        """, (author,))

        result = cur.fetchone()

        if result:
            author_id = result[0]
        else:
            cur.execute("SELECT id FROM authors WHERE name = %s", (author,))
            author_id = cur.fetchone()[0]

        # Build relationship
        cur.execute("""
            INSERT INTO paper_authors (paper_id, author_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (paper["id"], author_id))

    # categories
    for category in paper["categories"]:
        cur.execute("""
            INSERT INTO categories (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
        """, (category,))

        result = cur.fetchone()

        if result:
            category_id = result[0]
        else:
            cur.execute("SELECT id FROM categories WHERE name = %s", (category,))
            category_id = cur.fetchone()[0]

        # Build relationship
        cur.execute("""
            INSERT INTO paper_categories (paper_id, category_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (paper["id"], category_id))

if __name__ == "__main__":
    # Read JSONL
    with open("./raw_data/arxiv_2025_01.jsonl", "r", encoding="utf-8") as f:
        for i, line in track(enumerate(f), description="Inserting papers"):
            paper = json.loads(line)

            insert_paper(paper)

            # Commit every 100 papers to avoid too many transactions
            if i % 100 == 0:
                conn.commit()
                print(f"Inserted {i} papers...")

    conn.commit()
    cur.close()
    conn.close()

    print("Done!")