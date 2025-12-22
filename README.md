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

### 2.1. First start (one-time initialization)

On the very first run, use the `first_start.sh` helper script, which initializes `user_data/` and then brings up the Docker stack, building the image if needed:

```bash
./first_start.sh
```

Under the hood this will:
- Run `init_user_data.sh` to create/populate the `user_data/` directory
- Run `docker compose up -d --build` to build the multi-stage image defined in `Dockerfile` (backend + frontend + nginx) and start a single container exposing the web UI and API on port `80`

### 2.2. Subsequent starts

After the first initialization, you can start the stack directly with Docker Compose (without forcing a rebuild every time):

```bash
docker compose up -d
```

### 2.3. Access the application

- Web UI: `http://localhost/`
- API (via reverse proxy): `http://localhost/api`
- API docs (via reverse proxy): `http://localhost/docs`

### 2.4. Stop the stack

```bash
docker compose down
```

Volumes under `user_data/` are mounted into the container so that configuration and database files persist across restarts.

### 2.5. Environment variables

The container supports a couple of environment variables that control runtime behavior:

- `TIMEZONE`: timezone used by the backend (default: `Europe/Rome`)
- `SCHEDULER_INTERVAL_SECONDS`: polling interval for the scheduler loop (default: `5` seconds)

When using Docker Compose, you can configure them in `compose.yaml` under the `environment` section of the `edge-mining` service. For example:

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
```
### 2.6. Core interactive CLI mode

Once the container is running in the background with:

```bash
docker compose up -d
```

you can open an interactive Core CLI session inside the running container using `docker compose exec` and the startup command described in the `core` README:

```bash
docker compose exec edge-mining python -m edge_mining cli interactive
```

This command:
- enters the `edge-mining` service container defined in `compose.yaml`
- starts the backend in **interactive CLI** mode, allowing you to manage miners, energy sources, controllers, policies, etc. via a text-based menu.

To see the available CLI options you can run:

```bash
docker compose exec edge-mining python -m edge_mining cli --help
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

The `first_start.sh` script already runs `init_user_data.sh` for you, so in normal usage you do not need to call it manually on the first run.

If you prefer to manage things yourself, you can still run the helper script directly to create and populate the `user_data/` directory with default files:

```bash
./init_user_data.sh
```

This script:
- Creates the `user_data/` structure if missing
- Copies example optimization policies into `user_data/optimization_policies/`
- Ensures a `user_data/edgemining.db` file exists (copying one from `core/` if present, or creating an empty file otherwise)

You may want to re-run it if you intentionally delete the `user_data/` folder and want to restore the default structure.

---

## 4. Useful Tips

- **Logs**: Use `docker compose logs -f` to inspect services when running with Docker.
- **Rebuild after changes**: If you change backend or frontend code, re-run `docker compose up -d --build` (or `./first_start.sh` if you prefer the one-shot helper) to rebuild images.

## 5. Troubleshooting

- If containers fail to start, check logs:

```bash
docker compose logs
```

- If ports are already in use (80), stop the conflicting services or adjust ports and Nginx configuration.
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
