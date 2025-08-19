from airtable_client import AirtableClient, AirtableConfig
import csv
from pathlib import Path

def print_first_5():
    client = AirtableClient(AirtableConfig())
    records = []
    for rec in client.list_records(max_records=5):
        records.append(rec)
    print(f"Fetched {len(records)} records")
    for r in records:
        print(r["id"], r.get("fields", {}))

def dump_all_to_csv(out_path: str = "airtable_export.csv", fields=None):
    """
    Streams the whole table to CSV. If fields is None, writes all present keys unioned on the fly.
    """
    client = AirtableClient(AirtableConfig())
    rows = []
    all_keys = set()

    for rec in client.list_records(page_size=100):
        f = rec.get("fields", {})
        rows.append({"id": rec["id"], **f})
        all_keys.update(f.keys())

    # choose headers: id + provided fields or discovered keys
    headers = ["id"] + (fields if fields else sorted(all_keys))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in headers})

    print(f"Wrote {len(rows)} rows to {out_path}")

def filtered_example():
    client = AirtableClient(AirtableConfig())
    # Example: records where {Status} = "Draft" and Created this year (adjust for your fields)
    formula = 'AND({Status}="Draft", YEAR(TODAY())=YEAR({Created}))'
    for rec in client.list_records(
        filter_by_formula=formula,
        fields=["Name", "Status", "Created"],
        sort=[{"field": "Created", "direction": "desc"}],
        view=None,
        page_size=100,
        max_records=20,
    ):
        print(rec["id"], rec["fields"])

if __name__ == "__main__":
    print_first_5()
    # dump_all_to_csv("exports/airtable_export.csv")
    # filtered_example()
