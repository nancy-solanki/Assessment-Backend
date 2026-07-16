# Meal Management System (Backend Developer Assessment)

A robust, performant Django REST Framework API for tracking, aggregating, and analyzing daily dietary intake. The application features soft deletion, precise datetime tracking, tag indexation, request-duration logging middleware, and optimized PostgreSQL aggregation.

---

## Architecture & Core Features

- **Clean Layered Architecture**:
  - **HTTP View Layer (`views.py`)**: Receives requests, handles pagination, parses/orders parameters, and coordinates view-specific responses.
  - **Validation & Serialization Layer (`serializers.py`)**: Validates input data payloads, enforces integrity constraints (e.g., past dates, valid tags), and guards against duplicate entries.
  - **Filtering Layer (`filters.py`)**: Separates request query extraction from database filters, supporting text searches, date range checks, and array-containment queries.
  - **Service Layer (`services.py`)**: Houses analytics calculation logic (summaries and trends) to keep controllers slim and reusable.
  - **Utility Layer (`utils.py`)**: Contains helpers like data gap-filling for date ranges.
  - **Model/Database Layer (`models.py`)**: Inherits from a reusable metadata base model providing UUID primary keys, automatic audit timestamps, and soft deletion flags.
- **Request Logging Middleware**: Logs method, path, HTTP status, and precise processing duration (in milliseconds) for all requests.
- **Optimized Postgres Queries**: Utilizes GIN indexes, combined annotations, `JSONBAgg`, and single-query aggregations to optimize trends calculation and alleviate database load.

---

## Technology Stack

