# 10. The Full Architecture Narrative: End-to-End Execution Story

This document provides a single continuous narrative describing the complete lifecycle of the application — tracing both the **Training Pipeline Execution Flow** and the **Web Request Prediction Flow**, explicitly linking every file, class, and method across the codebase.

---

## 1. System Initialization & Infrastructure Deployment

Before any web request or training pipeline can run, the application infrastructure is built and deployed:

1.  **Code Commit & CI/CD Trigger**: A developer pushes code changes to the `main` branch of the GitHub repository.
2.  **GitHub Actions Trigger (`.github/workflows/aws.yaml`)**: GitHub Actions catches the push event and launches the `continuous-integration` job on `ubuntu-latest`.
3.  **Docker Build (`Dockerfile`, `.dockerignore`)**: GitHub Actions authenticates with AWS using `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets, logs into AWS Elastic Container Registry (ECR), and runs `docker build`. Docker reads `.dockerignore` to filter out local logs, virtual environments, and notebooks, compiling a lean image based on `python:3.10-slim-buster`. During build, `RUN pip install -r requirements.txt` executes, installing dependencies and running `setup.py` (`-e .`) to install `src` as an editable package.
4.  **Registry Push & Deployment**: The Docker image is tagged and pushed to AWS ECR. Next, the `continuous-deployment` job fires on a self-hosted runner active on an AWS EC2 instance. The EC2 runner logs into AWS ECR, pulls the new container image, and runs `docker run -d -p 5000:5000` injecting environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `MONGODB_URL`).
5.  **FastAPI Startup (`app.py`, `src/logger/__init__.py`)**: Inside the running container, `python3 app.py` starts. Importing `src.logger` triggers `configure_logger()`, establishing a timestamped log file in `logs/`. `app.py` initializes FastAPI, mounts `static/css/style.css`, loads Jinja2 templates from `templates/vehicledata.html`, adds CORS middleware, and starts Uvicorn listening on `0.0.0.0:5000`.

---

## 2. The Training Pipeline Lifecycle (Data -> Model Registry)

When an engineer triggers model training via `GET /train` (or CLI `demo.py`):

1.  **Orchestrator Trigger (`src/pipline/training_pipeline.py`)**: `app.py` instantiates `TrainPipeline()` and calls `run_pipeline()`. `TrainPipeline` initializes `TrainingPipelineConfig`, creating a timestamped artifact directory (`artifact/MM_DD_YYYY_HH_MM_SS/`).
2.  **Data Ingestion (`src/components/data_ingestion.py`, `src/data_access/proj1_data.py`, `src/configuration/mongo_db_connection.py`)**:
    *   `TrainPipeline` calls `start_data_ingestion()`.
    *   `DataIngestion` calls `Proj1Data.export_collection_as_dataframe()`.
    *   `Proj1Data` obtains a singleton PyMongo connection handle via `MongoDBClient` (reading `MONGODB_URL` with TLS certificates from `certifi`).
    *   `Proj1Data` queries the `Proj1-Data` collection in MongoDB Atlas, converts documents into a Pandas DataFrame, drops the `_id` field, and replaces string `"na"` with `np.nan`.
    *   `DataIngestion` saves a raw snapshot to `feature_store/data.csv`, performs a 75/25 train-test split via `train_test_split()`, writes `train.csv` and `test.csv`, and returns a `DataIngestionArtifact`.
3.  **Data Validation (`src/components/data_validation.py`, `config/schema.yaml`)**:
    *   `TrainPipeline` calls `start_data_validation(DataIngestionArtifact)`.
    *   `DataValidation` loads `config/schema.yaml` via `read_yaml_file()`.
    *   It checks whether `train.csv` and `test.csv` contain all required columns and correct schema definitions.
    *   It writes a validation report (`report.yaml`) and returns `DataValidationArtifact(validation_status=True)`.
4.  **Data Transformation (`src/components/data_transformation.py`, `src/utils/main_utils.py`)**:
    *   `TrainPipeline` calls `start_data_transformation()`.
    *   `DataTransformation` maps `Gender` (`Male` -> 1, `Female` -> 0) and generates dummy variables for `Vehicle_Age` and `Vehicle_Damage`.
    *   Constructs a scikit-learn `ColumnTransformer` applying `StandardScaler` to `Age` & `Vintage`, and `MinMaxScaler` to `Annual_Premium`.
    *   Fits the transformer on training features and transforms both train and test DataFrames.
    *   Applies **SMOTEENN** (`imblearn.combine.SMOTEENN`) on the training set to oversample minority `Response = 1` cases and clean boundary noise.
    *   Saves `preprocessing.pkl` via `save_object()`, saves `train.npy` and `test.npy` via `save_numpy_array_data()`, and returns `DataTransformationArtifact`.
5.  **Model Training (`src/components/model_trainer.py`, `src/entity/estimator.py`)**:
    *   `TrainPipeline` calls `start_model_trainer()`.
    *   `ModelTrainer` loads `train.npy` and `test.npy`.
    *   Fits `RandomForestClassifier` (`n_estimators=200`, `min_samples_split=7`, `min_samples_leaf=6`, `random_state=101`).
    *   Evaluates accuracy metric ($> 0.60$ threshold). Calculates test set F1-score, Precision, and Recall.
    *   Wraps preprocessor (`preprocessing.pkl`) and fitted classifier inside a custom `MyModel` container object.
    *   Saves `MyModel` to `trained_model/model.pkl` and returns `ModelTrainerArtifact`.
6.  **Model Evaluation (`src/components/model_evaluation.py`, `src/entity/s3_estimator.py`, `src/cloud_storage/aws_storage.py`)**:
    *   `TrainPipeline` calls `start_model_evaluation()`.
    *   `ModelEvaluation` computes `trained_model_f1_score` on test data.
    *   Instantiates `Proj1Estimator` to check if a production model exists in AWS S3 bucket `my-model-mlopsproject-bucket`.
    *   If present, downloads and evaluates the active S3 model to compute `s3_model_f1_score`.
    *   Compares F1 scores: if `trained_model_f1_score - s3_model_f1_score > 0.02`, sets `is_model_accepted = True` and returns `ModelEvaluationArtifact`.
7.  **Model Pusher (`src/components/model_pusher.py`)**:
    *   If `is_model_accepted` is `True`, `ModelPusher` uses `SimpleStorageService.upload_file()` to upload `model.pkl` to AWS S3 bucket `my-model-mlopsproject-bucket`.
    *   Saves a local copy to `model/model.pkl` and returns `ModelPusherArtifact`.

---

## 3. The Real-Time Web Prediction Lifecycle

When an end-user visits the web application and submits customer details:

```mermaid
flowchart LR
    User(["User Browser"]) -->|"POST /"| App["app.py"]
    App --> VD["VehicleData"]
    VD --> VDC["VehicleDataClassifier"]
    VDC --> Est["Proj1Estimator"]
    Est -->|"Lazy load from S3/cache"| Model["MyModel"]
    Model -->|"transform → predict"| Result["[1] or [0]"]
    Result --> App
    App -->|"Response-Yes / No"| User

    style User fill:#ff9800,stroke:#e65100,color:#fff
    style Model fill:#2ecc71,stroke:#27ae60,color:#fff
