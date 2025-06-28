import os
from dotenv import load_dotenv
from pathlib import Path

from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

def upload_personal_data():
    # Resolve absolute path to data/knowledge_base directory
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "knowledge_base"

    if not data_path.exists():
        raise FileNotFoundError(f"❌ Folder not found: {data_path}")

    # Load all .txt files
    loader = DirectoryLoader(
        path=str(data_path),
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    raw_docs = loader.load()

    # Add metadata to each doc
    for doc in raw_docs:
        filename = os.path.basename(doc.metadata['source'])
        topic = filename.replace(".txt", "")
        doc.metadata.update({
            "source": topic,
            "topic": "personal_info",
            "author": "Rakesh Reddy"
        })

    print(f"📄 Loaded {len(raw_docs)} raw documents")

    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(raw_docs)

    print(f"✂️  Created {len(chunks)} chunks")

    # Load embeddings
    embeddings = OpenAIEmbeddings()

    # Upload to Qdrant
    vectorstore = Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings,
        location=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name="personal_knowledge_base"
    )

    print("✅ Personal data uploaded to Qdrant!")

if __name__ == "__main__":
    upload_personal_data()
