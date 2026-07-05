# 04. Execution Flow

This chapter traces the runtime lifecycle of the application, describing which files execute first, what objects are created, how parameters are loaded, and how components interact.

---

## 🚀 1. FastAPI Server Startup Flow

When the application is run via `python app.py` (or through the Docker container command):

```mermaid
sequenceDiagram
    participant OS as Operating System
    participant App as app.py
    participant Log as src/logger/__init__.py
    participant Const as src/constants/__init__.py
    participant Predictor as src/pipline/prediction_pipeline.py
    participant Est as src/entity/s3_estimator.py

    OS->>App: python app.py
    App->>Const: Load Constants (Host, Port, DB settings)
    Const-->>App: Constants loaded
    App->>Log: Import src.logger (Auto-executes)
    Log->>Log: configure_logger()
    Log->>Log: Create logs/<timestamp>.log file
    Log-->>App: Logger initialized
    App->>App: Instantiate app = FastAPI()
    App->>App: Mount static folder ("/static")
    App->>App: Configure Jinja2 templates directory
    App->>App: Add CORS middleware (allow all origins "*")
    App->>Predictor: Instantiate model_predictor = VehicleDataClassifier()
    Predictor->>Est: Instantiate Proj1Estimator(bucket_name, model_path)
    Est-->>Predictor: Estimator configured
    Predictor-->>App: Predictor ready (model is NOT loaded yet - lazy loaded)
    App->>OS: app_run(app, host="0.0.0.0", port=5000)
```

1.  **Entry Point**: The OS runs `app.py`. The python interpreter processes imports.
2.  **Constants Loading**: Imports from `src.constants` are resolved. This sets global values like target column (`Response`), paths (`config/schema.yaml`), and host parameters (`0.0.0.0:5000`).
3.  **Logger Startup**: Importing `src.logger` triggers its module-level `configure_logger()` execution immediately. It creates a `logs/` folder and starts a `RotatingFileHandler`.
4.  **FastAPI Setup**: FastAPI is initialized, mounts the static CSS directory, configures Jinja2 templates, and sets CORS middleware.
5.  **Predictor Setup**: Instantiates `VehicleDataClassifier()`, which initializes a `Proj1Estimator` with default values (S3 bucket: `my-model-mlopsproject-bucket` and file key: `model.pkl`). The model itself is not loaded yet (lazy loading).
6.  **Server Listen**: The program invokes `uvicorn.run()` to start listening for incoming requests on port 5000.

---

## 🔄 2. Model Training Flow (Triggering `/train`)

When an HTTP GET request targets the `/train` endpoint:

```mermaid
sequenceDiagram
    actor Admin
    participant App as app.py
    participant TrainPipe as src/pipline/training_pipeline.py
    participant Ingestion as src/components/data_ingestion.py
    participant Validation as src/components/data_validation.py
    participant Transformation as src/components/data_transformation.py
    participant Trainer as src/components/model_trainer.py
    participant Evaluation as src/components/model_evaluation.py
    participant Pusher as src/components/model_pusher.py

    Admin->>App: GET /train
    App->>TrainPipe: Instantiate TrainPipeline()
    TrainPipe->>TrainPipe: Generate config entities using timestamp
    App->>TrainPipe: run_pipeline()
    
    %% Ingestion
    TrainPipe->>Ingestion: start_data_ingestion()
    Ingestion->>Ingestion: Connect to MongoDB Atlas
    Ingestion->>Ingestion: Export records to feature_store/data.csv
    Ingestion->>Ingestion: Split train/test (75/25)
    Ingestion-->>TrainPipe: Return DataIngestionArtifact
    
    %% Validation
    TrainPipe->>Validation: start_data_validation(IngestionArtifact)
    Validation->>Validation: Check schema & columns against schema.yaml
    Validation->>Validation: Write validation report JSON
    Validation-->>TrainPipe: Return DataValidationArtifact
    
    %% Transformation
    TrainPipe->>Transformation: start_data_transformation(IngestionArtifact, ValidationArtifact)
    Transformation->>Transformation: Map Gender column to binary
    Transformation->>Transformation: Create dummy variables for categories
    Transformation->>Transformation: Apply ColumnTransformers (Standard/MinMax)
    Transformation->>Transformation: Apply SMOTEENN resample on train/test data
    Transformation->>Transformation: Save preprocessing.pkl & npy arrays
    Transformation-->>TrainPipe: Return DataTransformationArtifact
    
    %% Trainer
    TrainPipe->>Trainer: start_model_trainer(TransformationArtifact)
    Trainer->>Trainer: Fit RandomForestClassifier
    Trainer->>Trainer: Check accuracy >= threshold (60%)
    Trainer->>Trainer: Bundle preprocessor + classifier into MyModel
    Trainer->>Trainer: Save model.pkl locally
    Trainer-->>TrainPipe: Return ModelTrainerArtifact
    
    %% Evaluation
    TrainPipe->>Evaluation: start_model_evaluation(IngestionArtifact, TrainerArtifact)
    Evaluation->>Evaluation: Download production model from S3 (if present)
    Evaluation->>Evaluation: Calculate test set F1-scores
    Evaluation->>Evaluation: Compare models (F1 difference >= 0.02)
    Evaluation-->>TrainPipe: Return ModelEvaluationArtifact (is_model_accepted)
    
    alt is_model_accepted == True
        TrainPipe->>Pusher: start_model_pusher(EvaluationArtifact)
        Pusher->>Pusher: Upload new model.pkl to S3 bucket registry
        Pusher->>Pusher: Cache model locally as model/model.pkl
        Pusher-->>TrainPipe: Return ModelPusherArtifact
        TrainPipe-->>App: Success Response
        App-->>Admin: "Training successful!!!"
    else is_model_accepted == False
        TrainPipe-->>App: Halt Pipeline
        App-->>Admin: "Training successful!!!" (No push)
    end
```

---

## 🔮 3. Prediction Inference Flow (POST `/`)

When a user submits vehicle details on the webpage form:

```mermaid
sequenceDiagram
    actor User
    participant App as app.py
    participant Predictor as src/pipline/prediction_pipeline.py
    participant Est as src/entity/s3_estimator.py
    participant Model as src/entity/estimator.py (MyModel)

    User->>App: Submit form (POST /)
    App->>App: Instantiate DataForm(request)
    App->>App: Extract values asynchronously
    App->>Predictor: Instantiate VehicleData(form values)
    App->>Predictor: Call get_vehicle_input_data_frame()
    Predictor-->>App: Return 1-row Pandas DataFrame
    App->>Predictor: Call predict(dataframe)
    Predictor->>Est: Call predict(dataframe)
    
    alt Model not loaded in memory
        Est->>Est: Call load_model()
        alt Local cache path model/model.pkl exists
            Est->>Est: Load model using dill.load()
        else Local path does not exist
            Est->>Est: Fetch model from S3 using SimpleStorageService
            Est->>Est: Save copy locally to model/model.pkl
        end
    end
    
    Est->>Model: Call predict(dataframe)
    Model->>Model: Apply preprocessor.transform(dataframe)
    Model->>Model: Call trained_model.predict(transformed_features)
    Model-->>Est: Return class array [1] or [0]
    Est-->>Predictor: Return prediction array
    Predictor-->>App: Return prediction value
    App->>App: Map prediction value (1 -> "Response-Yes", 0 -> "Response-No")
    App->>User: Render vehicledata.html with status result
```
