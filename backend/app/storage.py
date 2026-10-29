import json
import os
import tempfile
from threading import RLock
from pathlib import Path


class JsonStorage:

    def __init__(
        self,
        file_path: str | Path | None = None
    ):
        project_root = Path(__file__).resolve().parents[2]

        self.file_path = Path(
            file_path
            or project_root / "data" / "deliveries.json"
        )

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )
        self._lock = RLock()

    def load_records(self) -> list[dict]:
        with self._lock:
            if not self.file_path.exists():
                return []

            content = self.file_path.read_text(encoding="utf-8").strip()
            if not content:
                return []

            try:
                records = json.loads(content)
            except json.JSONDecodeError as error:
                raise RuntimeError(
                    f"Invalid JSON data file: {self.file_path}"
                ) from error

            if not isinstance(records, list):
                raise TypeError("Storage file must contain a JSON list.")

            return records

    def save_records(
        self,
        records: list[dict]
    ) -> None:

        with self._lock:
            payload = json.dumps(records, indent=2)
            file_descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.file_path.name}.",
                suffix=".tmp",
                dir=self.file_path.parent,
                text=True,
            )
            try:
                with os.fdopen(file_descriptor, "w", encoding="utf-8") as temporary:
                    temporary.write(payload)
                    temporary.flush()
                    os.fsync(temporary.fileno())
                os.replace(temporary_name, self.file_path)
            finally:
                if os.path.exists(temporary_name):
                    os.unlink(temporary_name)

    def add_record(
        self,
        record: dict
    ) -> None:

        records = self.load_records()
        records.append(record)
        self.save_records(records)

    def update_record(
        self,
        record_id: str,
        updates: dict
    ) -> dict | None:

        records = self.load_records()

        for record in records:
            if record.get("id") == record_id:
                record.update(updates)
                self.save_records(records)
                return record

        return None
