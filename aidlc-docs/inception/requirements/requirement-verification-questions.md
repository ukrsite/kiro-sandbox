# Requirements Clarification Questions

Please answer each question by filling in the letter choice after the `[Answer]:` tag.
If none of the options match, choose the last option (Other) and describe your preference.

---

## Question 1: Target Services
Your request mentions `services/python-processor/` twice. Which services should have the Helm chart build-and-push CI pipeline configured?

A) Only `services/python-processor/`
B) Only `services/java-api/`
C) Both `services/python-processor/` AND `services/java-api/`
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2: Helm Chart Registry Target
You mentioned pushing Helm charts to "ECS". ECS (Elastic Container Service) is a container runtime, not a chart registry. The existing pipelines already reference ECR (`905418281081.dkr.ecr.us-east-1.amazonaws.com`) with `HELM_ECR: "true"`. Did you mean:

A) AWS ECR (Elastic Container Registry) — push Helm charts as OCI artifacts to ECR (already partially configured via `HELM_ECR: "true"`)
B) Artifactory ARM Helm repo — push to the existing `proj-santi-genai-helm-local` Helm repo
C) Both ECR and Artifactory
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3: Current Pipeline Gap
Looking at the existing `.gitlab-ci.yml` files, `HELM_CREATE: "true"` and `HELM_ECR: "true"` are already set, but there is no explicit Helm chart build/package/push job defined. What is missing?

A) The Helm chart package and push job is missing entirely — need to add a new job that packages the chart and pushes to ECR
B) The existing template (`backend-pipeline.gitlab-ci.yml`) already handles it via the flags — just need to verify/fix the variables
C) Need a completely new standalone Helm CI job independent of the shared template
D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 4: ECR Repository for Helm Charts
What ECR repository should the Helm charts be pushed to? The existing pipeline uses `905418281081.dkr.ecr.us-east-1.amazonaws.com` for Docker images.

A) Same ECR account/region (`905418281081.dkr.ecr.us-east-1.amazonaws.com`) — use a dedicated Helm charts repository path
B) A different ECR account or region (please specify after [Answer]: tag)
C) Use the same repository as the Docker image (OCI artifact alongside the image)
D) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 5: Helm Chart Directory
Each service has a chart at `chart/acceptance-criteria-refiner-backend/`. Should the CI pipeline use this existing chart directory, or is there a different chart path?

A) Use the existing `chart/acceptance-criteria-refiner-backend/` directory in each service
B) Use a different chart directory (please specify after [Answer]: tag)
C) Other (please describe after [Answer]: tag below)

[Answer]: C
services/python-processor/chart/python-processor

---

## Question 6: Security Extension
Should security extension rules (SECURITY-01 through SECURITY-15) be enforced for this CI pipeline configuration?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade pipelines)
B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)
X) Other (please describe after [Answer]: tag below)

[Answer]: B
