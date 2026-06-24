⚠️ **Disclaimer**: *This project is in a preliminary state and under active development. Features and functionality may change significantly.*

Edge Mining ⚡️🌞 is a software to optimize the use of excess energy, especially from renewable sources, through Bitcoin mining. This system automates the turning on and off of ASIC miner devices based on energy availability, production forecasts, and user-defined policies.

---

## 1. Prerequisites

- Git
- Docker and Docker Compose

Clone the repository and move into the project root:

```bash
git clone https://github.com/edge-mining/app.git
cd app/
```

## Run with Docker Compose

You can run Edge Mining using `docker compose` in daemon mode using the provided `compose.yaml`.

**Important:** The `user_data/` directory is mounted as a volume, ensuring your database, policies, and backups persist even when the container is removed.

### 2.1. First start (one-time initialization)

On the very first run, use the `first_start.sh` helper script from `scripts` folder, which initializes `user_data/`, creates the necessary directory structure, and then brings up the Docker stack, building the image if needed:

```bash
./scripts/first_start.sh
```

Under the hood this will:
- Run `init_user_data.sh` to create/populate the `user_data/` directory
- Run `docker compose up -d --build` to build the multi-stage image defined in `Dockerfile` (backend + frontend + nginx) and start a single container exposing the web UI and API on port `80`

Now you can:
- Place your optimization policy YAML files in `user_data/policies/`
- Find rule examples in `user_data/examples/start/` and `user_data/examples/stop/`
- Access the database at `user_data/db/edgemining.db`
- Find automatic backups in `user_data/db/backups/`

### 2.2. Subsequent starts

After the first initialization, you can start the stack directly with Docker Compose (without forcing a rebuild every time):

```bash
docker compose up -d
```

> **Note:** Volumes under `user_data/` are mounted into the container so that configuration and database files persist across restarts.

### 2.3. Access the application

- Web UI: `http://localhost/`
- API (via reverse proxy): `http://localhost/api`
- API docs (via reverse proxy): `http://localhost/docs`

To see logs:

```bash
docker compose logs -f
```

### 2.4. Stop the stack

```bash
docker compose down
```

### 2.5. Environment variables

The container supports a couple of environment variables that control runtime behavior:

- `TIMEZONE`: timezone used by the backend (default: `Europe/Rome`)
- `LATITUDE` and `LONGITUDE`: used for sunrise/sunset calculations
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

User-specific data lives in the `user_data/` folder of the this application folder. This is where you can place your own configuration files, policies, and where the backend will store its database.:

- `user_data/policies/` – optimization policy YAML files (automatically copied from `core/data/policies/` on first run if missing)
- `user_data/examples/` – example rules files (copied from `core/data/examples/` on first run)
- `user_data/db/edgemining.db` – SQLite database file used by the backend

### 3.1 Initialize user data (recommended)

The `first_start.sh` script already runs `init_user_data.sh` for you, so in normal usage you do not need to call it manually on the first run.

If you prefer to manage things yourself, you can still run the helper script directly to create and populate the `user_data/` directory with default files:

```bash
./scripts/init_user_data.sh
```

This script:
- Creates the `user_data/` structure if missing
- Copies example optimization policies into `user_data/policies/`
- Copies example rules files into `user_data/examples/`
- Ensures a `user_data/db/edgemining.db` file exists (copying one from `core/` if present, or creating an empty file otherwise)

You may want to re-run it if you intentionally delete the `user_data/` folder and want to restore the default structure.

---

## 4. Useful Tips

- **Logs**: Use `docker compose logs -f` to inspect services when running with Docker.
- **Rebuild after changes**: If you change backend or frontend code, re-run `docker compose up -d --build` (or `./scripts/first_start.sh` if you prefer the one-shot helper) to rebuild images.

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

## 6. Updating the Application

When a new version is available, use the `update.sh` script to pull the latest changes and restart the application:

```bash
./scripts/update.sh
```

This script will:
- Pull the latest changes from the current branch
- Re-initialize `user_data/` (copies missing defaults only)
- Rebuild and restart the Docker stack

### 6.1 Switching Branch

The `main` branch is the active development branch. For regular updates, stay on `main`; to test a feature branch, use the `switch_branch.sh` script:

```bash
./scripts/switch_branch.sh
```

This script will:
- Fetch the latest remote branches
- Display a numbered list of all available branches
- Prompt you to select the desired branch
- Switch to the selected branch
- Rebuild and restart the Docker stack

---

## 7. Development

For local development setup (without Docker), available `make` commands, linting, testing, and contribution guidelines, see:

- [`DEVELOPMENT.md`](DEVELOPMENT.md) — step-by-step setup and daily workflow
- [`DEV_TOOLS.md`](DEV_TOOLS.md) — linting, formatting, testing tools and configuration
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution guidelines and PR rules
