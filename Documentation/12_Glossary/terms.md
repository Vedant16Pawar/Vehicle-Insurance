# 12. Glossary of Terms

This glossary defines the core programming, machine learning, and operations terms used throughout this project.

---

## 🛠️ MLOps & System Terms

### Pipeline
A structured sequence of components that automates the machine learning workflow. In this project, the pipeline manages data ingestion, validation, preprocessing, training, evaluation, and deployment.

### Artifact
A file generated during the execution of a pipeline (e.g., split CSV datasets, validation reports, preprocessing pipelines, and serialized model files). Each pipeline run stores its artifacts in a timestamped directory.

### Model Registry
A central repository for storing and managing trained machine learning models, supporting versioning and deployment tracking. In this project, AWS S3 is used as the model registry.

### Containerization
The process of packaging an application and its dependencies into a single, isolated image (container) that can run consistently across different operating systems. This project uses Docker.

### CI/CD (Continuous Integration & Continuous Deployment)
An operations practice that automates testing, building, and deploying code changes. In this project, GitHub Actions handles CI/CD by building Docker images and deploying them to AWS EC2.

### ECR (Elastic Container Registry)
An AWS managed Docker container image registry that stores, manages, and deploys container images. The CI pipeline pushes Docker images to ECR, and the CD pipeline pulls them onto the EC2 instance.

### EC2 (Elastic Compute Cloud)
An AWS virtual server used to host the application. The project runs a self-hosted GitHub Actions runner on the EC2 instance for deployment.

### S3 (Simple Storage Service)
An AWS object storage service. The project uses an S3 bucket (`my-model-mlopsproject-bucket`) as the model registry, storing serialized model `.pkl` files.

### Self-Hosted Runner
A machine that runs GitHub Actions workflows locally instead of using GitHub-provided cloud runners. In this project, the target EC2 instance runs a self-hosted runner to execute the CD (deployment) job directly on the server.

---

## 🧠 Machine Learning Terms

### Estimator
A scikit-learn interface representing a machine learning model (e.g., `RandomForestClassifier`), exposing `.fit()` for training and `.predict()` for making predictions.

### Transformer
A scikit-learn interface representing a preprocessing component (e.g., `StandardScaler`), exposing `.fit()` to compute parameters and `.transform()` to apply scaling.

### ColumnTransformer
A scikit-learn utility that applies different preprocessing transformations to different subsets of columns in a dataset. In this project, it applies `StandardScaler` to `Age`/`Vintage`, `MinMaxScaler` to `Annual_Premium`, and passes other columns through unchanged.

### StandardScaler
A scaler that standardizes features by removing the mean and scaling to unit variance: $z = \frac{x - \mu}{\sigma}$. Applied to `Age` and `Vintage` columns.

### MinMaxScaler
A scaler that transforms features to a specified range (default `[0, 1]`): $x_{scaled} = \frac{x - x_{min}}{x_{max} - x_{min}}$. Applied to `Annual_Premium`.

### SMOTEENN
A hybrid resampling algorithm designed to handle class imbalance. It combines oversampling (SMOTE) to create synthetic minority samples and undersampling (ENN) to clean up noise near decision boundaries.

### Random Forest
An ensemble learning method that trains multiple decision trees on random subsets of the data and features, then combines their predictions via majority voting. This project uses `RandomForestClassifier` with 200 trees.

### F1-Score
The harmonic mean of Precision and Recall: $F_1 = 2 \cdot \frac{Precision \cdot Recall}{Precision + Recall}$. The primary metric used in model evaluation to balance false positives and false negatives.

### Precision
The ratio of true positive predictions to total positive predictions: $\frac{TP}{TP + FP}$. Measures how accurate the positive predictions are.

### Recall (Sensitivity)
The ratio of true positive predictions to all actual positives: $\frac{TP}{TP + FN}$. Measures how many actual positives the model captures.

### Confusion Matrix
A table summarizing classification results by counting True Positives (TP), True Negatives (TN), False Positives (FP), and False Negatives (FN).

### Inference
The process of passing new input data to a trained model to generate predictions. In this project, inference happens when a user submits the web form.

### Data Leakage
An error where information from the testing set is inadvertently used to train the model, leading to overly optimistic evaluation metrics. Using separate `fit` and `transform` steps on split datasets prevents this.

### One-Hot Encoding (Dummy Variables)
A technique to convert categorical variables into binary columns. `pd.get_dummies(drop_first=True)` is used on `Vehicle_Age` and `Vehicle_Damage` to prevent the dummy variable trap.

### Hyperparameter Tuning
The process of searching for optimal model configuration values (e.g., `n_estimators`, `max_depth`) that are not learned during training. The notebook uses `RandomizedSearchCV` for this.

### Overfitting
A condition where a model learns noise in the training data and performs well on training data but poorly on unseen test data. Random Forest's ensemble approach and depth limiting help reduce overfitting.

---

## 🐍 Python Programming Terms

### Serialization
The process of converting a Python object in memory into a byte stream for storage (e.g., `.pkl` files) or network transmission. In this project, `dill` and `pickle` handle serialization.

### Deserialization
The reverse of serialization — loading a stored byte stream (e.g., a `.pkl` file) back into a Python object in memory. `dill.load()` is used to load the model and preprocessor.

### Singleton Pattern
A design pattern that restricts the instantiation of a class to a single object. In this project, `S3Client` and `MongoDBClient` use this pattern to reuse database and storage connections across modules.

### Dataclass
A Python decorator (`@dataclass`) that automatically generates `__init__`, `__repr__`, and other methods for classes that primarily store data. Used extensively in `config_entity.py` and `artifact_entity.py`.

### Context Manager
A Python construct (using `with` statements) that manages resources like files or database connections, ensuring cleanup and release of resources on exit.

### Magic Methods (Dunder Methods)
Special methods in Python classes prefixed with double underscores (e.g., `__init__`, `__str__`, `__repr__`) that customize class behaviors like initialization, string conversion, and comparison.

### Lazy Loading
A design pattern where an object is not initialized until it is first needed. The prediction pipeline uses lazy loading to defer model download from S3 until the first prediction request.

---

## 🌐 Web & API Terms

### FastAPI
A modern, high-performance Python web framework for building APIs. Used in this project to serve the prediction web form and expose the `/train` endpoint.

### Jinja2
A Python HTML templating engine used by FastAPI to render dynamic HTML pages. The project uses Jinja2 to render `vehicledata.html` with prediction results.

### CORS (Cross-Origin Resource Sharing)
A security mechanism that controls which web domains can access the API. The project configures CORS middleware with `allow_origins=["*"]` to accept requests from any origin.

### Uvicorn
An ASGI (Asynchronous Server Gateway Interface) web server used to run the FastAPI application. The app starts Uvicorn on `0.0.0.0:5000`.
