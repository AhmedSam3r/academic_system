# Academic Enrollment System

This project provides a backend service for processing and analyzing student enrollments.
It is built with **Django**, **Celery**, and **RabbitMQ**, and is designed to scale to **10M+ enrollment records** while maintaining performant analytics queries.

---

# Tech Stack

* Python
* Django
* PostgreSQL
* Celery
* RabbitMQ
* Redis
* Docker / Docker Compose
* Gunicorn

---

# Features

* Batch enrollment processing
* Asynchronous background processing
* Retry + Dead Letter Queue architecture
* High-performance reporting queries
* Dockerized environment
* API documentation

---

# Running the Project

## Running the Project with Poetry

This project uses **Poetry** for dependency management and virtual environments.


## 1. Run Locally (Without Docker)

### 1. Install Poetry

If Poetry is not installed, install it using the official installer:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Verify the installation:

```bash
poetry --version
```

You may need to add Poetry to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

### 2. Install Project Dependencies

From the project root (where `pyproject.toml` is located), run:

```bash
poetry install
```

This will:

* create a virtual environment
* install all project dependencies

---

### 3. Activate the Virtual Environment

```bash
poetry shell
```

Alternatively, you can run commands without activating the shell:

```bash
poetry run <command>
```

Example:

```bash
poetry run python manage.py runserver
```

---

### 4. Run Database Migrations

```bash
poetry run python manage.py migrate
```

---

### 5. Run the Django Application

```bash
poetry run python manage.py runserver
```

The API will be available at:

```
http://localhost:8000
```

---

### 6. Start the Celery Worker

```
poetry run celery -A config worker -Q main -l info
```



### Configure environment variables

Create a `.env.dev` file.

Example:

```
DB_NAME=academia
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Run database migrations

```bash
python manage.py migrate
```

### Start the Django server

```bash
python manage.py runserver
```

### Start Celery worker

```bash
celery -A config worker -Q main -l info
```

The worker listens only to the **main queue**.

---

# Running With Docker

The easiest way to run the full stack is using Docker Compose.

### Build containers

```bash
docker compose -f docker/docker-compose.yml build
```

### Start services

```bash
docker compose -f docker/docker-compose.yml up -d
```

### Check running containers

```bash
docker compose ps
```

### View logs

```bash
docker compose logs -f
```

---

# Services Started

The following services will start:

| Service       | Description                              |
| ------------- | ---------------------------------------- |
| backend       | Django application running with Gunicorn |
| celery_worker | Background task worker                   |
| postgres      | PostgreSQL database                      |
| redis         | Result backend for Celery                |
| rabbitmq      | Message broker                           |
| db_migrations | Runs migrations automatically            |

---

# API Documentation

Once the application is running, the API documentation can be accessed at:

```
http://localhost:8000/api/docs
```

Health check endpoint:

```
http://localhost:8000/v1/health-check/
```

---

# Architecture Overview

The system is designed for **high-throughput batch processing**.

## Enrollment Batch Flow

1. Client submits enrollment batch
2. API stores the batch metadata
3. Background processing task is queued
4. Celery worker processes the batch asynchronously
5. Each enrollment record is stored with status tracking

---

# Celery Queue Architecture

The message flow is designed to support retries and failure isolation.

```
main_exchange
      ↓
main_queue
      ↓ (failure)
main_exchange
      ↓
retry_queue (with TTL delay)
      ↓
main_queue (retry)
      ↓ (max retries exceeded)
dlx_exchange
      ↓
dead_letter_queue
```

### Main Queue

The `main` queue is where tasks are first processed.

Celery workers listen **only to this queue**.

```
celery -A config worker -Q main
```

This prevents workers from accidentally consuming retry or DLQ messages.

---

### Retry Queue

If a task fails, it is routed to a **retry queue** with a TTL delay.

Example:

```
retry_queue (TTL = 60s)
```

After TTL expires, the message is automatically routed back to the **main queue** for retry.

---

### Dead Letter Queue (DLQ)

If retries exceed the configured limit:

```
max_retries = 3
```

The message is sent to the **Dead Letter Queue**.

This allows:

* failure analysis
* manual reprocessing
* debugging corrupted messages

---

# Database Design

Two main tables are used:

### EnrollmentBatch

Stores metadata about each batch.

Fields:

* id
* status
* total_count
* processed_count

---

### Enrollment

Stores individual enrollment records.

Fields:

* student
* grade
* region
* school
* batch
* status
* error_message

---

# Performance Strategy (10M Records)

The reporting API must return results in **<500ms** with **10M records**.

The following optimizations are used.

---

## Database Indexing

Indexes are created on fields used in aggregation queries.

Example indexes:

```
student_id
region
grade
status
```

Composite indexes may also be used:

```
(region, grade)
```

These indexes allow PostgreSQL to quickly group records during aggregation.

---

## Aggregation Query

Example reporting query:

```
Enrollment.objects
    .values("region")
    .annotate(total_students=Count("student", distinct=True))
```

This query calculates the number of students per region.

---

## Why Indexing Matters

Without indexes:

* PostgreSQL scans **10M rows**

With indexes:

* PostgreSQL performs **index scans**
* drastically reducing query latency

---

# Generating Test Data

To simulate large datasets, a seeding script generates:

* up to **10M enrollments**
* randomized data using Faker

Example command:

```
poetry run python manage.py seed_enrollments
```

---

# Monitoring

RabbitMQ management dashboard:

```
http://localhost:15672
```

Default credentials:

```
guest / guest
```

---

# Future Improvements

Potential improvements for production:

* Materialized views for analytics queries
* Horizontal scaling of Celery workers
* Partitioned tables for enrollments

---

# Summary

This system is designed to support:

* High-volume enrollment ingestion
* Reliable asynchronous processing
* Fault-tolerant message handling
* Fast analytics queries on large datasets
