# AnomAI — Enterprise Data Reliability Platform

AnomAI is a schema-first data reliability platform using:

- Node.js + Express
- MongoDB + Mongoose
- HTML/CSS/JavaScript frontend
- Python + FastAPI
- pandas / scikit-learn / Isolation Forest

React is intentionally not used.

## 1. Requirements

Install locally:

- Node.js 20+ recommended
- Python 3.11+ recommended
- MongoDB Community Server 7/8+ running locally
- MongoDB Compass is optional

## 2. Start MongoDB

Make sure the MongoDB service is running and listening on:

`mongodb://127.0.0.1:27017`

The application uses database:

`anomai`

You do NOT need to manually create the database. The backend creates the database collections and indexes automatically when it starts.

## 3. Start the ML service

Open Terminal 1:

```cmd
cd AnomAi\mlservices
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verify:

`http://127.0.0.1:8000/health`

It should return a healthy response.

## 4. Start the backend

Open Terminal 2:

```cmd
cd AnomAi\backend
npm install
npm run setup
npm start
```

The backend will be available at:

`http://localhost:8080/anomai`

The setup command is safe to run more than once.

## 5. Application flow

1. Open `/anomai`.
2. Create an account.
3. Login.
4. Upload a dataset.
5. AnomAI validates the file.
6. FastAPI loads it and performs schema-first profiling.
7. Rules, statistics and Isolation Forest analyze the data.
8. Reliability and ML-readiness scores are calculated.
9. Conservative remidiation is applied and audited.
10. The cleaned dataset is saved through the backend.
11. The analysis is saved to MongoDB against the authenticated user.
12. Open `/anomai/<your-user-id>/history` to see only your records.

## Supported formats

CSV, TSV, TXT, XLSX, XLS, ODS, JSON, JSONL, NDJSON, XML and Parquet.

Legacy `.xls` input is accepted. Its cleaned output is returned as modern `.xlsx` because reliable legacy XLS writing is not provided by the pandas/openpyxl stack.

## MongoDB collections

The backend creates:

- `users`
- `analysishistories`

History records contain the owning `user` ObjectId. The history controller checks both the JWT user and the MongoDB query, so a logged-in user cannot request another user's history.

## API routes

### Authentication

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Analysis

- `POST /api/upload` — authenticated
- `GET /api/download/:filename` — authenticated

### History

- `GET /api/users/:userId/history` — authenticated and owner-only
- `GET /api/users/:userId/history/:historyId` — authenticated and owner-only

### Health

- `GET /api/health`

## Error handling

Request-level failures are returned as JSON instead of crashing the Express request handler. The backend handles:

- invalid credentials
- duplicate accounts
- expired/invalid tokens
- missing files
- unsupported extensions
- oversized uploads
- malformed datasets
- FastAPI unavailable
- FastAPI analysis errors
- missing cleaned files
- invalid history IDs
- unauthorized history access
- MongoDB validation/duplicate-key errors
- unknown API routes

The FastAPI service also validates size, extension, empty files, parsing errors and pipeline failures.

Fatal process-level exceptions are logged. SIGINT/SIGTERM are handled with graceful HTTP-server and MongoDB shutdown.
