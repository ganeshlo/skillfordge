# LearnOS

LearnOS is an enterprise-ready learning operating system. The current incremental build includes identity and onboarding, tenant-aware access, roadmaps, the learning dashboard, and a Monaco-based coding workspace with versioned files and an isolated execution control plane.

Architecture and delivery decisions are documented under [`docs/`](docs/). Unfinished capabilities remain disabled instead of simulating production behavior.

## Quick start with Docker

```bash
cp .env.example .env
docker compose --profile runner-images build kotlin-runner-image
docker compose up --build
```

Open <http://localhost:3000>. The API is available at <http://localhost:8000/api/v1>, API documentation at <http://localhost:8000/api/docs/>, and liveness at <http://localhost:8000/api/v1/health/live/>.

AI provider configuration is reserved for the AI module and no provider call is made yet.

Payment and subscription setup is documented in [`docs/PAYMENT_SUBSCRIPTION.md`](docs/PAYMENT_SUBSCRIPTION.md).

### Secure code execution

LearnOS never runs server-executed source in Django, Celery, React, or the controller process. Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, PHP, Ruby, Kotlin, and SQL run in short-lived language containers. HTML, CSS, and React use a browser preview iframe without application-origin access. To enable Run/Stop, set these values in `.env`:

```env
EXECUTION_CONTROLLER_URL=http://execution-controller:8080
EXECUTION_CONTROLLER_SECRET=replace-with-a-long-random-secret
SANDBOX_BACKEND=docker
DOCKER_GID=991
```

`DOCKER_GID` must match the group of `/var/run/docker.sock` (`stat -c '%g' /var/run/docker.sock` on Linux; the included local Colima configuration uses `991`). User-code containers do not receive the socket. They run without network access or Linux capabilities, with a read-only root filesystem and bounded processes, CPU, memory, time, and output. The controller also supports a remote hardened provider for production; see [`services/execution-controller/README.md`](services/execution-controller/README.md).

Without a ready sandbox backend, the editor remains usable and Run fails closed. Controller health is available at <http://localhost:8080/health/ready>.

For a public deployment, set `DJANGO_DEBUG=false`, replace `DJANGO_SECRET_KEY` with a long random secret, and configure the allowed hosts/origins for your domain. Production mode enables secure cookies, HTTPS redirect, proxy SSL handling, and HSTS.

## Local development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The Docker stack uses PostgreSQL on host port `5433`; SQLite is only a fallback when `DATABASE_URL` is omitted. Optional development seed data is created with `python manage.py seed_development`.

## CI/CD

Pull requests run backend and execution-controller tests, build the React production bundle, and validate all Docker images. A push to `main` publishes versioned backend, frontend, and execution-controller images to GitHub Container Registry (`ghcr.io`) using the commit SHA and `latest` tags.
