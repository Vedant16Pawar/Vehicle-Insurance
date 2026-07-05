# Source Code: Model Training, Evaluation & Pusher

This section covers the components responsible for training the Random Forest model, evaluating its performance against production baselines, and deploying it to the cloud storage registry.

---

# File 1: [src/entity/estimator.py](file:///c:/Projects/Vehicle-Insurance/src/entity/estimator.py)

*   **Purpose**: Defines target mappings and bundles preprocessing pipelines with model estimators.
*   **Why it exists**: During deployment, predictions require both data scaling (preprocessing) and model execution. Combining them prevents version mismatch.
*   **Who imports/calls it**: Imported by `ModelTrainer` during training and `s3_estimator.py` during inference.
*   **Dependencies**: `sys`, `pandas`, `sklearn.pipeline.Pipeline`, `src.exception.MyException`, `src.logger`.

## Line-by-Line Walkthrough

### Code Block 1: Target Mapping & Model Bundle (Lines 1-55)
```python
1: import sys
2: 
3: import pandas as pd
4: from pandas import DataFrame
5: from sklearn.pipeline import Pipeline
6: 
7: from src.exception import MyException
8: from src.logger import logging
9: 
10: class TargetValueMapping:
11:     def __init__(self):
12:         self.yes:int = 0
13:         self.no:int = 1
14:     def _asdict(self):
15:         return self.__dict__
16:     def reverse_mapping(self):
17:         mapping_response = self._asdict()
18:         return dict(zip(mapping_response.values(),mapping_response.keys()))
19: 
20: class MyModel:
21:     def __init__(self, preprocessing_object: Pipeline, trained_model_object: object):
22:         """
23:         :param preprocessing_object: Input Object of preprocesser
24:         :param trained_model_object: Input Object of trained model 
25:         """
26:         self.preprocessing_object = preprocessing_object
27:         self.trained_model_object = trained_model_object
28: 
29:     def predict(self, dataframe: pd.DataFrame) -> DataFrame:
30:         """
31:         Function accepts preprocessed inputs (with all custom transformations already applied),
32:         applies scaling using preprocessing_object, and performs prediction on transformed features.
33:         """
34:         try:
35:             logging.info("Starting prediction process.")
36: 
37:             # Step 1: Apply scaling transformations using the pre-trained preprocessing object
38:             transformed_feature = self.preprocessing_object.transform(dataframe)
39: 
40:             # Step 2: Perform prediction using the trained model
41:             logging.info("Using the trained model to get predictions")
42:             predictions = self.trained_model_object.predict(transformed_feature)
43: 
44:             return predictions
45: 
46:         except Exception as e:
47:             logging.error("Error occurred in predict method", exc_info=True)
48:             raise MyException(e, sys) from e
49: 
50:     def __repr__(self):
51:         return f"{type(self.trained_model_object).__name__}()"
52: 
53:     def __str__(self):
54:         return f"{type(self.trained_model_object).__name__}()"
```

*   **Line-by-Line Explanation**:
    *   `Line 10`: Declares `TargetValueMapping` to map string predictions back to categories.
    *   `Line 14-15`: Exposes properties as a dictionary.
    *   `Line 16-18`: Uses `zip` to reverse map responses (e.g., matching code `0` to `"yes"` and `1` to `"no"`).
    *   `Line 20`: Declares wrapper class `MyModel`.
    *   `Line 21`: Constructor accepts the preprocessing pipeline and the trained model object.
    *   `Line 29`: Declares the prediction method.
    *   `Line 38`: Passes the input DataFrame to `self.preprocessing_object.transform()`. This standardizes the incoming features without fitting new parameters.
    *   `Line 42`: Passes the scaled array to `self.trained_model_object.predict()` to generate classifications.
    *   `Line 44`: Returns predictions.
    *   `Line 50-54`: Overrides string representation methods to return the name of the wrapped estimator class (e.g., `RandomForestClassifier()`).

---

