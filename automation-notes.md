# 🎓 Automation Maestro: The Complete DevOps & GitOps Handbook

**Wersja:** 1.0.0
**Autor:** Automation Maestro Student
**Opis:** Kompletna dokumentacja wdrożenia nowoczesnego stacku CI/CD dla mikroserwisów, oparta na projekcie "OrderFlow".

---

## 📑 Spis Treści

1.  [Filozofia DevSecOps i Shift Left](#1-filozofia-devsecops-i-shift-left)
2.  [Zarządzanie Projektem (Python & Poetry)](#2-zarządzanie-projektem-python--poetry)
3.  [Higiena Repozytorium (Pre-commit)](#3-higiena-repozytorium-pre-commit)
4.  [Konteneryzacja (Docker & Image Security)](#4-konteneryzacja-docker--image-security)
5.  [Continuous Integration (GitHub Actions)](#5-continuous-integration-github-actions)
6.  [Pakowanie Aplikacji (Helm)](#6-pakowanie-aplikacji-helm)
7.  [GitOps i ArgoCD](#7-gitops-i-argocd)
8.  [Safe Deployments (Argo Rollouts & Canary)](#8-safe-deployments-argo-rollouts--canary)
9.  [Skalowalność (HPA & Metrics)](#9-skalowalność-hpa--metrics)
10. [Troubleshooting & Battle Scars](#10-troubleshooting--battle-scars)
11. [Słownik Pojęć](#11-słownik-pojęć)

---

## 1. Filozofia DevSecOps i Shift Left

### Co to jest "Shift Left"?
Tradycyjnie testy bezpieczeństwa i jakości odbywały się na końcu procesu (przed wdrożeniem). "Shift Left" polega na przesunięciu tych testów **jak najwcześniej** w cyklu wytwarzania oprogramowania (na lewą stronę osi czasu).

**Koszt naprawy błędu:**
*   Podczas pisania kodu (Local): 1x
*   W pipeline CI: 10x
*   Na produkcji: 100x + utrata reputacji

### Warstwy Ochrony w naszym projekcie:
1.  **IDE/Local:** Pre-commit hooks (blokada commitów z błędami).
2.  **CI Pipeline:** SAST (Static Application Security Testing) i Linters.
3.  **Build:** Skanowanie obrazów kontenerów (Trivy).
4.  **Cluster:** Polityki sieciowe, User ID w kontenerach.

---

## 2. Zarządzanie Projektem (Python & Poetry)

Zamiast `pip` i `requirements.txt`, używamy **Poetry** do deterministycznego zarządzania zależnościami.

### Struktura projektu
```text
my-project/
├── pyproject.toml       # Główny plik konfiguracyjny (zależności + config narzędzi)
├── poetry.lock          # Zamrożone wersje bibliotek (SHA)
├── src/                 # Kod źródłowy
│   └── main.py
└── tests/               # Testy
```

### Kluczowe komendy Poetry
```bash
# Inicjalizacja projektu
poetry init

# Dodawanie bibliotek produkcyjnych
poetry add flask requests

# Dodawanie narzędzi deweloperskich (nie trafią do obrazu Docker)
poetry add --group dev black isort flake8 bandit mypy pre-commit

# Instalacja środowiska
poetry install

# Uruchomienie skryptu w venv
poetry run python src/main.py
```

---

## 3. Higiena Repozytorium (Pre-commit)

Narzędzie, które uruchamia skrypty sprawdzające kod **zanim** Git pozwoli na wykonanie polecenia `commit`.

### Instalacja
```bash
poetry add --group dev pre-commit
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

### Konfiguracja: `.pre-commit-config.yaml`
To serce automatyzacji lokalnej.

```yaml
repos:
  # 1. Wykrywanie sekretów (Kluczowe dla bezpieczeństwa!)
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        # --baseline pozwala ignorować stare sekrety (legacy)
        # --no-verify jest potrzebne przy pierwszym uruchomieniu
        args: ["--baseline", ".secrets.baseline"]
        exclude: poetry.lock

  # 2. Podstawowa higiena plików
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-yaml            # Czy YAML jest poprawny?
      - id: end-of-file-fixer     # Czy plik ma pustą linię na końcu?
      - id: trailing-whitespace   # Usuwa spacje na końcach linii

  # 3. Code Quality (Python)
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black                 # Automatyczne formatowanie kodu

  # 4. Standard Commitów
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        # Wymusza format: "feat: opis", "fix: opis", "chore: opis"
        args: ["feat", "fix", "chore", "docs", "style", "refactor", "test", "ci"]
```

### Detect-Secrets Workflow
Narzędzie to zapobiega wyciekom kluczy API, AWS keys, Private Keys itp.

1.  **Generowanie bazy (Baseline):**
    ```bash
    detect-secrets scan > .secrets.baseline
    git add .secrets.baseline
    ```
2.  **Działanie:** Jeśli w kodzie pojawi się ciąg znaków o wysokiej entropii, commit zostanie odrzucony.

---

## 4. Konteneryzacja (Docker & Image Security)

Budujemy lekki i bezpieczny obraz produkcyjny używając **Multi-Stage Build**.

### Dockerfile (Best Practices)

```dockerfile
# ETAP 1: Builder (ciężki obraz z kompilatorami)
FROM python:3.10-slim as builder

WORKDIR /app

# Instalacja Poetry
RUN pip install poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

# Instalacja tylko zależności produkcyjnych (bez --dev)
RUN poetry install --no-dev --no-interaction --no-ansi

# ETAP 2: Runtime (lekki obraz produkcyjny)
FROM python:3.10-slim

WORKDIR /app

# Kopiowanie bibliotek z etapu builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

# SECURITY: Utworzenie użytkownika non-root
# Uruchamianie aplikacji jako root to ryzyko bezpieczeństwa!
RUN useradd -m myuser
USER myuser

CMD ["python", "src/main.py"]
```

---

## 5. Continuous Integration (GitHub Actions)

Pipeline w `ci.yaml` uruchamia się przy każdym Pull Requeście. Realizuje strategię "Defense in Depth".

### Kluczowe sekcje pliku `.github/workflows/ci.yaml`

#### A. Obsługa Monorepo
Jeśli projekt jest w podfolderze (np. `automation/`), musimy wskazać ścieżki.

```yaml
on:
  push:
    paths: ['automation/**'] # Trigger tylko przy zmianach w folderze
defaults:
  run:
    working-directory: ./automation # Domyślna ścieżka dla komend 'run'
```

#### B. Job: Code Quality
Sprawdza jakość kodu przed zbudowaniem.

```yaml
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: poetry install

      # SAST - Security Scan
      - name: Run Bandit
        run: poetry run bandit -r src -ll

      # Linters
      - name: Check Formatting
        run: poetry run black --check src
```

#### C. Job: Build & Scan & Push
Buduje obraz, skanuje go i wypycha do rejestru (GHCR).

```yaml
  build-and-scan:
    needs: code-quality # Zależność!
    permissions:
      packages: write # Uprawnienia do GHCR

    steps:
      - name: Build Docker
        run: docker build -t myapp:${{ github.sha }} .

      # Skanowanie obrazu na obecność CVE (Common Vulnerabilities and Exposures)
      - name: Run Trivy Scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:${{ github.sha }}'
          severity: 'CRITICAL,HIGH'
          exit-code: '1' # Zablokuj pipeline, jeśli znajdziesz dziury!

      # Logowanie i Push do GHCR
      - name: Login to GHCR
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Push
        run: docker push ghcr.io/user/repo:${{ github.sha }}
```

---

## 6. Pakowanie Aplikacji (Helm)

Helm to "Menadżer pakietów dla Kubernetesa". Pozwala sparametryzować pliki YAML.

### Struktura Chartu
```text
charts/orderflow/
├── Chart.yaml          # Nazwa i wersja chartu
├── values.yaml         # Domyślne wartości
└── templates/          # Szablony YAML
    ├── deployment.yaml # Definicja Podów (lub Rollout)
    ├── service.yaml    # Definicja sieciowa
    └── hpa.yaml        # Autoskalowanie
```

### Templating
W plikach `templates/*.yaml` używamy składni Go Template:

```yaml
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
replicas: {{ .Values.replicaCount }}
```

**Przydatne komendy:**
```bash
# Renderowanie szablonu lokalnie (debugowanie)
helm template debug-release . --values values.yaml --debug

# Sprawdzanie błędów (lint)
helm lint .
```

---

## 7. GitOps i ArgoCD

### Architektura "Two Repos"
Separacja kodu aplikacji od konfiguracji infrastruktury.

1.  **App Repo (`various-trainings`)**:
    *   Tu pracują programiści.
    *   CI buduje obraz Docker.
2.  **GitOps Config Repo (`various-trainings.gitops`)**:
    *   Tu pracują DevOps/Boty.
  *   Zawiera Helm Chart i pliki `values.yaml` dla każdego środowiska (dev, prod).
  *   Repozytorium GitOps dla tego projektu: `https://github.com/PiotrSacharuk/various-trainings.gitops`
    *   Jest "Źródłem Prawdy" dla ArgoCD.

### Dlaczego dwa repozytoria?
1.  Unikamy pętli nieskończoności w CI (commit z CI wyzwala CI).
2.  Czysty podział uprawnień (dev nie musi mieć write access do prod config).
3.  Czysta historia zmian infrastruktury.

### ArgoCD Application
Definicja obiektu, który łączy Git z Klastrem.

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
      selfHeal: true  # Automatycznie naprawiaj "drift" (ręczne zmiany na klastrze)
      prune: true     # Usuwaj zasoby usunięte z Git
```

---

## 8. Safe Deployments (Argo Rollouts & Canary)

Zastępujemy standardowy `Deployment` obiektem `Rollout`, aby umożliwić wdrożenia kanarkowe.

### Co to jest Canary Release?
Wdrażanie nowej wersji na mały procent ruchu (np. 20%), weryfikacja błędów, a następnie pełne wdrożenie.

### Konfiguracja Rollout (`templates/deployment.yaml`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout # Zamiast Deployment
metadata:
  name: orderflow
spec:
  # replicas: usunięte stąd, bo zarządza nimi HPA!
  strategy:
    canary:
      steps:
      - setWeight: 20         # Krok 1: 20% ruchu na nową wersję
      - pause: {}             # Krok 2: Czekaj na decyzję (Promote)
      - setWeight: 50         # Krok 3: 50% ruchu
      - pause: {duration: 30s}# Krok 4: Czekaj 30s
      - setWeight: 100        # Krok 5: 100% ruchu
```

**Obsługa:**
- W ArgoCD UI widzimy status **Paused** podczas wdrożenia.
- Przycisk **Resume** (lub CLI `kubectl argo rollouts promote`) pozwala przejść dalej.
- Przycisk **Abort** (lub CLI `undo`) natychmiast cofa do stabilnej wersji.

---

## 9. Skalowalność (HPA & Metrics)

Automatyczne dostosowanie liczby podów do obciążenia.

### Wymagania
1.  **Metrics Server**: Musi działać na klastrze (`minikube addons enable metrics-server`).
2.  **Requests/Limits**: Kontener musi mieć zdefiniowane `resources.requests.cpu`.

### HPA (`templates/hpa.yaml`)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orderflow-hpa
spec:
  scaleTargetRef:
    apiVersion: argoproj.io/v1alpha1
    kind: Rollout  # HPA musi celować w Rollout!
    name: orderflow
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50 # Skaluj, gdy średnie CPU > 50%
```

**Ważne:** Jeśli używasz HPA, **usuń** pole `replicas` z manifestu `Rollout/Deployment`. Inaczej HPA i GitOps będą ze sobą walczyć (HPA ustawi 5, GitOps przywróci 1).

---

## 10. Troubleshooting & Battle Scars

Lista problemów napotkanych podczas wdrożenia i ich rozwiązania.

### 🔴 Problem: `ErrImagePull` / `ImagePullBackOff`
*   **Objaw:** Pod nie startuje, w events widać "Authentication required".
*   **Przyczyna:** Obraz w GHCR jest prywatny, a klaster nie ma tokena.
*   **Rozwiązanie:**
    1. Utworzenie sekretu: `kubectl create secret docker-registry ghcr-secret ...`
    2. Dodanie `imagePullSecrets` do specyfikacji poda w Helm.

### 🔴 Problem: ArgoCD nie widzi zmian (Replicas 1 vs 5)
*   **Objaw:** W Gicie jest `replicaCount: 5`, ArgoCD robi Sync, ale na klastrze nadal `1`.
*   **Przyczyna:** Wartość parametru była **nadpisana (override)** w definicji Application w ArgoCD. Parametry aplikacji mają priorytet nad Gitem.
*   **Rozwiązanie:** Usunięcie nadpisania w UI ArgoCD (Parameters tab).

### 🔴 Problem: GitHub Actions nie widzi `ci.yaml`
*   **Objaw:** Push na branch nie uruchamia pipeline'u.
*   **Przyczyna:** Plik był w `automation/.github/workflows/`, a GitHub szuka w root `.github/workflows/`.
*   **Rozwiązanie:** Przeniesienie pliku do roota i dodanie `defaults.run.working-directory` w YAML.

### 🔴 Problem: Helm Template Error
*   **Objaw:** `Error converting YAML to JSON: did not find expected key`.
*   **Przyczyna:** Błąd wcięć (indentation) w pliku `deployment.yaml` przy pętli `range` dla zmiennych środowiskowych.

---

## 11. Słownik Pojęć

*   **CI (Continuous Integration):** Częste integrowanie kodu (merge), automatyczne testy i budowanie artefaktów.
*   **CD (Continuous Delivery):** Automatyczne dostarczanie kodu do środowisk (staging/prod), czasem z manualnym zatwierdzeniem.
*   **GitOps:** Model operacyjny, gdzie Git jest jedynym źródłem prawdy dla infrastruktury.
*   **Drift:** Różnica między stanem w Git a stanem faktycznym na klastrze.
*   **Canary Release:** Technika wdrażania polegająca na stopniowym udostępnianiu nowej wersji.
*   **Monorepo:** Jedno repozytorium zawierające kod wielu projektów/usług.
*   **SBOM (Software Bill of Materials):** Lista wszystkich komponentów i bibliotek w oprogramowaniu (ważne dla security).
