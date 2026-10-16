
from pathlib import Path
from paddleocr import PaddleOCRVL


pipeline = PaddleOCRVL(device="cpu")


def read_pdf(pdf_path: str) -> list[dict]:
    """Read a PDF with PaddleOCR-VL and return extracted JSON."""
    pdf_path = Path(pdf_path)

    results = pipeline.predict(input=str(pdf_path))

    return [
        result.json
        for result in results
    ]


if __name__ == "__main__":
    import json

    results = read_pdf("closing_disclosure.pdf")
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