```

1.  **User Form Submission (`templates/vehicledata.html`)**: The user fills out fields for Age, Gender, Annual Premium, Vintage, Vehicle Age, Damage, and Insurance history, clicking **Submit**.
2.  **FastAPI Route Handling (`app.py`)**: A `POST /` request hits FastAPI. `app.py` invokes `DataForm(request)` to extract form field strings asynchronously.
3.  **Input Data Formatting (`src/pipline/prediction_pipeline.py`)**:
    *   `app.py` instantiates `VehicleData` passing form inputs.
    *   Calls `vehicle_data.get_vehicle_input_data_frame()`, converting inputs into a single-row Pandas DataFrame matching the 11 feature columns expected by the trained pipeline.
4.  **Prediction Invocation (`src/pipline/prediction_pipeline.py`, `src/entity/s3_estimator.py`)**:
    *   `app.py` calls `VehicleDataClassifier.predict(dataframe)`.
    *   `VehicleDataClassifier` delegates to `Proj1Estimator.predict(dataframe)`.
5.  **Model Loading & Execution (`src/entity/s3_estimator.py`, `src/entity/estimator.py`)**:
    *   `Proj1Estimator` checks if `MyModel` is loaded in memory. If not, it checks local cache `model/model.pkl` or downloads it from AWS S3 (`SimpleStorageService.load_model()`).
    *   `Proj1Estimator` calls `loaded_model.predict(dataframe)`.
    *   Inside `MyModel.predict()`, the DataFrame is transformed via `preprocessing_object.transform(dataframe)` (scaling `Age`, `Vintage`, `Annual_Premium`) and passed to `trained_model_object.predict()`.
    *   Returns array `[1]` or `[0]`.
6.  **Response Rendering (`app.py`, `templates/vehicledata.html`)**:
    *   `app.py` receives prediction `[1]` or `[0]`.
    *   Maps `1` -> `"Response-Yes"` (interested in insurance) or `0` -> `"Response-No"`.
    *   Renders `vehicledata.html` with Jinja2 template context displaying the prediction banner to the user.
