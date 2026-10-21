from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Resolve PDFs relative to this script, regardless of the current directory.
pdf_files = [
    Path(__file__).resolve().parent / "template.pdf",
    Path(__file__).resolve().parent / "resume.pdf",
]

documents = []
for pdf in pdf_files:
    if not pdf.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf}")
    loader = PyPDFLoader(pdf)
    documents.extend(loader.load())

print(f"Loaded {len(documents)} pages from {len(pdf_files)} PDFs.")

# 2. Split the documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)
chunks = text_splitter.split_documents(documents)
print(f"Split into {len(chunks)} chunks of text.")