# File 2: [src/entity/s3\_estimator.py](file:///c:/Projects/Vehicle-Insurance/src/entity/s3_estimator.py)

*   **Purpose**: Manages downloading, local caching, and inference using the model stored in S3.
*   **Why it exists**: Prevents network latency during inference by caching models locally.
*   **Who imports/calls it**: Used by `VehicleDataClassifier` in prediction pipelines.
*   **Dependencies**: `os`, `glob`, `src.cloud_storage.aws_storage.SimpleStorageService`, `src.utils.main_utils`.

## Line-by-Line Walkthrough

### Code Block 1: S3 Estimator Loader (Lines 11-74)
```python
11: class Proj1Estimator:
12:     """
13:     This class is used to save and retrieve our model from s3 bucket and to do prediction
14:     """
15:     def __init__(self,bucket_name,model_path,):
21:         self.bucket_name = bucket_name
22:         self.s3 = SimpleStorageService()
23:         self.model_path = model_path
24:         self.loaded_model:MyModel=None
25: 
26:     def is_model_present(self,model_path):
27:         try:
28:             return self.s3.s3_key_path_available(bucket_name=self.bucket_name, s3_key=model_path)
29:         except MyException as e:
30:             print(e)
31:             return False
32: 
33:     def load_model(self)->MyModel:
39:         local_model_path = os.path.join("model", "model.pkl")
40: 
41:         # 1. Try to load from standard local path 'model/model.pkl'
42:         if os.path.exists(local_model_path):
43:             try:
44:                 print(f"Loading model from local path: {local_model_path}")
45:                 return load_object(local_model_path)
46:             except Exception as e:
47:                 print(f"Failed to load model from local path {local_model_path}: {e}. Falling back...")
48: 
49:         # 2. Try to find the latest trained model in the artifact directory
50:         if os.path.exists("artifact"):
51:             model_paths = glob.glob(os.path.join("artifact", "*", "model_trainer", "trained_model", "model.pkl"))
52:             if model_paths:
53:                 # Sort by modification time to get the latest trained model
54:                 model_paths.sort(key=os.path.getmtime, reverse=True)
55:                 latest_model_path = model_paths[0]
56:                 try:
57:                     print(f"Loading model from latest artifact path: {latest_model_path}")
58:                     return load_object(latest_model_path)
59:                 except Exception as e:
60:                     print(f"Failed to load model from artifact path {latest_model_path}: {e}. Falling back...")
61: 
62:         # 3. Fallback: Download the model from S3 and cache it locally
63:         print("Model not found locally. Fetching model from S3...")
64:         model = self.s3.load_model(self.model_path, bucket_name=self.bucket_name)
65: 
66:         # Cache downloaded model locally for fast subsequent loads
67:         try:
68:             os.makedirs(os.path.dirname(local_model_path), exist_ok=True)
69:             save_object(local_model_path, model)
70:             print(f"Successfully cached downloaded model locally at {local_model_path}")
71:         except Exception as e:
72:             print(f"Failed to cache model locally: {e}")
73: 
74:         return model
```

*   **Line-by-Line Explanation**:
    *   `Line 15`: Constructor sets S3 credentials and sets `self.loaded_model` to `None`.
    *   `Line 26`: Checks if the model exists in the S3 bucket by querying the path key.
    *   `Line 33`: Declares `load_model()`.
    *   `Line 42-45`: First checks if `model/model.pkl` exists in the local directory. If found, loads it using `load_object()` to avoid network calls.
    *   `Line 50-55`: If not found in the standard directory, searches for the latest model file in the `artifact/` directory. Uses `glob.glob` to find all matches, sorts them by modification time (`os.path.getmtime`), and loads the newest file.
    *   `Line 63-64`: If no local copy exists, downloads the model from the S3 bucket.
    *   `Line 68-69`: Caches a copy of the downloaded model at `model/model.pkl` for subsequent inference calls.

---

