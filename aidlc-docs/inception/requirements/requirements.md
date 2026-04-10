# Requirements: Helm Chart CI Pipeline for python-processor

## Intent Analysis
- **User Request**: Configure CI pipeline for `services/python-processor/` to build and push Helm charts to AWS ECR
- **Request Type**: Enhancement — fixing/completing existing CI pipeline configuration
- **Scope**: Single service (`services/python-processor/`)
- **Complexity**: Simple — the shared template already supports Helm ECR publishing via feature flags; only variable corrections needed

## Functional Requirements

1. The `services/python-processor/.gitlab-ci.yml` pipeline MUST build and push the Helm chart at `services/python-processor/chart/python-processor/` to AWS ECR as an OCI artifact
2. The Helm chart MUST be pushed to the same ECR repository used for the Docker image: `905418281081.dkr.ecr.us-east-1.amazonaws.com`
3. The pipeline MUST use the existing shared template (`backend-pipeline.gitlab-ci.yml`) Helm ECR feature flags (`HELM_ECR: "true"`, `HELM_CREATE: "true"`, `HELM_PUBLISH: "true"`)
4. The `HELM_IMAGE` variable MUST reference the helm-yq container image (not a `docker push` command string)
5. The chart directory variable MUST point to `chart/python-processor` (not the default `chart/acceptance-criteria-refiner-backend`)

## Non-Functional Requirements

- Security rules: Skipped (PoC/prototype project)
- The fix MUST NOT break the existing Docker image build (`build container` job)
- Changes MUST be minimal — only correct the variables that are wrong or missing

## Key Findings from Existing Config

| Variable | Current Value | Issue |
|---|---|---|
| `HELM_IMAGE` | `docker push 905418281081.dkr.ecr.us-east-1.amazonaws.com/ci-cd/helm-yq:0.0.2` | Wrong — this is a command string, not an image reference. Should be `905418281081.dkr.ecr.us-east-1.amazonaws.com/ci-cd/helm-yq:0.0.2` |
| Chart path | Not set (defaults to `chart/acceptance-criteria-refiner-backend`) | Must be overridden to `chart/python-processor` |
| `HELM_ECR` | `"true"` | Correct |
| `HELM_CREATE` | `"true"` | Correct |
| `HELM_PUBLISH` | `"true"` | Correct |