- **Core**: Python 3.12, Django 6.0.x, Django REST Framework 3.17.x
- **Database**: PostgreSQL 16
- **Package Management**: [uv](https://github.com/astral-sh/uv) (Extremely fast Rust-based Python dependency manager)
- **Containerization**: Docker, Docker Compose

---

## Project Structure

```text
Backend/
├── apps/
│   ├── core/                  # Shared base features (abstract models, request-logging middleware)
│   │   ├── middleware.py
│   │   └── models.py
│   └── meals/                 # Core Meal feature application space
│       ├── admin.py
│       ├── filters.py         # Advanced query-params extraction & DB filtering
│       ├── models.py          # Meal model with Choices & indexing configs
│       ├── serializers.py     # Custom DRF validators & duplicate-guard exceptions
│       ├── services.py        # Analytics (Aggregators and Trend Generators)
│       ├── tests.py           # Comprehensive integration and unit test suite
│       └── views.py           # Pagination & controller responses
├── config/                    # Main Django project configuration settings & URLs
├── Dockerfile                 # Docker configuration file
├── docker-compose.yml         # Container choreography profile
├── manage.py                  # Django administrative script
├── pyproject.toml             # uv & Python project meta and dependency profiles
├── uv.lock                    # Locked exact dependency tree
└── .env.example               # Config blueprint template
```

---

## Getting Started

### 1. Environment Setup

Copy `.env.example` to create your own configuration file:
```bash
cp .env.example .env
```

The application will read settings directly from `.env`:
*   `SECRET_KEY`: Django cryptographic key
*   `DB_NAME`: Database Name (Default: `meals`)
*   `DB_USER`: Database Username (Default: `postgres`)
*   `DB_PASSWORD`: Database Password (Default: `postgres`)
*   `DB_HOST`: Database IP Address (Use `db` inside Docker, `localhost` for local dev)
*   `DB_PORT`: Database Port (Default: `5432`)

---

### 2. Run with Docker Compose (Recommended)

Spins up the database container (configured with a healthy status check) and automatically runs initial migrations followed by the web application server:

```bash
# Build and run containers
docker compose up --build

# Run Django tests inside the web container
docker compose exec web uv run python manage.py test
```

The server will be reachable at `http://localhost:8000`.

---

### 3. Run Locally (Traditional Development)

To run the project directly on your host machine, make sure you have [uv](https://github.com/astral-sh/uv) installed.

1.  **Install dependencies and prepare virtual environment:**
    ```bash
    uv sync
    ```

2.  **Start your local PostgreSQL service**, then create a database matching your `.env` configuration.

3.  **Run migrations:**
    ```bash
    uv run python manage.py migrate
    ```

4.  **Seed database (Optional):**
    If seed helper data exists (e.g., `seed_meals.json`), load it into your database:
    ```bash
    uv run python manage.py loaddata seed_meals.json
    ```

5.  **Run development server:**
    ```bash
    uv run python manage.py runserver
    ```

6.  **Run tests:**
    ```bash
    uv run python manage.py test
    ```

---

## API Documentation

### 1. Create a Meal
*   **Endpoint**: `POST /api/meals/`
*   **Payload**:
    ```json
    {
      "name": "Grilled Salmon Salad",
      "calories": 420,
      "protein_g": 35,
      "carbs_g": 12,
      "fat_g": 26,
      "tags": ["high-protein", "low-carb"],
      "eaten_at": "2026-07-16T12:30:00Z"
    }
    ```
*   **Response (201 Created)**:
    ```json
    {
      "id": "e0b82f0a-aebd-48d8-9993-9c884260dfcb",
      "name": "Grilled Salmon Salad",
      "calories": 420,
      "protein_g": 35,
      "carbs_g": 12,
      "fat_g": 26,
      "tags": ["high-protein", "low-carb"],
      "eaten_at": "2026-07-16T12:30:00Z",
      "created_at": "2026-07-16T12:32:00.123456Z",
      "updated_at": "2026-07-16T12:32:00.123456Z"
    }
    ```
*   *Validation rules: Cannot have future dates, empty names, or out-of-boundary nutrition numbers. Detects exact duplicates (same name and timestamp) and throws 409 Conflict.*

### 2. List & Filter Meals
*   **Endpoint**: `GET /api/meals/`
*   **Query Parameters** (All optional, combinable):
    *   `search` (string): Case-insensitive match on meal names.
    *   `date` (YYYY-MM-DD): Filter meals eaten on target date.
    *   `start_date` (YYYY-MM-DD): Filter meals eaten on or after target date.
    *   `end_date` (YYYY-MM-DD): Filter meals eaten on or before target date.
    *   `tags` / `tag` (CSV list): Returns meals containing *all* specified tags (e.g. `tags=vegan,high-protein`).
    *   `ordering` (CSV list): Fields to order results (e.g. `-calories,eaten_at`). Available fields: `name`, `calories`, `protein_g`, `carbs_g`, `fat_g`, `eaten_at`, `created_at`, `updated_at`.
    *   `page` (int): Number of page to fetch (Default: `1`).
    *   `page_size` (int): Items per page dynamically constrained (Default: `10`, Max: `100`).
*   **Response (200 OK)**: Standard paginated response.

### 3. Retrieve or Soft-Delete a Meal
*   **Endpoints**:
    *   `GET /api/meals/<uuid:id>/`
    *   `DELETE /api/meals/<uuid:id>/`
*   **Response (200 OK / 204 No Content)**
*   *Note: Soft-deleted meals are excluded from all query lists and return 404 (Not Found) on retrieval.*

### 4. Fetch Filters-Aware Summary
*   **Endpoint**: `GET /api/meals/summary/`
*   **Query Parameters**: Accepts the same filter query parameters as the List endpoint (`search`, `date`, `start_date`, `end_date`, `tags`).
*   **Response (200 OK)**:
    ```json
    {
      "total_meals": 12,
      "total_calories": 5240,
      "total_protein": 312,
      "total_carbs": 480,
      "total_fat": 190,
      "meal_names": ["Grilled Salmon Salad", "Oatmeal", "Protein Shake"],
      "unique_tags": ["high-protein", "low-carb", "vegetarian"],
      "goal_kcal": 2000,
      "remaining_kcal": -3240
    }

    ```

### 5. Fetch Daily Trends
*   **Endpoint**: `GET /api/meals/trends/`
*   **Query Parameters**:
    *   `days` (int): Lookback history window length (Default: `7`).
    *   `goal` (int): Daily calorie budget goal (Default: `2000`).
    *   Also accepts structural search & tag parameters (`search`, `tags`).
*   **Response (200 OK)**: Returns day-by-day aggregates (filling days with 0 metrics if no meal was eaten) together with compliance analytics (days met, exceeded, or missed):
    ```json
    {
      "days": [
        {
          "date": "2026-07-10",
          "total_calories": 1850,
          "total_protein": 110,
          "total_carbs": 160,
          "total_fat": 65
        },
        {
          "date": "2026-07-11",
          "total_calories": 2200,
          "total_protein": 135,
          "total_carbs": 210,
          "total_fat": 75
        }
      ],
      "stats": {
        "average_calories": 2025,
        "days_above_goal": 1,
        "days_below_or_equal_goal": 1
      }
    }
    ```

---

## Deployment Architectures

### 1. Backend on Render (using Docker)
Render supports deploying Django applications directly using the `Dockerfile` we created in the `Backend` directory.

- **Deployment Steps**:
  1. Create a new **Web Service** on Render.
  2. Connect your Git repository.
  3. Set the **Language/Runtime** to `Docker`.
  4. Specify the **Docker Path** to `./Backend/Dockerfile` (or just `Dockerfile` if deployment root is changed).
  5. Add Environment Variables under the Render dashboard:
     - `SECRET_KEY`: A unique random string
     - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: Credentials pointing to your production database (e.g. Render PostgreSQL Database instance).
     - `ALLOWED_HOSTS`: Set to your Render app domain (e.g., `your-app-name.onrender.com`).
  6. Render will build the Docker container and start serving the API.

---

### 2. Frontend on Vercel (Zero-Docker Deployment)
**Important**: Vercel does not build or run applications from custom `Dockerfiles`. Instead, Vercel is designed to directly build and deploy Static/Serverless applications directly from source repositories.

- **Deployment Steps**:
  1. Push your frontend code inside the `Frontend` sibling directory to GitHub.
  2. Create a new project on **Vercel**.
  3. Select your Git repository and set the **Root Directory** to `Frontend/`.
  4. Vercel will automatically detect your build engine (Vite, Next.js, etc.).
  5. Enter the Environment Variables (e.g., `VITE_API_URL` pointing to your Render Backend domain).
  6. Click **Deploy**. Vercel will trigger serverless static builds, host the files on edge networks, and give you an active URL.

---

### 3. Frontend Dockerfile (For Local Development orchestration)
If you wish to host the frontend elsewhere as a container, or to Orchestrate local execution via the provided `docker-compose.yml`, create a `Dockerfile` at `Frontend/Dockerfile` with the following content:

```dockerfile
# Stage 1: Build static assets
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve static files with Nginx
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Additionally, for local development (without rebuilding on every change), you can build the Frontend development container inside Compose by uncommenting the `frontend` block in `docker-compose.yml` and using the following development-focused `Dockerfile` in your `Frontend` folder:

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
```

---

## Technical Implementations, Design Decisions, & Tradeoffs

### 1. Summary Aggregation Mechanism
The `/api/meals/summary/` endpoint fetches total dietary statistics (calories, macros, associated unique tags, list of eaten meal names) by performing SQL-level aggregations inside **exactly one** QuerySet database hit.
Instead of loading thousands of database rows into memory and doing mathematical operations or map-reduce logic in Python, the backend leverages Django ORM's `aggregate` feature combined with PostgreSQL-specific functions (like `Coalesce` for null handling, `ArrayAgg` for names list aggregation, and `JSONBAgg` to aggregate tags arrays) ensuring O(1) server memory consumption.

### 2. Trends Calculation & Gap Filling
The `/api/meals/trends/` endpoint aggregates consumed meals day-by-day over an N-day historic window (default: 7, max: 30) against a configured daily caloric budget `goal`.
- **Query Optimization**: This endpoint makes **exactly one** query regardless of the `days` parameter. It annotates each record using PostgreSQL date truncations (`TruncDate("eaten_at")`), aggregates calories/macros, and orders them chronologically.
- **Python Gap-Filling**: Days inside the requested range that have no record in the database are filled in memory with zero-intake placeholders. This guarantees standard-length response arrays where a lookback window of N days always yields exactly N items.
- **Statistical Computations**: High-level statistical numbers (e.g. daily averages, highest caloric day, days exceeding goal) are calculated over the completed chronological sequence in memory, including empty placeholder days to keep the average daily intake correct.

### 3. Database Indexes
To maintain responsive query lookups in production, custom database indexes have been defined:
- **`eaten_at` Index**: Accelerates date-range query scans (crucial for `/api/meals/trends` and range filtering on list views).
- **`name` Index**: Accelerates search operations (`icontains` wildcard lookup).
- **`tags` GIN Index**: PostgreSQL-native Generalized Inverted Index (GIN) enables high-performance subset checking inside array fields (e.g., finding all meals matching tags `vegan,high-protein`).

### 4. Tradeoffs & Design Decisions
- **Postgres Dependency**: The application leverages `ArrayField` and `GINIndex`, which makes it Postgres-dependent and prevents running on SQLite. However, Postgres's native array features offer unmatched speed and clean queries for tags without requiring a bloated ManyToMany relationship table.
- **Validation-Time vs. Query-Time Normalization**: Name validation and duplicate checks are enforced inside the serializer validation lifecycle using Python string operations on database query windows rather than raw SQL or DB triggers. This separates application logic cleanly from the database layer, allowing easier migrations.

### 5. AI Usage
- Artificial intelligence was utilized during development to draft boilerplate Django project layouts, structure the custom abstract base models (implementing soft delete managers and UUID keys), formulate proper GIN index metadata on PostgreSQL array tags, and plan high-performance aggregate SQL statements. All AI-suggested code was subsequently benchmarked, refactored, and thoroughly verified via integration tests.