### Code Block 2: Save and Prediction Methods (Lines 76-103)
```python
76:     def save_model(self,from_file,remove:bool=False)->None:
83:         try:
84:             self.s3.upload_file(from_file,
85:                                 to_filename=self.model_path,
86:                                 bucket_name=self.bucket_name,
87:                                 remove=remove
88:                                 )
89:         except Exception as e:
90:             raise MyException(e, sys)
91: 
92: 
93:     def predict(self,dataframe:DataFrame):
98:         try:
99:             if self.loaded_model is None:
100:                 self.loaded_model = self.load_model()
101:             return self.loaded_model.predict(dataframe=dataframe)
102:         except Exception as e:
103:             raise MyException(e, sys)
```

*   **Line-by-Line Explanation**:
    *   `Line 76`: Declares `save_model()`.
    *   `Line 84-88`: Uploads the local model file to the S3 bucket path key.
    *   `Line 93`: Declares `predict()`.
    *   `Line 99-100`: If `self.loaded_model` is not yet cached in instance memory, calls `load_model()` to load it.
    *   `Line 101`: Calls the wrapped `MyModel.predict` method and returns predictions.

---

# File 3: [src/components/model\_trainer.py](file:///c:/Projects/Vehicle-Insurance/src/components/model_trainer.py)

*   **Purpose**: Trains a Random Forest model on the transformed training set and saves the model artifact.
*   **Who imports/calls it**: Called by `TrainPipeline`.
*   **Dependencies**: `sklearn.ensemble.RandomForestClassifier`, `sklearn.metrics`, `src.entity.estimator.MyModel`, `src.utils.main_utils`.

## Line-by-Line Walkthrough

### Code Block 1: Model Training and Evaluation Metrics (Lines 15-68)
```python
15: class ModelTrainer:
16:     def __init__(self, data_transformation_artifact: DataTransformationArtifact,
17:                  model_trainer_config: ModelTrainerConfig):
22:         self.data_transformation_artifact = data_transformation_artifact
23:         self.model_trainer_config = model_trainer_config
24: 
25:     def get_model_object_and_report(self, train: np.array, test: np.array) -> Tuple[object, object]:
33:         try:
34:             logging.info("Training RandomForestClassifier with specified parameters")
35: 
36:             # Splitting the train and test data into features and target variables
37:             x_train, y_train, x_test, y_test = train[:, :-1], train[:, -1], test[:, :-1], test[:, -1]
38:             logging.info("train-test split done.")
39: 
40:             # Initialize RandomForestClassifier with specified parameters
41:             model = RandomForestClassifier(
42:                 n_estimators = self.model_trainer_config._n_estimators,
43:                 min_samples_split = self.model_trainer_config._min_samples_split,
44:                 min_samples_leaf = self.model_trainer_config._min_samples_leaf,
45:                 max_depth = self.model_trainer_config._max_depth,
46:                 criterion = self.model_trainer_config._criterion,
47:                 random_state = self.model_trainer_config._random_state
48:             )
49: 
50:             # Fit the model
51:             logging.info("Model training going on...")
52:             model.fit(x_train, y_train)
53:             logging.info("Model training done.")
54: 
55:             # Predictions and evaluation metrics
56:             y_pred = model.predict(x_test)
57:             accuracy = accuracy_score(y_test, y_pred)
58:             f1 = f1_score(y_test, y_pred)
59:             precision = precision_score(y_test, y_pred)
60:             recall = recall_score(y_test, y_pred)
61: 
62:             # Creating metric artifact
63:             metric_artifact = ClassificationMetricArtifact(f1_score=f1, precision_score=precision, recall_score=recall)
64:             return model, metric_artifact
65:         
66:         except Exception as e:
67:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 25`: Declares `get_model_object_and_report()`.
    *   `Line 37`: Splits the train/test arrays. `[:, :-1]` extracts all columns except the last one (features), and `[:, -1]` extracts the last column (targets).
    *   `Line 41-48`: Instantiates `RandomForestClassifier` with hyperparameter values loaded from configuration entities.
    *   `Line 52`: Calls `.fit(x_train, y_train)` to train the Random Forest.
    *   `Line 56-60`: Makes predictions on the test set and calculates evaluation metrics (Accuracy, F1-Score, Precision, and Recall).
    *   `Line 63`: Instantiates a `ClassificationMetricArtifact` containing the calculated F1-score, Precision, and Recall.

