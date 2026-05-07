## 1. Workflow file

- [x] 1.1 Create `.github/workflows/ci.yml` with trigger on push to `main` and non-fork PRs to `main`
- [x] 1.2 Add checkout step using `actions/checkout@v4.2.2`
- [x] 1.3 Add `actions/setup-node` step pinned to Node.js 24
- [x] 1.4 Add step to install openspec CLI: `npm install -g openspec` (latest)
- [x] 1.5 Add `actions/setup-python` step pinned to Python 3.11
- [x] 1.6 Add step to install Python deps: `pip install -r requirements-dev.txt`
- [x] 1.7 Add pre-commit step using `pre-commit/action@v3.0.1`

## 2. Documentation

- [x] 2.1 Add CI section to `DEVELOPMENT.md` covering triggers, openspec install rationale, Python deps install rationale, and fork-filtering behavior
- [x] 2.2 Add note to `DEVELOPMENT.md` that any new `language: system` hook requires a corresponding CI setup step
- [x] 2.3 Add GitHub Actions CI status badge to `README.md` below the existing badges
