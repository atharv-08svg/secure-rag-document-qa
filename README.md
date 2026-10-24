# Secure RAG Document Question-Answering API

A backend application that enables authenticated users to ask questions about their documents using Retrieval-Augmented Generation (RAG), with role-based access control and document-level retrieval restrictions.

## Features

- Document-grounded question answering using Google Gemini and LangChain
- Vector similarity search using ChromaDB
- JWT-based authentication and bcrypt password hashing
- Role-based access control (RBAC) with user and admin roles
- Document-level authorization to prevent cross-user retrieval
- Text document upload, listing, retrieval and deletion
- Request validation, error handling and basic prompt-injection safeguards
- Docker and Docker Compose support
- Automated testing with pytest

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| RAG | LangChain, Google Gemini |
| Vector database | ChromaDB |
| Relational database | SQLite, SQLAlchemy |
| Authentication | JWT, bcrypt |
| Testing | pytest, FastAPI TestClient |
| Containerization | Docker, Docker Compose |

## Architecture

1. A client sends an HTTP request to FastAPI.
2. Protected endpoints validate the JWT access token.
3. RBAC checks whether the authenticated user has the required permission.
4. SQLAlchemy retrieves document ownership information from SQLite.
5. The RAG pipeline filters vector retrieval to authorized documents.
6. Relevant document chunks are passed to Gemini as context.
7. The API returns a generated answer and source information.

## Getting Started

### Prerequisites

- Python 3.12 or later
- Docker Desktop (optional)
- Google Gemini API credentials

### Local setup

Clone the repository and navigate into the project directory.

Create a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and supply your own credentials.

Initialize the database and seed the required roles and permissions according to the project's setup scripts.

Start the API:

```bash
uvicorn app:app --reload
```

API documentation is available at:

`http://127.0.0.1:8000/docs`

### Docker

```bash
docker compose up -d --build
```

### Testing

```bash
python -m pytest -v
```

The latest local test run passed **19 automated tests**, covering authentication, JWT validation, authorization, API responses and document upload validation.

## Security

- JWT-protected endpoints
- Permission-based authorization
- Document-level retrieval filtering
- Password hashing
- Basic defenses against instructions embedded in retrieved documents
- Environment-based secret configuration

## Current Limitations

- SQLite is used for local persistence.
- The API has not yet been publicly deployed.
- Automated tests do not currently cover the complete live Gemini question-answering workflow.
- A web frontend is planned for a future version.

## Future Improvements

- RAG retrieval and answer-quality evaluation
- CI testing using GitHub Actions
- PostgreSQL support
- React frontend
- Cloud deployment

## Project Status

Core backend implemented, containerized and passing the current automated test suite. End-to-end integration verification and deployment are planned next.