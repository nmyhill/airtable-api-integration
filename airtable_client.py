# airtable_client.py
import os
import time
import typing as t
import requests
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

class AirtableError(Exception):
    pass

@dataclass(frozen=True)
class AirtableConfig:
    token: str = os.getenv("AIRTABLE_TOKEN", "")
    base_id: str = os.getenv("BASE_ID", "")
    # table is optional now; we'll pass it explicitly when we build clients
    table: str = os.getenv("TABLE_NAME", "")

    def validate(self) -> None:
        missing = [k for k, v in [
            ("AIRTABLE_TOKEN", self.token),
            ("BASE_ID", self.base_id),
            # TABLE_NAME intentionally not required
        ] if not v]
        if missing:
            raise AirtableError(f"Missing env vars: {', '.join(missing)}")

class AirtableClient:
    def __init__(self, config: AirtableConfig, *, table: str, timeout: int = 30):
        config.validate()
        if not table:
            raise AirtableError("AirtableClient requires a table name or table ID.")
        self.base_id = config.base_id
        self.table = table
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table}"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {config.token}"})
        self.timeout = timeout

    def _request(self, method: str, url: str, **kwargs) -> dict:
        max_attempts = 5
        backoff = 1.0
        for attempt in range(1, max_attempts + 1):
            resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", backoff))
                time.sleep(retry_after)
            elif 500 <= resp.status_code < 600:
                time.sleep(backoff)
                backoff *= 2
            else:
                try:
                    resp.raise_for_status()
                    return resp.json()
                except requests.HTTPError as e:
                    try:
                        err = resp.json()
                    except Exception:
                        err = {"error": resp.text}
                    raise AirtableError(f"{resp.status_code} {resp.reason} at {url} :: {err}") from e
        # Final raise if we somehow exit loop
        resp.raise_for_status()

    def list_records(
        self,
        *,
        max_records: t.Optional[int] = None,
        page_size: int = 100,
        fields: t.Optional[t.List[str]] = None,
        filter_by_formula: t.Optional[str] = None,
        view: t.Optional[str] = None,
        sort: t.Optional[t.List[t.Dict[str, str]]] = None,
        params_extra: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Iterator[dict]:
        """
        Yields full record objects from the table.
        """
        params: t.Dict[str, t.Any] = {"pageSize": page_size}
        if fields:
            for f in fields:
                params.setdefault("fields[]", []).append(f)
        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula
        if view:
            params["view"] = view
        if sort:
            for i, s in enumerate(sort):
                params[f"sort[{i}][field]"] = s["field"]
                if "direction" in s:
                    params[f"sort[{i}][direction]"] = s["direction"]
        if params_extra:
            params.update(params_extra)

        url = self.base_url
        total = 0
        while True:
            data = self._request("GET", url, params=params)
            for rec in data.get("records", []):
                yield rec
                total += 1
                if max_records and total >= max_records:
                    return
            offset = data.get("offset")
            if not offset:
                return
            params["offset"] = offset
