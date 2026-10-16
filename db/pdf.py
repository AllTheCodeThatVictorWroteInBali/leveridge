
import json
import sqlite3
from pathlib import Path


class PdfStore:
    def __init__(self, db_path: str = "pdfs.db"):
        self.db_path = db_path
        self._initialize()

    def _initialize(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pdfs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL CHECK (json_valid(data))
                )
            """)

    def save_pdf(self, data: dict | list) -> int:
        """Save extracted PDF data as JSON. Return the new ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO pdfs (data) VALUES (?)",
                (json.dumps(data, ensure_ascii=False, default=str),)
            )
            return cursor.lastrowid

    def get_pdfs(self) -> list[dict]:
        """Return all saved PDFs as Python objects."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, data FROM pdfs ORDER BY id"
            ).fetchall()

        return [
            {"id": pdf_id, "data": json.loads(data)}
            for pdf_id, data in rows
        ]


if __name__ == "__main__":
    store = PdfStore()

    # Example: connect your existing PaddleOCR function
    # extracted_data = read_pdf("closing_disclosure.pdf")
    # pdf_id = store.save_pdf(extracted_data)
    # print(f"Saved PDF with ID: {pdf_id}")

    for pdf in store.get_pdfs():
        print(json.dumps(pdf, indent=2, ensure_ascii=False))
