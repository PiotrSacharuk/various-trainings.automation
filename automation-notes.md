# 🎓 Automation Maestro: The Complete DevOps & GitOps Handbook

**Version:** 1.0.0
**Author:** Automation Maestro Student
**Description:** Complete documentation of modern CI/CD stack implementation for microservices, based on the "OrderFlow" project.

---

## 📑 Table of Contents

1.  [DevSecOps Philosophy & Shift Left](#1-devsecops-philosophy--shift-left)
2.  [Project Management (Python & Poetry)](#2-project-management-python--poetry)
3.  [Repository Hygiene (Pre-commit)](#3-repository-hygiene-pre-commit)
4.  [Containerization (Docker & Image Security)](#4-containerization-docker--image-security)
5.  [Continuous Integration (GitHub Actions)](#5-continuous-integration-github-actions)
6.  [Application Packaging (Helm)](#6-application-packaging-helm)
7.  [GitOps and ArgoCD](#7-gitops-and-argocd)
8.  [Safe Deployments (Argo Rollouts & Canary)](#8-safe-deployments-argo-rollouts--canary)
9.  [Scalability (HPA & Metrics)](#9-scalability-hpa--metrics)
10. [Troubleshooting & Battle Scars](#10-troubleshooting--battle-scars)
11. [Glossary of Terms](#11-glossary-of-terms)

---

## 1. DevSecOps Philosophy & Shift Left

### What is "Shift Left"?
Traditionally, security and quality tests were performed at the end of the process (before deployment). "Shift Left" involves moving these tests **as early as possible** in the software development cycle (to the left side of the timeline).

**Cost of fixing a bug:**
*   During code writing (Local): 1x
*   In CI pipeline: 10x
*   In production: 100x + reputation loss

### Layers of Protection in Our Project:
1.  **IDE/Local:** Pre-commit hooks (blocking commits with errors).
2.  **CI Pipeline:** SAST (Static Application Security Testing) and Linters.
3.  **Build:** Container image scanning (Trivy).
4.  **Cluster:** Network policies, User ID in containers.

---

## 2. Project Management (Python & Poetry)

Instead of `pip` and `requirements.txt`, we use **Poetry** for deterministic dependency management.

### Project Structure
```text
my-project/
├── pyproject.toml       # Main configuration file (dependencies + tool config)
├── poetry.lock          # Frozen library versions (SHA)
├── src/                 # Source code
│   └── main.py
└── tests/               # Tests
```

### Key Poetry Commands
```bash
# Project initialization
poetry init

# Adding production libraries
poetry add flask requests

# Adding development tools (won't be included in Docker image)
poetry add --group dev black isort flake8 bandit mypy pre-commit

# Installing environment
poetry install

# Running a script in venv
poetry run python src/main.py
```

---

## 3. Repository Hygiene (Pre-commit)

A tool that runs code validation scripts **before** Git allows the `commit` command to execute.

### Installation
```bash
poetry add --group dev pre-commit
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

### Configuration: `.pre-commit-config.yaml`
This is the heart of local automation.

```yaml
repos:
  # 1. Secret Detection (Critical for security!)
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        # --baseline allows ignoring old secrets (legacy)
        # --no-verify is needed on first run
        args: ["--baseline", ".secrets.baseline"]
        exclude: poetry.lock

  # 2. Basic File Hygiene
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-yaml            # Is YAML valid?
      - id: end-of-file-fixer     # Does file have empty line at end?
      - id: trailing-whitespace   # Removes trailing spaces

  # 3. Code Quality (Python)
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black                 # Automatic code formatting

  # 4. Commit Standards
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        # Enforces format: "feat: description", "fix: description", "chore: description"
        args: ["feat", "fix", "chore", "docs", "style", "refactor", "test", "ci"]
```

### Detect-Secrets Workflow
This tool prevents leaks of API keys, AWS credentials, Private Keys, etc.

1.  **Generate baseline:**
    ```bash
    detect-secrets scan > .secrets.baseline
    git add .secrets.baseline
    ```
2.  **Operation:** If code contains a high-entropy string, the commit is rejected.

---

## 4. Containerization (Docker & Image Security)

We build a lightweight and secure production image using **Multi-Stage Build**.

### Dockerfile (Best Practices)

```dockerfile
# STAGE 1: Builder (heavy image with compilers)
FROM python:3.12-slim as builder

WORKDIR /app

# Install Poetry
RUN pip install poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

# Install only production dependencies (without --dev)
RUN poetry install --no-dev --no-interaction --no-ansi

# STAGE 2: Runtime (lightweight production image)
FROM python:3.12-slim

WORKDIR /app

# Copy libraries from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

# SECURITY: Create non-root user
# Running applications as root is a security risk!
RUN useradd -m myuser
USER myuser

CMD ["python", "src/main.py"]
```

---

## 5. Continuous Integration (GitHub Actions)

The pipeline in `ci.yaml` runs on every Pull Request. It implements a "Defense in Depth" strategy.

### Key Sections of `.github/workflows/order-flow-ci.yaml`

#### A. Basic Configuration

```yaml
on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

permissions:
  contents: read
  packages: write
```

#### B. Job: Code Quality
Checks code quality before building (bandit, black, isort, flake8).

```yaml
jobs:
  code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install Poetry
        uses: snok/install-poetry@v1
      - name: Install dependencies
        run: poetry install

      # SAST - Security Scan
      - name: Run Security Scan (bandit)
        run: poetry run bandit -r src -ll

      # Linters
      - name: Run Linters
        run: |
          poetry run black --check src
          poetry run isort --check-only src
          poetry run flake8 src
```

#### C. Job: Build & Scan & Push
Builds Docker image, scans it (Trivy), generates SBOM and pushes to GHCR.

```yaml
  build-and-scan:
    needs: code-quality
    runs-on: ubuntu-latest
    permissions:
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t order-flow:${{ github.sha }} .

      # Scan image for CVE
      - name: Scan Docker image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: order-flow:${{ github.sha }}
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      # SBOM (Software Bill of Materials)
      - name: Install Syft
        run: |
          VERSION="v1.36.0"
          FILE="syft_${VERSION#v}_linux_amd64.tar.gz"

          for i in 1 2 3; do
            curl -sSfL -o syft.tgz "https://github.com/anchore/syft/releases/download/${VERSION}/${FILE}" && break
            echo "Retry $i..."
            sleep 3
          done

          tar -xzf syft.tgz
          sudo install syft /usr/local/bin/syft
          syft --version

      - name: Generate SBOM
        run: |
          syft order-flow:${{ github.sha }} -o json > sbom.json
          echo "SBOM generated successfully"
          ls -la sbom.json

      # Login and Push to GHCR
      - name: Login to GHCR
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Push image to GHCR
        run: |
          OWNER="${{ github.repository_owner }}"
          IMAGE_REPO="ghcr.io/$(echo "$OWNER" | tr '[:upper:]' '[:lower:]')/order-flow"
          docker tag order-flow:${{ github.sha }} $IMAGE_REPO:${{ github.sha }}
          docker tag order-flow:${{ github.sha }} $IMAGE_REPO:latest
          docker push $IMAGE_REPO:${{ github.sha }}
          docker push $IMAGE_REPO:latest
```

---

## 6. Application Packaging (Helm)

Helm is the "Package Manager for Kubernetes". It allows parametrizing YAML files.

### Chart Structure
```text
charts/orderflow/
├── Chart.yaml          # Chart name and version
├── values.yaml         # Default values
└── templates/          # YAML templates
    ├── deployment.yaml # Pod definitions (or Rollout)
    ├── service.yaml    # Network definitions
    └── hpa.yaml        # Autoscaling
```

### Templating
In `templates/*.yaml` files, we use Go Template syntax:

```yaml
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
replicas: {{ .Values.replicaCount }}
```

**Useful commands:**
```bash
# Render template locally (debugging)
helm template debug-release . --values values.yaml --debug

# Check for errors (lint)
helm lint .
```

---

## 7. GitOps and ArgoCD

### "Two Repos" Architecture
Separation of application code from infrastructure configuration.

1.  **App Repo (`various-trainings`)**:
    *   Where developers work.
    *   CI builds Docker image.
2.  **GitOps Config Repo (`various-trainings.gitops`)**:
    *   Where DevOps/Bots work.
    *   Contains Helm Chart and `values.yaml` files for each environment (dev, prod).
    *   GitOps repository for this project: `https://github.com/PiotrSacharuk/various-trainings.gitops`
    *   It is the "Source of Truth" for ArgoCD.

### Why Two Repositories?
1.  Avoid infinite loops in CI (commit from CI triggering CI).
2.  Clean separation of permissions (dev doesn't need write access to prod config).
3.  Clean history of infrastructure changes.

### ArgoCD Application
Definition of an object that links Git to the Cluster.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: orderflow-app
spec:
  source:
    repoURL: https://github.com/PiotrSacharuk/various-trainings.gitops
    path: orderflow
    targetRevision: HEAD
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      selfHeal: true  # Automatically fix "drift" (manual changes on cluster)
      prune: true     # Remove resources deleted from Git
```

---

## 8. Safe Deployments (Argo Rollouts & Canary)

We replace the standard `Deployment` object with a `Rollout` object to enable canary deployments.

### What is Canary Release?
Deploying a new version to a small percentage of traffic (e.g., 20%), verifying for errors, then full deployment.

### Rollout Configuration (`templates/deployment.yaml`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout # Instead of Deployment
metadata:
  name: orderflow
spec:
  # replicas: removed here because HPA manages it!
  strategy:
    canary:
      steps:
      - setWeight: 20         # Step 1: 20% traffic to new version
      - pause: {}             # Step 2: Wait for decision (Promote)
      - setWeight: 50         # Step 3: 50% traffic
      - pause: {duration: 30s}# Step 4: Wait 30s
      - setWeight: 100        # Step 5: 100% traffic
```

**Operation:**
- In ArgoCD UI we see **Paused** status during deployment.
- **Resume** button (or CLI `kubectl argo rollouts promote`) allows proceeding.
- **Abort** button (or CLI `undo`) immediately reverts to stable version.

---

## 9. Scalability (HPA & Metrics)

Automatic adjustment of pod count based on load.

### Requirements
1.  **Metrics Server**: Must be running on cluster (`minikube addons enable metrics-server`).
2.  **Requests/Limits**: Container must have defined `resources.requests.cpu`.

### HPA (`templates/hpa.yaml`)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orderflow-hpa
spec:
  scaleTargetRef:
    apiVersion: argoproj.io/v1alpha1
    kind: Rollout  # HPA must target Rollout!
    name: orderflow
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50 # Scale when average CPU > 50%
```

**Important:** If using HPA, **remove** the `replicas` field from `Rollout/Deployment` manifest. Otherwise HPA and GitOps will conflict (HPA sets 5, GitOps reverts to 1).

---

## 10. Troubleshooting & Battle Scars

List of problems encountered during deployment and their solutions.

### 🔴 Problem: `ErrImagePull` / `ImagePullBackOff`
*   **Symptom:** Pod doesn't start, events show "Authentication required".
*   **Cause:** Image in GHCR is private, cluster doesn't have token.
*   **Solution:**
    1. Create secret: `kubectl create secret docker-registry ghcr-secret ...`
    2. Add `imagePullSecrets` to pod specification in Helm.

### 🔴 Problem: ArgoCD doesn't see changes (Replicas 1 vs 5)
*   **Symptom:** Git has `replicaCount: 5`, ArgoCD Syncs, but cluster still shows `1`.
*   **Cause:** Parameter value was **overridden** in ArgoCD Application definition. Application parameters have priority over Git.
*   **Solution:** Remove override in ArgoCD UI (Parameters tab).

### 🔴 Problem: GitHub Actions doesn't see `ci.yaml`
*   **Symptom:** Push to branch doesn't trigger pipeline.
*   **Cause:** File was in `automation/.github/workflows/`, but GitHub looks in root `.github/workflows/`.
*   **Solution:** Move file to root and add `defaults.run.working-directory` in YAML.

### 🔴 Problem: Helm Template Error
*   **Symptom:** `Error converting YAML to JSON: did not find expected key`.
*   **Cause:** Indentation error in `deployment.yaml` file in `range` loop for environment variables.

---

## 11. Glossary of Terms

*   **CI (Continuous Integration):** Frequent code integration (merge), automated tests and artifact building.
*   **CD (Continuous Delivery):** Automatic delivery of code to environments (staging/prod), sometimes with manual approval.
*   **GitOps:** Operational model where Git is the single source of truth for infrastructure.
*   **Drift:** Difference between state in Git and actual state on cluster.
*   **Canary Release:** Deployment technique involving gradual rollout of new version.
*   **Monorepo:** Single repository containing code for multiple projects/services.
*   **SBOM (Software Bill of Materials):** List of all components and libraries in software (important for security).
