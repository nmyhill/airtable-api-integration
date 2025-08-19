# generate_visnetwork_assets.py
from pathlib import Path
import csv, json, os
from typing import Dict, List, Any, Iterable
from airtable_client import AirtableClient, AirtableConfig

# --------- CONFIGURE YOUR TABLE & FIELD NAMES HERE ----------
# These names mirror your colleague's R script. Adjust if your Airtable columns differ.
TABLES = {
    "Dimension": {
        "group": "Dimension",
        "name_field": "Name",
        "pillars_field": None,
        "relations": [("Domain", "Domain")],  # text or linked-records
    },
    "Domains": {
        "group": "Domain",
        "name_field": "domain_name",
        "pillars_field": "Lifestyle Medicine Pillars",
        "relations": [("Construct", "Construct"), ("Related Domains", "Domain")],
    },
    "Constructs": {
        "group": "Construct",
        "name_field": "Construct Name",
        "pillars_field": "Lifestyle Medicine Pillar",
        "relations": [("Metrics", "Metric"), ("Assessments", "Assessment"), ("Related Constructs", "Construct")],
    },
    "Assessments": {
        "group": "Assessment",
        "name_field": "assessment_name",
        "pillars_field": None,
        "relations": [],
    },
    "Metrics": {
        "group": "Metric",
        "name_field": "metric_name",
        "pillars_field": None,
        "relations": [("Related Assessments", "Assessment"), ("Related Interventions", "Intervention")],
    },
    "Interventions": {
        "group": "Intervention",
        "name_field": "intervention_name",
        "pillars_field": None,
        "relations": [("Assessments", "Assessment"), ("Metrics", "Metric")],
    },
}

# Brand color fallback per group (used later if/when you add color in nodes.json)
GROUP_COLORS = {
    "Dimension": "#025E68",
    "Domain": "#3E5237",
    "Construct": "#D8EBD5",
    "Assessment": "#F1C6DF",
    "Metric": "#EBD82E",
    "Intervention": "#B8B5C6",
}
# ------------------------------------------------------------

OUTDIR = Path("data")
OUTDIR.mkdir(parents=True, exist_ok=True)

def _coerce_list(value: Any) -> List[str]:
    """
    Airtable linked-record fields come as list of record IDs.
    Manual text fields may be a string with comma/semicolon lists.
    Normalize to a list of strings.
    """
    if value is None:
        return []
    if isinstance(value, list):
        # linked records: list of record IDs
        return [str(v) for v in value if v]
    if isinstance(value, str):
        if not value.strip():
            return []
        # split on commas/semicolons
        parts = [p.strip() for p in value.replace(";", ",").split(",")]
        return [p for p in parts if p]
    # Fallback: single value to list
    return [str(value)]

def fetch_table(table_name: str) -> List[dict]:
    client = AirtableClient(AirtableConfig(), table=table_name)
    # We request default JSON (linked records → record IDs). That's fine; we'll map IDs to names.
    return list(client.list_records(page_size=100))

def build_nodes_and_maps() -> (List[Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, str], Dict[str, str]):
    """
    Returns:
      nodes: list of node dicts {id,label,group,pillars,title}
      recid_to_nodeid: map Airtable record ID -> node.id
      recid_to_name: map Airtable record ID -> display name (label)
      name_to_nodeid: map name -> node.id  (handy if relations come as names)
    """
    nodes: List[Dict[str, Any]] = []
    recid_to_nodeid: Dict[str, str] = {}
    recid_to_name: Dict[str, str] = {}
    name_to_nodeid: Dict[str, str] = {}

    for table_name, spec in TABLES.items():
        group = spec["group"]
        name_field = spec["name_field"]
        pillars_field = spec["pillars_field"]

        records = fetch_table(table_name)
        for rec in records:
            rec_id = rec["id"]  # Airtable record ID (stable)
            fields = rec.get("fields", {})
            label = str(fields.get(name_field, "")).strip()
            if not label:
                # Skip nameless records
                continue
            pillars = ""
            if pillars_field:
                val = fields.get(pillars_field, "")
                if isinstance(val, list):
                    pillars = ", ".join([str(v) for v in val if v])
                else:
                    pillars = str(val or "")
            title = f"<b>{label}</b><br>Group: {group}" + (f"<br>Pillars: {pillars}" if pillars else "")

            node = {
                "id": rec_id,            # Use Airtable Record ID → stable!
                "label": label,
                "group": group,
                "pillars": pillars,
                "title": title,
            }
            nodes.append(node)
            recid_to_nodeid[rec_id] = rec_id
            recid_to_name[rec_id] = label
            name_to_nodeid[label] = rec_id

    return nodes, recid_to_nodeid, recid_to_name, name_to_nodeid

def build_edges(name_to_nodeid: Dict[str, str], recid_to_nodeid: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Walk relation fields across all tables and produce edges using node IDs (Airtable Record IDs).
    Supports both linked-record style (record IDs) and comma/semicolon-separated names.
    """
    edges: List[Dict[str, str]] = []

    for table_name, spec in TABLES.items():
        relations = spec["relations"]
        if not relations:
            continue

        records = fetch_table(table_name)
        for rec in records:
            source_node_id = rec["id"]
            fields = rec.get("fields", {})
            # Skip if this source record wasn't turned into a node (e.g., missing name)
            if source_node_id not in recid_to_nodeid:
                continue

            for field_name, _target_group in relations:
                raw = fields.get(field_name)
                if raw is None:
                    continue
                vals = _coerce_list(raw)

                for v in vals:
                    # Two possibilities:
                    # 1) v is a record ID (linked-record) → map via recid_to_nodeid
                    # 2) v is a display name (text list)  → map via name_to_nodeid
                    if v in recid_to_nodeid:
                        to_id = recid_to_nodeid[v]
                    else:
                        to_id = name_to_nodeid.get(v)
                    if not to_id:
                        continue  # unknown target; skip
                    if to_id == source_node_id:
                        continue  # avoid self-loop if present
                    edges.append({"from": source_node_id, "to": to_id})

    # de-dup edges
    seen = set()
    unique_edges = []
    for e in edges:
        key = (e["from"], e["to"])
        if key in seen:
            continue
        seen.add(key)
        unique_edges.append(e)
    return unique_edges

def write_csv(path: Path, rows: Iterable[Dict[str, Any]], headers: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in headers})

if __name__ == "__main__":
    # 1) Build nodes and useful maps
    nodes, recid_to_nodeid, recid_to_name, name_to_nodeid = build_nodes_and_maps()

    # 2) Build edges across relation fields
    edges = build_edges(name_to_nodeid=name_to_nodeid, recid_to_nodeid=recid_to_nodeid)

    # 3) Write CSVs for the R visualization (exact columns expected)
    write_csv(OUTDIR / "nodes.csv", nodes, headers=["id", "label", "group", "pillars", "title"])
    write_csv(OUTDIR / "edges.csv", edges, headers=["from", "to"])

    # 4) (Optional) also write JSONs if you want to use elsewhere
    with open(OUTDIR / "nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
    with open(OUTDIR / "edges.json", "w", encoding="utf-8") as f:
        json.dump(edges, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(nodes)} nodes and {len(edges)} edges to {OUTDIR}/")
