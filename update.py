import feedparser, json, argparse, requests, time, datetime, psycopg
import xml.etree.ElementTree as ET
from sentence_transformers import SentenceTransformer
from rich.progress import track
from arxiv_api import parse_arxiv_entry

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

def crawler(start_time, end_time):
    results = []

    print(f"Fetching papers from {start_time} to {end_time}...")
    start = 0
    sleep_time = 10  # seconds
    while True:
        params = {
            "search_query": '(cat:cs.AI OR cat:cs.LG)' + \
                f' AND submittedDate:[{start_time} TO {end_time}]',    
            "start" : start,
            "max_results": 100
        }
        try:
            response = requests.get("http://export.arxiv.org/api/query", params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            print("Request failed:", e)
            time.sleep(sleep_time)
            sleep_time += 5
            continue
        sleep_time = 10  # reset sleep time after a successful request
        print(f"Request status code: {response.status_code}")
        if response.status_code in [429, 503]:
            print("Rate limited... sleeping")
            time.sleep(sleep_time)
            sleep_time += 5
            continue
        sleep_time = 10  # reset sleep time after a successful request

        feed = feedparser.parse(response.text)
        # Get total papers amount for current month from the XML response
        root = ET.fromstring(response.content)
        ns = {'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}
        total = root.find('opensearch:totalResults', ns).text
        print("Total papers:", total)

        # Break when no more entries are returned (i.e., we've fetched all papers for the month)
        if not feed.entries:
            break

        for entry in feed.entries:
            parsed = parse_arxiv_entry(entry)
            results.append(parsed)

        start += 100
        time.sleep(5)
        print(f'Fetched {len(results)} entries so far...')
        print(f"Current progress: {start} / {total}")

    # Save into JSON file
    with open(f"./raw_data/arxiv_{start_time}_{end_time}.jsonl", "w+", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"Total saved: {len(results)}")

def insert_into_db(jsonl_path):
    # Read JSONL
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in track(enumerate(f), description="Inserting papers into database..."):
            paper = json.loads(line)

            insert_paper(paper)

            # Commit every 100 papers to avoid too many transactions
            if i % 100 == 0:
                conn.commit()
                print(f"Inserted {i} papers...")

    conn.commit()
    print("Done!")

def build_embedding():
    print("Building embeddings for papers...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')

    cur.execute("SELECT id, title, abstract FROM papers WHERE embedding_bge IS NULL")
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

if __name__ == "__main__":
    # Query the latest published date from DB
    cur.execute("SELECT MAX(published) FROM papers")
    max_date_row = cur.fetchone()
    print(max_date_row[0])
    if max_date_row[0]:
        max_date = datetime.datetime.strptime(str(max_date_row[0]), "%Y-%m-%d %H:%M:%S")
        start_date = max_date + datetime.timedelta(days=1)
    else:
        start_date = datetime.datetime(2026, 4, 1)  # Default start if no data
    end_date = datetime.datetime.now()

    start_time = start_date.strftime("%Y%m%d")
    end_time = end_date.strftime("%Y%m%d")

    crawler(start_time, end_time)
    insert_into_db(f"./raw_data/arxiv_{start_time}_{end_time}.jsonl")
    build_embedding()

    cur.close()
    conn.close()