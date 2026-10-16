from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from db.pdf import PdfStore
from main import app


class ReadTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = PdfStore(str(Path(directory.name) / "pdfs.db"))
        store_patch = patch("main.PdfStore", return_value=self.store)
        store_patch.start()
        self.addCleanup(store_patch.stop)

    def test_returns_ocr_json_and_removes_temporary_file(self):
        paths = []
        pdf_bytes = b"%PDF-1.4\n%%EOF"
        extracted = [{"page": 1, "text": "Example"}]

        def fake_read_pdf(pdf_path):
            path = Path(pdf_path)
            paths.append(path)
            self.assertEqual(path.read_bytes(), pdf_bytes)
            return extracted

        with patch.dict("sys.modules", {"model.paddle": SimpleNamespace(read_pdf=fake_read_pdf)}):
            with TestClient(app) as client:
                response = client.post(
                    "/read", files={"file": ("example.pdf", pdf_bytes, "application/pdf")}
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), extracted)
        self.assertEqual(self.store.get_pdfs(), [{"id": 1, "data": extracted}])
        self.assertEqual(len(paths), 1)
        self.assertFalse(paths[0].parent.exists())

    def test_removes_temporary_file_when_ocr_fails(self):
        paths = []

        def fake_read_pdf(pdf_path):
            paths.append(Path(pdf_path))
            raise RuntimeError("OCR failed")

        with patch.dict("sys.modules", {"model.paddle": SimpleNamespace(read_pdf=fake_read_pdf)}):
            with TestClient(app) as client:
                with self.assertRaisesRegex(RuntimeError, "OCR failed"):
                    client.post(
                        "/read", files={"file": ("example.pdf", b"%PDF", "application/pdf")}
                    )

        self.assertEqual(len(paths), 1)
        self.assertFalse(paths[0].parent.exists())
        self.assertEqual(self.store.get_pdfs(), [])

    def test_rejects_invalid_and_missing_uploads_without_running_ocr(self):
        read_pdf = Mock()
        with patch.dict("sys.modules", {"model.paddle": SimpleNamespace(read_pdf=read_pdf)}):
            with TestClient(app) as client:
                self.assertEqual(
                    client.post("/read", files={"file": ("example.txt", b"text")}).status_code,
                    415,
                )
                self.assertEqual(client.post("/read").status_code, 422)
        read_pdf.assert_not_called()
        self.assertEqual(self.store.get_pdfs(), [])

    def test_loads_ocr_at_startup_and_logs_readiness(self):
        read_pdf = Mock(return_value=[])
        with patch("main.import_module", return_value=SimpleNamespace(read_pdf=read_pdf)) as load:
            with self.assertLogs("uvicorn.error", level="INFO") as logs:
                load.assert_not_called()
                with TestClient(app) as client:
                    load.assert_called_once_with("model.paddle")
                    read_pdf.assert_not_called()
                    self.assertIs(app.state.read_pdf, read_pdf)
                    self.assertEqual(client.get("/index.html").status_code, 200)
                    response = client.post(
                        "/read", files={"file": ("example.pdf", b"%PDF", "application/pdf")}
                    )
                    self.assertEqual(response.status_code, 200)
                    load.assert_called_once_with("model.paddle")
                    read_pdf.assert_called_once()
        self.assertTrue(any("Loading PaddleOCR" in message for message in logs.output))
        self.assertTrue(any("PaddleOCR ready" in message for message in logs.output))

    def test_aborts_startup_and_logs_model_initialization_failure(self):
        with patch("main.import_module", side_effect=RuntimeError("Model load failed")):
            with self.assertLogs("uvicorn.error", level="ERROR") as logs:
                with self.assertRaisesRegex(RuntimeError, "Model load failed"):
                    with TestClient(app):
                        self.fail("Startup should not complete")
        self.assertTrue(any("server startup aborted" in message for message in logs.output))


if __name__ == "__main__":
    unittest.main()