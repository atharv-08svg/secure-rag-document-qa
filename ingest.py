from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

# 1. Load document
loader = TextLoader("documents/notes.txt")
documents = loader.load()

# 2. Split document into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = splitter.split_documents(documents)

print(f"Created {len(chunks)} chunks")

# 3. Create embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)

# 4. Create vector database
vector_store = Chroma(
    collection_name="my_documents",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# 5. Store chunks and embeddings
vector_store.add_documents(chunks)

print("Documents successfully added to ChromaDB!")