---

### Code Block 2: Trainer Orchestration and Threshold Checks (Lines 69-114)
```python
69:     def initiate_model_trainer(self) -> ModelTrainerArtifact:
70:         logging.info("Entered initiate_model_trainer method of ModelTrainer class")
78:         try:
79:             print("------------------------------------------------------------------------------------------------")
80:             print("Starting Model Trainer Component")
81:             # Load transformed train and test data
82:             train_arr = load_numpy_array_data(file_path=self.data_transformation_artifact.transformed_train_file_path)
83:             test_arr = load_numpy_array_data(file_path=self.data_transformation_artifact.transformed_test_file_path)
84:             logging.info("train-test data loaded")
85:             
86:             # Train model and get metrics
87:             trained_model, metric_artifact = self.get_model_object_and_report(train=train_arr, test=test_arr)
88:             logging.info("Model object and artifact loaded.")
89:             
90:             # Load preprocessing object
91:             preprocessing_obj = load_object(file_path=self.data_transformation_artifact.transformed_object_file_path)
92:             logging.info("Preprocessing obj loaded.")
93: 
94:             # Check if the model's accuracy meets the expected threshold
95:             if accuracy_score(train_arr[:, -1], trained_model.predict(train_arr[:, :-1])) < self.model_trainer_config.expected_accuracy:
96:                 logging.info("No model found with score above the base score")
97:                 raise Exception("No model found with score above the base score")
98: 
99:             # Save the final model object that includes both preprocessing and the trained model
100:             logging.info("Saving new model as performace is better than previous one.")
101:             my_model = MyModel(preprocessing_object=preprocessing_obj, trained_model_object=trained_model)
102:             save_object(self.model_trainer_config.trained_model_file_path, my_model)
103:             logging.info("Saved final model object that includes both preprocessing and the trained model")
104: 
105:             # Create and return the ModelTrainerArtifact
106:             model_trainer_artifact = ModelTrainerArtifact(
107:                 trained_model_file_path=self.model_trainer_config.trained_model_file_path,
108:                 metric_artifact=metric_artifact,
109:             )
110:             logging.info(f"Model trainer artifact: {model_trainer_artifact}")
111:             return model_trainer_artifact
112:         
113:         except Exception as e:
114:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 82-83`: Loads the transformed NumPy arrays from the transformation step.
    *   `Line 87`: Trains the Random Forest model and retrieves the evaluation metrics.
    *   `Line 91`: Loads the serialized preprocessing object (`preprocessing.pkl`).
    *   `Line 95-97`: Compares the model's accuracy on the **training set** against the expected accuracy threshold (60%). If it falls below the threshold, raises an exception and halts the pipeline.
    *   `Line 101-102`: Bundles the preprocessing pipeline and the trained Random Forest classifier into a `MyModel` instance, serializing it to the trainer's target artifact directory.
    *   `Line 106-109`: Instantiates and returns the `ModelTrainerArtifact`.
*   **Production Improvements/Issues**:
    *   *Training Accuracy Check Bug*: Evaluating accuracy on the *training set* (`train_arr`) rather than the *test set* (`test_arr`) can lead to overfitting, as a model can overfit the training data to pass the threshold check while performing poorly on unseen test data.

---

# File 4: [src/components/model\_evaluation.py](file:///c:/Projects/Vehicle-Insurance/src/components/model_evaluation.py)

*   **Purpose**: Compares the newly trained model's performance against the active production model in S3.
*   **Who imports/calls it**: Called by `TrainPipeline`.
*   **Dependencies**: `sklearn.metrics.f1_score`, `src.entity.s3_estimator.Proj1Estimator`, `src.utils.main_utils`.

