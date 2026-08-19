# 🚀 Automation Maestro Capstone: E-Commerce Microservice

A production-ready Python microservice built to demonstrate modern DevOps practices, including "Shift Left" security, GitOps, and Autoscaling.

## 📋 Project Roadmap & Status

### Phase 1: Foundations & Hygiene ✅
- [x] **Project Initialization**: Repository setup with standard structure.
- [x] **Pre-commit Hooks**:
  - [x] `detect-secrets` to prevent credential leaks.
  - [x] `check-yaml`, `trailing-whitespace`, `end-of-file-fixer` for code hygiene.
- [x] **Commitlint**: Enforcing Conventional Commits (e.g., `feat:`, `fix:`, `chore:`).

### Phase 2: CI & Security ✅
- [x] **GitHub Actions Pipeline**: Workflow for CI/CD configured.
- [x] **Dependency Management**: Poetry integrated into CI pipeline.
- [x] **Static Analysis (SAST)**:
  - [x] `bandit` security scanning running in CI.
  - [x] `black`, `isort`, `flake8` linters validating code quality.
- [x] **Docker Build**: Automated image creation.
- [x] **Image Security**: Scanning container images with Trivy.

### Phase 3: Packaging (Helm) ✅
- [x] Create a reusable Helm Chart.
- [x] Parameterize values for different environments (dev/prod).

### Phase 4: GitOps (ArgoCD) ✅
- [x] Setup GitOps configuration repository.
- [x] Install ArgoCD on Kubernetes.
- [x] Implement automated sync between Git and Cluster.
   - [x] setup: https://github.com/PiotrSacharuk/various_trainings.gitops

### Phase 5: Safe Deployment Strategy ✅
- [x] Install Argo Rollouts.
- [x] Implement Canary Release strategy (traffic splitting).

### Phase 6: Scalability & Reliability ✅
- [x] Configure Horizontal Pod Autoscaler (HPA).
- [x] Stress test the application to verify autoscaling.

---

## 🛠️ Tech Stack

- **Language**: Python 3.14+ (Poetry)
- **CI/CD**: GitHub Actions
- **Infrastructure**: Kubernetes (Minikube/K3s)
- **GitOps**: ArgoCD
- **Packaging**: Helm
- **Observability**: Prometheus/Grafana (planned)
