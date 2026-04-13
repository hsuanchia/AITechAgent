import feedparser, json, argparse, calendar, requests, time
from datetime import datetime
import xml.etree.ElementTree as ET

def parse_arxiv_entry(entry):
    return {
        "id": entry.id,
        "title": entry.title.strip().replace("\n", " "),
        "abstract": entry.summary.strip().replace("\n", " "),
        "published": entry.published,
        "authors": [author.name for author in entry.authors],
        "categories": [tag.term for tag in entry.tags],
        "url": entry.link
    }

def is_target_month(published_str, cur_year=2026, cur_month=4):
    # e.g. '2026-04-10T12:34:56Z'
    dt = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ")
    # print(dt.year, " ", dt.month)
    # print(cur_year, " ", cur_month)
    return dt.year == cur_year and int(dt.month) == int(cur_month)

def build_date_range(year, month):
    last_day = calendar.monthrange(year, month)[1]
    start = f"{year}{month:02d}010000"
    end = f"{year}{month:02d}{last_day}2359"
    
    return start, end

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch arXiv papers from a specific month / year.")
    parser.add_argument("--month", type=int, default=4, help="Target month (1-12)")
    parser.add_argument("--year", type=int, default=2026, help="Target year")
    args = parser.parse_args()
    target_month = f"{args.month:02d}"
    target_year = args.year
    start_date, end_date = build_date_range(target_year, args.month)
    results = []
    start = 0
    sleep_time = 10  # seconds
    while True:
        params = {
            "search_query": '(cat:cs.AI OR cat:cs.LG)' + \
                f' AND submittedDate:[{start_date} TO {end_date}]',    
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
            try:
                if is_target_month(entry.published, cur_year=target_year, cur_month=target_month):
                    parsed = parse_arxiv_entry(entry)
                    results.append(parsed)
            except Exception as e:
                print(f"Error parsing entry: {e}")
                continue

        start += 100
        time.sleep(5)
        print(f'Fetched {len(results)} entries so far...')
        print(f"Current progress: {start} / {total}")

    # Save into JSON file
    with open(f"./raw_data/arxiv_{target_year}_{target_month}.jsonl", "w+", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"Total saved: {len(results)}")