## Line-by-Line Walkthrough

### Code Block 1: Active Model Retrieval (Lines 22-83)
```python
22: class ModelEvaluation:
23: 
24:     def __init__(self, model_eval_config: ModelEvaluationConfig, data_ingestion_artifact: DataIngestionArtifact,
25:                  model_trainer_artifact: ModelTrainerArtifact):
26:         try:
27:             self.model_eval_config = model_eval_config
28:             self.data_ingestion_artifact = data_ingestion_artifact
29:             self.model_trainer_artifact = model_trainer_artifact
30:         except Exception as e:
31:             raise MyException(e, sys) from e
32: 
33:     def get_best_model(self) -> Optional[Proj1Estimator]:
41:         try:
42:             bucket_name = self.model_eval_config.bucket_name
43:             model_path=self.model_eval_config.s3_model_key_path
44:             proj1_estimator = Proj1Estimator(bucket_name=bucket_name,
45:                                                model_path=model_path)
46: 
47:             if proj1_estimator.is_model_present(model_path=model_path):
48:                 return proj1_estimator
49:             return None
50:         except Exception as e:
51:             raise  MyException(e,sys)
```

*   **Line-by-Line Explanation**:
    *   `Line 24`: Constructor saves evaluation configurations, ingestion file paths, and model trainer metrics.
    *   `Line 33`: Declares `get_best_model()`.
    *   `Line 44-45`: Instantiates `Proj1Estimator` with the target S3 bucket name and model file path key.
    *   `Line 47-48`: If the model file is present in the S3 bucket, returns the estimator; otherwise, returns `None`.

---

### Code Block 2: Custom Mapping & F1 Score Comparisons (Lines 84-152)
```python
84:     def evaluate_model(self) -> EvaluateModelResponse:
93:         try:
94:             test_df = pd.read_csv(self.data_ingestion_artifact.test_file_path)
95:             x, y = test_df.drop(TARGET_COLUMN, axis=1), test_df[TARGET_COLUMN]
97:             logging.info("Test data loaded and now transforming it for prediction...")
99:             x = self._map_gender_column(x)
100:             x = self._drop_id_column(x)
101:             x = self._create_dummy_columns(x)
102:             x = self._rename_columns(x)
104:             trained_model = load_object(file_path=self.model_trainer_artifact.trained_model_file_path)
106:             trained_model_f1_score = self.model_trainer_artifact.metric_artifact.f1_score
109:             best_model_f1_score=None
110:             best_model = self.get_best_model()
111:             if best_model is not None:
112:                 logging.info(f"Computing F1_Score for production model..")
113:                 y_hat_best_model = best_model.predict(x)
114:                 best_model_f1_score = f1_score(y, y_hat_best_model)
117:             tmp_best_model_score = 0 if best_model_f1_score is None else best_model_f1_score
118:             result = EvaluateModelResponse(trained_model_f1_score=trained_model_f1_score,
119:                                            best_model_f1_score=best_model_f1_score,
120:                                            is_model_accepted=trained_model_f1_score > tmp_best_model_score,
121:                                            difference=trained_model_f1_score - tmp_best_model_score
122:                                            )
124:             return result
127:         except Exception as e:
128:             raise MyException(e, sys)
129: 
130:     def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
137:         try:
138:             print("------------------------------------------------------------------------------------------------")
139:             logging.info("Initialized Model Evaluation Component.")
140:             evaluate_model_response = self.evaluate_model()
141:             s3_model_path = self.model_eval_config.s3_model_key_path
143:             model_evaluation_artifact = ModelEvaluationArtifact(
144:                 is_model_accepted=evaluate_model_response.is_model_accepted,
145:                 s3_model_path=s3_model_path,
146:                 trained_model_path=self.model_trainer_artifact.trained_model_file_path,
147:                 changed_accuracy=evaluate_model_response.difference)
149:             return model_evaluation_artifact
151:         except Exception as e:
152:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 84`: Declares `evaluate_model()`.
    *   `Line 94-95`: Loads test set CSV files and splits features from targets.
    *   `Line 99-102`: Applies our custom column mapping and renaming transformations to the raw test features.
    *   `Line 104`: Loads the newly trained model object from the local trainer directory.
    *   `Line 106`: Retrieves the new model's F1-score from the trainer artifact.
    *   `Line 110-111`: Fetches the current production model from the S3 bucket registry.
    *   `Line 113-114`: Uses the production model to predict on the test features and calculates its F1-score on the test set.
    *   `Line 117-122`: Instantiates `EvaluateModelResponse`. If the new model's F1-score is strictly higher than the production model's F1-score, sets `is_model_accepted` to `True`.
    *   `Line 130`: Declares `initiate_model_evaluation()`.
    *   `Line 140`: Evaluates the model comparisons.
    *   `Line 143-147`: Instantiates and returns the `ModelEvaluationArtifact` indicating whether the new model is accepted for deployment.

