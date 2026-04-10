# kiro-sandbox

## What this is

Sandbox multi-service stack (Docker Compose).

Services:
`java-api` (Spring Boot) on `:8088`, `python-processor` (FastAPI) on `:5000`, `node-gateway` (Express) on `:3000`, and aggregated `swagger-ui` on `:8888`.

## Run locally

From the repo root:

```bash
docker compose up --build
```

Once healthy:
- Gateway health: `GET http://localhost:3000/health`
- Gateway API docs: `http://localhost:3000/api-docs`
- Aggregated API docs (single entry point): `http://localhost:8888`

Gateway endpoints:
- `GET  http://localhost:3000/api/users`
- `POST http://localhost:3000/api/process/users`
- `POST http://localhost:3000/api/reports/generate`

## Deploying python-processor via CI

The pipeline triggers automatically when files under `services/python-processor/` change on push.

1. The root `.gitlab-ci.yml` detects changes and triggers the child pipeline at `services/python-processor/.gitlab-ci.yml`.
2. The `version` job determines the build version:
   - `main` branch: semantic-release computes the next semver (e.g. `1.0.3`).
   - Other branches: uses `{base-version}-{commit-hash}` (e.g. `1.0.2-7a1946f1`).
3. The container image is built with Kaniko and pushed to Artifactory.
4. `publish container ECR` copies the image to AWS ECR with the release version tag.
5. `create helm chart` packages the Helm chart and pushes it to the Helm repo.
6. `helm publis ECR` pushes the chart to the ECR-based Helm registry.
7. On `main`, semantic-release creates a Git tag, updates `CHANGELOG.md` and `.version`, and publishes a GitLab release.

No manual steps needed — merge to `main` for a production release, push to any other branch for a hash-tagged pre-release build.

## Kiro IDE/CLI (requirements flow)

Use Kiro to gather Jira requirements with the tag:
`Using AI-DLC, ...`

Quick steps:
1. Open Kiro IDE (or run Kiro CLI) from this repo.
2. Paste your Jira context (key, problem, users, scope, constraints).
3. Start prompt with: `Using AI-DLC, help me gather requirements for Jira <KEY>`.
4. Ask for: scope, functional/non-functional requirements, acceptance criteria (Given/When/Then), risks, and open questions.
5. Copy the output into the Jira description and AC sections or Gitlab CI variable.


