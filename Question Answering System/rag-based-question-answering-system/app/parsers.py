from pypdf import PdfReader


def parse_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def parse_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as e:
            raise ValueError("PDF is encrypted and could not be decrypted") from e

    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)