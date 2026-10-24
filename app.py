from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile, File
from sqlalchemy.orm import Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as RAGDocument

from database import get_db
from models import User, Document
from rag import vector_store
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from database import SessionLocal
from models import User
from auth import verify_password
from jwt_helper import create_access_token
from security import get_current_user
from rbac import require_permission
from rag import ask_question, vector_store
import logging
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RAG API"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(
        "Unhandled API error on %s %s",
        request.method,
        request.url.path,
        exc_info=exc
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected server error occurred."
        }
    )


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/")
def home():
    return {
        "message": "RAG API is running"
    }


# -------------------------
# LOGIN
# -------------------------

@app.post("/login")
def login(data: LoginRequest):

    db = SessionLocal()

    user = db.query(User).filter(
        User.username == data.username
    ).first()

    if not user:
        db.close()

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):
        db.close()

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token({
        "user_id": user.id,
        "role": user.role.name
    })

    db.close()

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# -------------------------
# PROTECTED ENDPOINT
# -------------------------

@app.get("/protected")
def protected(
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": "You accessed a protected endpoint!",
        "user": current_user
    }


# -------------------------
# DELETE DOCUMENT
# -------------------------



@app.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(
        require_permission("upload_documents")
    ),
    db: Session = Depends(get_db),
):
    # Accept text files only for this first version.
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported"
        )

    # Read and validate the uploaded content.
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty"
        )

    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 2 MB"
        )

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The file must contain valid UTF-8 text"
        )

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded file contains no text"
        )

    # Generate a unique storage name to avoid filename collisions.
    documents_dir = Path("documents")
    documents_dir.mkdir(parents=True, exist_ok=True)

    stored_path = documents_dir / f"{uuid4().hex}.txt"
    stored_path.write_text(text, encoding="utf-8")

    db_document = None

    try:
        # Create the SQLite metadata record.
        db_document = Document(
        filename=Path(file.filename).name,
        uploaded_by=user.id,
        storage_path=str(stored_path)
    )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Split the uploaded text into RAG chunks.
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        chunks = [
            RAGDocument(
                page_content=chunk,
                metadata={
                    "document_id": str(db_document.id),
                    "source": str(stored_path),
                    "filename": db_document.filename
                }
            )
            for chunk in splitter.split_text(text)
        ]

        # Generate embeddings and store chunks in ChromaDB.
        vector_store.add_documents(chunks)

        return {
            "message": "Document uploaded successfully",
            "document_id": db_document.id,
            "filename": db_document.filename,
            "chunks_created": len(chunks)
        }

   
    except Exception as exc:
        # Remove any chunks that may have been added.
        if db_document is not None and db_document.id is not None:
            try:
                vector_store._collection.delete(
                    where={"document_id": str(db_document.id)}
                )
            except Exception:
                pass

        # Roll back any pending database changes.
        db.rollback()

        # Remove the document record if it was already committed.
        if db_document is not None and db_document.id is not None:
            try:
                existing = (
                    db.query(Document)
                    .filter(Document.id == db_document.id)
                    .first()
                )
                if existing:
                    db.delete(existing)
                    db.commit()
            except Exception:
                db.rollback()

        # Remove the uploaded file.
        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise HTTPException(
            status_code=500,
            detail="Document upload failed"
        ) from exc

    
@app.get("/documents")

@app.get("/documents")
def list_documents(
    user: User = Depends(
        require_permission("read_documents")
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Document)

    # Normal users can see only their own documents.
    # Admins can see all documents.
    if user.role.name != "admin":
        query = query.filter(
            Document.uploaded_by == user.id
        )

    documents = query.order_by(Document.id).all()

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "uploaded_by": document.uploaded_by,
        }
        for document in documents
    ]


@app.get("/documents/{document_id}")

@app.get("/documents/{document_id}")
def get_document(
    document_id: int,
    user: User = Depends(
        require_permission("read_documents")
    ),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Normal users can access only their own documents.
    if (
        user.role.name != "admin"
        and document.uploaded_by != user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "id": document.id,
        "filename": document.filename,
        "uploaded_by": document.uploaded_by,
    }

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    user: User = Depends(require_permission("delete_documents")),
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Remember the path before deleting the database record.
    storage_path = document.storage_path

    try:
        # Remove this document's chunks from ChromaDB.
        vector_store._collection.delete(
            where={"document_id": str(document.id)}
        )

        # Remove the database record.
        db.delete(document)
        db.commit()

        # Remove the original file, if its path is recorded.
        
        if storage_path:
            documents_dir = Path("documents").resolve()
            file_path = Path(storage_path).resolve()

            if (
                file_path != documents_dir
                and documents_dir in file_path.parents
                and file_path.is_file()
    ):
                file_path.unlink()

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Document deletion failed"
        ) from exc

    return {
        "message": "Document deleted successfully",
        "document_id": document_id,
        "deleted_by": user.username,
    }


from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000
    )



@app.post("/ask")

@app.post("/ask")
def ask(
    data: AskRequest,
    user: User = Depends(require_permission("read_documents")),
    db: Session = Depends(get_db),
):
    query = db.query(Document.id)

    if user.role.name != "admin":
        query = query.filter(Document.uploaded_by == user.id)

    allowed_document_ids = [
        str(row[0]) for row in query.all()
    ]

    try:
        result = ask_question(
            data.question,
            allowed_document_ids
        )
    except Exception:
        logger.exception(
            "RAG question processing failed for user_id=%s",
            user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to process the question. Please try again."
        )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
    }