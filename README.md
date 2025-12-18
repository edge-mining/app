# Edge Mining App

This repository bundles the Edge Mining **core backend** and **web frontend** into a single runnable application.

Edge Mining is intended to be run via **Docker Compose**.

---

## 1. Prerequisites

- Git
- Docker and Docker Compose

Clone the repository and move into the project root:

```bash
git clone --recurse-submodules https://github.com/edge-mining/app.git
cd app/
```

---

## 2. Quick Start with Docker (Recommended)

This setup runs a **single container** that bundles:
- `core`: Edge Mining backend (FastAPI, automation engine)
- `frontend`: Vue web UI (served as static files)
- `nginx`: reverse proxy exposing everything on port `80`

### 2.1. Start the stack

From the project root (where `docker-compose.yml` is located):

```bash
docker compose up -d --build
```

Docker will:
- Build the multi-stage image defined in `Dockerfile` (backend + frontend + nginx)
- Start a single container named `edge-mining` exposing the web UI and API on port `80`

### 2.2. Access the application

- Web UI: `http://localhost/`
- API (via reverse proxy): `http://localhost/api`
- API docs (via reverse proxy): `http://localhost/docs`

### 2.3. Stop the stack

```bash
docker compose down
```

Volumes under `user_data/` are mounted into the container so that configuration and database files persist across restarts.

### 2.4. Environment variables

The container supports a couple of environment variables that control runtime behavior:

- `TIMEZONE`: timezone used by the backend (default: `Europe/Rome`)
- `SCHEDULER_INTERVAL_SECONDS`: polling interval for the scheduler loop (default: `5` seconds)

When using Docker Compose, you can configure them in `compose.yml` under the `environment` section of the `edge-mining` service. For example:

```yaml
services:
  edge-mining:
    environment:
      - TIMEZONE=Europe/Rome
      - SCHEDULER_INTERVAL_SECONDS=5
```

When running the image directly with `docker run`, you can pass them with `-e`:

```bash
docker run -d \
  -p 80:80 \
  -e TIMEZONE=Europe/Rome \
  -e SCHEDULER_INTERVAL_SECONDS=5 \
  edge-mining:latest
```

---

## 3. Configuration & Data

User-specific data lives in the `user_data/` folder:

- `user_data/optimization_policies/` – example optimization policy YAML files
- `user_data/edgemining.db` – SQLite database file used by the backend

On first run you can:
- Copy or adjust example policies from `optimization_policies/` into `user_data/optimization_policies/`
- Let the backend create `user_data/edgemining.db` automatically, or pre-populate it if you know what you are doing

### 3.1 Initialize user data (recommended)

Before starting the stack for the first time, you can use the helper script `init_user_data.sh` to create and populate the `user_data/` directory with default files:

```bash
./init_user_data.sh
```

This script typically:
- Creates the `user_data/` structure if missing
- Copies example optimization policies into `user_data/optimization_policies/`

You only need to run it once, or again if you intentionally delete the `user_data/` folder and want to restore the default structure.

---

## 4. Useful Tips

- **Logs**: Use `docker compose logs -f core` or `docker compose logs -f frontend` to inspect services when running with Docker.
- **Rebuild after changes**: If you change backend or frontend code, re-run `docker compose up -d --build` to rebuild images.

## 5. Troubleshooting

- If containers fail to start, check logs:

```bash
docker compose logs
```

- If ports are already in use (80, 5173, 8001), stop the conflicting services or adjust ports and Nginx configuration.
- If the UI cannot reach the API, verify:
  - Backend container is healthy (`docker ps`)
  - Nginx is running and correctly proxying requests
  - Frontend is pointing to the right API URL.

## 6. Updating Submodules

This repository uses Git submodules for the `core` and `frontend` components. The submodules are configured to track the `dev` and `develop` branches respectively.

**After cloning**, the submodules will be checked out at the commit SHAs recorded in the parent repository. To update them to the latest commits from their respective branches:

```bash
# Update all submodules to the latest commits from their configured branches
git submodule update --remote --merge
```

**To update a specific submodule:**

```bash
# Update core submodule to latest dev branch
cd core
git checkout dev
git pull origin dev
cd ..

# Update frontend submodule to latest develop branch
cd frontend
git checkout develop
git pull origin develop
cd ..
```

**Note:** After updating submodules, if you want to commit the new submodule references to the parent repository:

```bash
git add core frontend
git commit -m "Update submodules to latest dev/develop branches"
```
