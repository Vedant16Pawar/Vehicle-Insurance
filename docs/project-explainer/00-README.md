# Vehicle Insurance MLOps Technical Documentation Index

Welcome to the comprehensive, reverse-engineered technical documentation suite for the **Vehicle Insurance Cross-Sell Prediction** MLOps project.

---

## ⚡ If You Only Read One Thing (5-Line Summary)

1.  **Business Goal**: Predicts customer interest in Vehicle Insurance (`Response = 1` vs `0`) to optimize sales outreach targeting.
2.  **Data & Pipeline**: Pulls records dynamically from MongoDB Atlas, validates schema contracts via `schema.yaml`, and applies `StandardScaler`, `MinMaxScaler`, and **SMOTEENN** to handle an 88-12 class imbalance.
3.  **Model Safety**: Wraps preprocessor + Random Forest inside a custom `MyModel` container to prevent train-serve feature mismatch, pushing to AWS S3 only if candidate F1-score beats production by $\ge 0.02$.
4.  **Serving & DevOps**: Serves real-time web predictions using FastAPI (`app.py`) with Jinja2 HTML templates, containerized with Docker (`python:3.10-slim-buster`).
5.  **CI/CD**: Fully automated via GitHub Actions (`aws.yaml`) — building Docker images, pushing to AWS ECR, and deploying to an AWS EC2 runner.

---

## 📚 Complete Technical Guide Index (In Reading Order)

1.  **[01-overview.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/01-overview.md)** — High-level 30,000-ft system overview, business problem, input/output data contract, and high-level architecture diagram.
2.  **[02-repo-structure.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/02-repo-structure.md)** — Complete file tree and line-item functional map of every folder and file in the codebase.
3.  **[03-data-layer.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/03-data-layer.md)** — Deep-dive into Data Access (`proj1_data.py`), MongoDB Connections (`mongo_db_connection.py`), Ingestion (`data_ingestion.py`), Validation (`data_validation.py`), Transformation (`data_transformation.py`), and Schema contracts (`schema.yaml`).
4.  **[04-training-layer.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/04-training-layer.md)** — Model training (`model_trainer.py`), evaluation gatekeeping (`model_evaluation.py`), S3 pushing (`model_pusher.py`), wrapper objects (`estimator.py`), and notebook research (`experiment_notebook.ipynb`).
5.  **[05-pipeline-orchestration.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/05-pipeline-orchestration.md)** — Master pipeline orchestrator (`training_pipeline.py`), FastAPI HTTP retraining route (`app.py`), and CLI development triggers (`demo.py`).
6.  **[06-model-packaging-registry.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/06-model-packaging-registry.md)** — AWS S3 authentication (`aws_connection.py`), cloud storage abstraction (`aws_storage.py`), remote model proxy (`s3_estimator.py`), and dill serialization utilities (`main_utils.py`).
7.  **[07-deployment-layer.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/07-deployment-layer.md)** — FastAPI serving application (`app.py`), prediction input formatting (`prediction_pipeline.py`), and HTML/CSS web interfaces (`vehicledata.html`, `style.css`).
8.  **[08-infra-devops.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/08-infra-devops.md)** — Docker containerization (`Dockerfile`, `.dockerignore`), GitHub Actions CI/CD workflows (`aws.yaml`), and PEP 517 packaging (`setup.py`, `pyproject.toml`, `requirements.txt`).
9.  **[09-monitoring-retraining.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/09-monitoring-retraining.md)** — Structured logging (`logger/__init__.py`), traceback exception handling (`exception/__init__.py`), and automated retraining feedback loops.
10. **[10-full-architecture-story.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/10-full-architecture-story.md)** — The complete start-to-finish execution story tracing data ingestion, training, evaluation, cloud registration, deployment, and real-time prediction inference in one continuous narrative.
11. **[11-interview-prep.md](file:///c:/Projects/Vehicle-Insurance/docs/project-explainer/11-interview-prep.md)** — 60-second elevator pitch, 12 deep-dive interview questions with grounded technical answers, and honest system limitation trade-offs.
