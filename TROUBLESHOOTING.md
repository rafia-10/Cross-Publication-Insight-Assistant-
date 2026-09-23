# Troubleshooting and Maintenance Guide

## 1. API Does Not Start

### Symptom
FastAPI fails to start.

### Checks
- Verify Python version.
- Verify dependencies are installed.
- Verify `.env` exists.
- Verify the configured API key.
- Check whether port 8000 is already in use.

## 2. Streamlit Does Not Load

### Checks
- Verify the API is running.
- Verify port 8501 is available.
- Check Docker container logs.

## 3. Repository Ingestion Fails

### Possible causes
- Invalid GitHub URL
- Private repository
- Repository does not exist
- GitHub API rate limit
- Network failure

### Recommended action
Verify the repository URL and GitHub accessibility, then inspect application logs.

## 4. LLM Requests Fail

### Possible causes
- Missing API key
- Invalid model configuration
- Provider outage
- Rate limit

### Recommended action
Check `.env`, provider availability, and application logs.

## 5. Retrieval Returns No Results

### Possible causes
- Repository has not been indexed
- ChromaDB data is missing
- Query is unrelated to indexed content
- Embedding/retrieval failure

### Recommended action
Verify that project ingestion completed successfully and that ChromaDB data exists.

## 6. Database Errors

Check the configured DATABASE_URL and database availability.

## 7. Docker Issues

Check container status:

docker compose ps

View logs:

docker compose logs api
docker compose logs frontend

Restart:

docker compose down
docker compose up --build

## Maintenance

Regular maintenance should include:

- Reviewing application logs
- Checking service health
- Updating dependencies
- Reviewing API/provider failures
- Cleaning obsolete indexed project data
- Running the test suite after changes
- Running the evaluation suite after changes
- Updating environment configuration when required