---

# File 5: [src/components/model\_pusher.py](file:///c:/Projects/Vehicle-Insurance/src/components/model_pusher.py)

*   **Purpose**: Deploys the approved model to the S3 bucket registry.
*   **Who imports/calls it**: Called by `TrainPipeline`.
*   **Dependencies**: `os`, `shutil`, `src.cloud_storage.aws_storage.SimpleStorageService`, `src.entity.s3_estimator.Proj1Estimator`.

## Line-by-Line Walkthrough

### Code Block 1: Deployment & Local Cache Sync (Lines 13-61)
```python
13: class ModelPusher:
14:     def __init__(self, model_evaluation_artifact: ModelEvaluationArtifact,
15:                  model_pusher_config: ModelPusherConfig):
20:         self.s3 = SimpleStorageService()
21:         self.model_evaluation_artifact = model_evaluation_artifact
22:         self.model_pusher_config = model_pusher_config
23:         self.proj1_estimator = Proj1Estimator(bucket_name=model_pusher_config.bucket_name,
24:                                 model_path=model_pusher_config.s3_model_key_path)
25: 
26:     def initiate_model_pusher(self) -> ModelPusherArtifact:
34:         logging.info("Entered initiate_model_pusher method of ModelTrainer class")
36:         try:
37:             print("------------------------------------------------------------------------------------------------")
38:             logging.info("Uploading artifacts folder to s3 bucket")
40:             logging.info("Uploading new model to S3 bucket....")
41:             self.proj1_estimator.save_model(from_file=self.model_evaluation_artifact.trained_model_path)
42: 
43:             # Copy the accepted model locally for immediate fast local prediction fallback
44:             local_model_path = os.path.join("model", "model.pkl")
45:             try:
46:                 os.makedirs(os.path.dirname(local_model_path), exist_ok=True)
47:                 shutil.copy(self.model_evaluation_artifact.trained_model_path, local_model_path)
48:                 logging.info(f"Successfully saved a copy of the accepted model locally at {local_model_path}")
49:             except Exception as e:
50:                 logging.error(f"Failed to copy accepted model to local path: {e}")
51: 
52:             model_pusher_artifact = ModelPusherArtifact(bucket_name=self.model_pusher_config.bucket_name,
53:                                                          s3_model_path=self.model_pusher_config.s3_model_key_path)
55:             return model_pusher_artifact
56:         except Exception as e:
57:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 20-24`: Constructor instantiates connection components and the S3 Estimator.
    *   `Line 26`: Declares `initiate_model_pusher()`.
    *   `Line 41`: Calls `.save_model()` on the S3 Estimator to upload the approved model file to the S3 bucket.
    *   `Line 44-47`: Creates the local `model/` cache folder and copies the model file there using `shutil.copy()`. This updates the local cache directory (`model/model.pkl`) to allow immediate predictions.
    *   `Line 52-53`: Instantiates and returns the `ModelPusherArtifact`.
