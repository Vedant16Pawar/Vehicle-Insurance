# Source Code: Orchestration, Web App & Templates

This section covers the pipeline orchestration layers, prediction data wrappers, and the FastAPI application routes.

---

# File 1: [src/pipline/training\_pipeline.py](file:///c:/Projects/Vehicle-Insurance/src/pipline/training_pipeline.py)

*   **Purpose**: Coordinates the execution flow of the machine learning training pipeline.
*   **Why it exists**: Provides a single execution interface that chains ingestion, validation, transformation, training, evaluation, and pusher components.
*   **Who imports/calls it**: Called by `app.py` (via `/train` route) or `demo.py` (runner script).
*   **Dependencies**: Exposes dependencies to all subcomponents (`DataIngestion`, `DataValidation`, etc.) and configuration/artifact entities.

## Line-by-Line Walkthrough

### Code Block 1: Pipeline Orchestrator (Lines 36-168)
```python
36: class TrainPipeline:
37:     def __init__(self):
38:         self.data_ingestion_config = DataIngestionConfig()
39:         self.data_validation_config = DataValidationConfig()
40: 
41:         self.data_transformation_config = DataTransformationConfig()
42:         self.model_trainer_config = ModelTrainerConfig()
43:         self.model_evaluation_config = ModelEvaluationConfig()
44:         self.model_pusher_config = ModelPusherConfig()
...
50:     def start_data_ingestion(self) -> DataIngestionArtifact:
55:         try:
56:             logging.info("Entered the start_data_ingestion method of TrainPipeline class")
57:             logging.info("Getting the data from mongodb")
58:             data_ingestion = DataIngestion(data_ingestion_config=self.data_ingestion_config)
59:             data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
60:             logging.info("Got the train_set and test_set from mongodb")
61:             logging.info("Exited the start_data_ingestion method of TrainPipeline class")
62:             return data_ingestion_artifact
63:         except Exception as e:
64:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 36`: Declares class `TrainPipeline`.
    *   `Line 37-44`: Constructor instantiates all pipeline configuration entities. These classes read default paths and constants to define execution targets.
    *   `Line 50`: Declares `start_data_ingestion()`.
    *   `Line 58`: Instantiates `DataIngestion` with configurations.
    *   `Line 59`: Triggers ingestion, which fetches records from MongoDB and splits train/test datasets.
    *   `Line 62`: Returns the generated `DataIngestionArtifact` containing the file paths.

---

### Code Block 2: Component Invocation & execution logic (Lines 66-168)
```python
66:     def start_data_validation(self, data_ingestion_artifact: DataIngestionArtifact) -> DataValidationArtifact:
70:         logging.info("Entered the start_data_validation method of TrainPipeline class")
72:         try:
73:             data_validation = DataValidation(data_ingestion_artifact=data_ingestion_artifact,
74:                                              data_validation_config=self.data_validation_config
75:                                              )
77:             data_validation_artifact = data_validation.initiate_data_validation()
82:             return data_validation_artifact
83:         except Exception as e:
84:             raise MyException(e, sys) from e
85: 
86: 
87:     def start_data_transformation(self, data_ingestion_artifact: DataIngestionArtifact, data_validation_artifact: DataValidationArtifact) -> DataTransformationArtifact:
91:         try:
92:             data_transformation = DataTransformation(data_ingestion_artifact=data_ingestion_artifact,
93:                                                      data_transformation_config=self.data_transformation_config,
94:                                                      data_validation_artifact=data_validation_artifact)
95:             data_transformation_artifact = data_transformation.initiate_data_transformation()
96:             return data_transformation_artifact
97:         except Exception as e:
98:             raise MyException(e, sys)
```

*   **Line-by-Line Explanation**:
    *   `Line 66`: Declares `start_data_validation()`.
    *   `Line 73`: Instantiates the validation step, passing the ingestion artifact to provide input file path locations.
    *   `Line 77`: Runs the validation checks and returns the validation artifact.
    *   `Line 87`: Declares `start_data_transformation()`.
    *   `Line 92-94`: Instantiates transformation, passing the ingestion and validation artifacts.
    *   `Line 95`: Performs preprocessing and class balancing, returning output array path references.

---

### Code Block 3: Model Training, Evaluation & Pusher chaining (Lines 101-168)
```python
101:     def start_model_trainer(self, data_transformation_artifact: DataTransformationArtifact) -> ModelTrainerArtifact:
105:         try:
106:             model_trainer = ModelTrainer(data_transformation_artifact=data_transformation_artifact,
107:                                          model_trainer_config=self.model_trainer_config
108:                                          )
109:             model_trainer_artifact = model_trainer.initiate_model_trainer()
110:             return model_trainer_artifact
111:         except Exception as e:
112:             raise MyException(e, sys)
113:         
114:     
115:     def start_model_evaluation(self, data_ingestion_artifact: DataIngestionArtifact,
116:                                model_trainer_artifact: ModelTrainerArtifact) -> ModelEvaluationArtifact:
121:         try:
122:             model_evaluation = ModelEvaluation(model_eval_config=self.model_evaluation_config,
123:                                                data_ingestion_artifact=data_ingestion_artifact,
124:                                                model_trainer_artifact=model_trainer_artifact)
125:             model_evaluation_artifact = model_evaluation.initiate_model_evaluation()
126:             return model_evaluation_artifact
127:         except Exception as e:
128:             raise MyException(e, sys)
129: 
130:     
131:     def start_model_pusher(self, model_evaluation_artifact: ModelEvaluationArtifact) -> ModelPusherArtifact:
135:         try:
136:             model_pusher = ModelPusher(model_evaluation_artifact=model_evaluation_artifact,
137:                                        model_pusher_config=self.model_pusher_config
138:                                        )
139:             model_pusher_artifact = model_pusher.initiate_model_pusher()
140:             return model_pusher_artifact
141:         except Exception as e:
142:             raise MyException(e, sys)
143: 
144: 
145:     def run_pipeline(self, ) -> None:
149:         try:
150:             data_ingestion_artifact = self.start_data_ingestion()
151:             data_validation_artifact = self.start_data_validation(data_ingestion_artifact=data_ingestion_artifact)
152:             data_transformation_artifact = self.start_data_transformation(
153:             data_ingestion_artifact=data_ingestion_artifact, data_validation_artifact=data_validation_artifact
154:             )
155:             
156:             model_trainer_artifact = self.start_model_trainer(data_transformation_artifact=data_transformation_artifact)
157:             model_evaluation_artifact = self.start_model_evaluation(data_ingestion_artifact=data_ingestion_artifact,
158:                                                                     model_trainer_artifact=model_trainer_artifact)
159:             if not model_evaluation_artifact.is_model_accepted:
160:                 logging.info(f"Model not accepted.")
161:                 return None
162:             model_pusher_artifact = self.start_model_pusher(model_evaluation_artifact=model_evaluation_artifact)
167:         except Exception as e:
168:             raise MyException(e, sys)
```

*   **Line-by-Line Explanation**:
    *   `Line 101`: Declares `start_model_trainer()`.
    *   `Line 106-108`: Instantiates `ModelTrainer` with transform artifact targets.
    *   `Line 109`: Trains the model and returns trainer artifacts.
    *   `Line 115`: Declares `start_model_evaluation()`.
    *   `Line 122-124`: Instantiates evaluation to compare model metrics.
    *   `Line 125`: Runs evaluation comparison and returns evaluation artifacts.
    *   `Line 131`: Declares `start_model_pusher()`.
    *   `Line 136-138`: Instantiates pusher with evaluation artifact targets.
    *   `Line 139`: Runs the model pusher to upload the approved model.
    *   `Line 145`: Declares core orchestration entry point `run_pipeline()`.
    *   `Line 150-158`: Sequentially calls components, passing artifacts between them.
    *   `Line 159-161`: Evaluates the model acceptance status. If `False`, execution stops and the model is not pushed to production.
    *   `Line 162`: If accepted, pushes the model to production.

---

# File 2: [src/pipline/prediction\_pipeline.py](file:///c:/Projects/Vehicle-Insurance/src/pipline/prediction_pipeline.py)

*   **Purpose**: Represents user form inputs and executes model inference.
*   **Who imports/calls it**: Imported by `app.py` to map form POST requests to predictions.
*   **Dependencies**: `pandas.DataFrame`, `src.entity.s3_estimator.Proj1Estimator`.

## Line-by-Line Walkthrough

### Code Block 1: Prediction Pipeline Classes (Lines 9-112)
```python
9: class VehicleData:
10:     def __init__(self,
11:                 Gender,
12:                 Age,
13:                 Driving_License,
14:                 Region_Code,
15:                 Previously_Insured,
16:                 Annual_Premium,
17:                 Policy_Sales_Channel,
18:                 Vintage,
19:                 Vehicle_Age_lt_1_Year,
20:                 Vehicle_Age_gt_2_Years,
21:                 Vehicle_Damage_Yes
22:                 ):
27:         try:
28:             self.Gender = Gender
29:             self.Age = Age
30:             self.Driving_License = Driving_License
31:             self.Region_Code = Region_Code
32:             self.Previously_Insured = Previously_Insured
33:             self.Annual_Premium = Annual_Premium
34:             self.Policy_Sales_Channel = Policy_Sales_Channel
35:             self.Vintage = Vintage
36:             self.Vehicle_Age_lt_1_Year = Vehicle_Age_lt_1_Year
37:             self.Vehicle_Age_gt_2_Years = Vehicle_Age_gt_2_Years
38:             self.Vehicle_Damage_Yes = Vehicle_Damage_Yes
39:         except Exception as e:
40:             raise MyException(e, sys) from e
41: 
42:     def get_vehicle_input_data_frame(self)-> DataFrame:
47:         try:
49:             vehicle_input_dict = self.get_vehicle_data_as_dict()
50:             return DataFrame(vehicle_input_dict)
51:         except Exception as e:
52:             raise MyException(e, sys) from e
53: 
54: 
55:     def get_vehicle_data_as_dict(self):
60:         logging.info("Entered get_usvisa_data_as_dict method as VehicleData class")
62:         try:
63:             input_data = {
64:                 "Gender": [self.Gender],
65:                 "Age": [self.Age],
66:                 "Driving_License": [self.Driving_License],
67:                 "Region_Code": [self.Region_Code],
68:                 "Previously_Insured": [self.Previously_Insured],
69:                 "Annual_Premium": [self.Annual_Premium],
70:                 "Policy_Sales_Channel": [self.Policy_Sales_Channel],
71:                 "Vintage": [self.Vintage],
72:                 "Vehicle_Age_lt_1_Year": [self.Vehicle_Age_lt_1_Year],
73:                 "Vehicle_Age_gt_2_Years": [self.Vehicle_Age_gt_2_Years],
74:                 "Vehicle_Damage_Yes": [self.Vehicle_Damage_Yes]
75:             }
79:             return input_data
80:         except Exception as e:
81:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 9`: Declares `VehicleData` to structure input parameters.
    *   `Line 10-22`: Constructor accepts the 11 feature variables.
    *   `Line 28-38`: Maps parameters to instance attributes.
    *   `Line 42`: Declares `get_vehicle_input_data_frame()`.
    *   `Line 49-50`: Retrieves data as a dictionary and converts it to a pandas DataFrame.
    *   `Line 55`: Declares `get_vehicle_data_as_dict()`.
    *   `Line 63-75`: Constructs a dictionary where values are nested inside lists (e.g., `[self.Gender]`) to allow pandas to build a single-row DataFrame.
*   **Code Quality Note**:
    *   *Mislabeled Log Message*: The log message on line 60 says `"Entered get_usvisa_data_as_dict method as VehicleData class"`, which is a copy-paste residual from a different project codebase.

---

### Code Block 2: Classifier integration (Lines 86-112)
```python
86: class VehicleDataClassifier:
87:     def __init__(self,prediction_pipeline_config: VehiclePredictorConfig = VehiclePredictorConfig(),) -> None:
91:         try:
92:             self.prediction_pipeline_config = prediction_pipeline_config
94:             self.model = Proj1Estimator(
95:                 bucket_name=self.prediction_pipeline_config.model_bucket_name,
96:                 model_path=self.prediction_pipeline_config.model_file_path,
97:             )
98:         except Exception as e:
99:             raise MyException(e, sys)
100: 
101:     def predict(self, dataframe) -> str:
105:         try:
107:             logging.info("Entered predict method of VehicleDataClassifier class")
109:             return self.model.predict(dataframe)
111:         except Exception as e:
112:             raise MyException(e, sys)
```

*   **Line-by-Line Explanation**:
    *   `Line 86`: Declares wrapper class `VehicleDataClassifier`.
    *   `Line 87`: Constructor accepts prediction configuration settings.
    *   `Line 94-97`: Instantiates the `Proj1Estimator` class with the target S3 bucket name and model file path key.
    *   `Line 101`: Declares `predict()`.
    *   `Line 109`: Calls `.predict()` on the S3 estimator and returns the prediction result.

---

# File 3: [app.py](file:///c:/Projects/Vehicle-Insurance/app.py)

*   **Purpose**: Exposes FastAPI endpoints for serving predictions and triggering training.
*   **Who calls it**: Executed by the application server (Uvicorn).
*   **Dependencies**: `fastapi`, `uvicorn`, `jinja2`, `src.pipline.prediction_pipeline`, `src.pipline.training_pipeline`.

## Line-by-Line Walkthrough

### Code Block 1: Application Initialization (Lines 1-38)
```python
1: from fastapi import FastAPI, Request
2: from fastapi.middleware.cors import CORSMiddleware
3: from fastapi.responses import Response
4: from fastapi.staticfiles import StaticFiles
5: from fastapi.templating import Jinja2Templates
6: from starlette.responses import HTMLResponse, RedirectResponse
7: from uvicorn import run as app_run
...
14: from src.constants import APP_HOST, APP_PORT
15: from src.pipline.prediction_pipeline import VehicleData, VehicleDataClassifier
16: from src.pipline.training_pipeline import TrainPipeline
17: 
18: # Initialize FastAPI application
19: app = FastAPI()
20: 
21: # Mount the 'static' directory for serving static files (like CSS)
22: app.mount("/static", StaticFiles(directory="static"), name="static")
23: 
24: # Set up Jinja2 template engine for rendering HTML templates
25: templates = Jinja2Templates(directory='templates')
26: 
27: # Allow all origins for Cross-Origin Resource Sharing (CORS)
28: origins = ["*"]
29: 
30: # Configure middleware to handle CORS, allowing requests from any origin
31: app.add_middleware(
32:     CORSMiddleware,
33:     allow_origins=origins,
34:     allow_credentials=True,
35:     allow_methods=["*"],
36:     allow_headers=["*"],
37: )
```

*   **Line-by-Line Explanation**:
    *   `Line 1-7`: Imports components from `fastapi`, `starlette`, and `uvicorn`.
    *   `Line 19`: Instantiates `app = FastAPI()`.
    *   `Line 22`: Mounts the static directory `/static` pointing to the local folder `./static`.
    *   `Line 25`: Configures `Jinja2Templates` to look for templates in the `./templates` folder.
    *   `Line 31-37`: Configures `CORSMiddleware` to allow requests from any origin (`allow_origins=["*"]`).

---

### Code Block 2: DataForm & API Routes (Lines 39-106)
```python
39: class DataForm:
40:     """
41:     DataForm class to handle and process incoming form data.
42:     """
43:     def __init__(self, request: Request):
44:         self.request: Request = request
45:         self.Gender: Optional[int] = None
...
59:     async def get_vehicle_data(self):
64:         form = await self.request.form()
65:         self.Gender = form.get("Gender")
...
75:         self.Vehicle_Damage_Yes = form.get("Vehicle_Damage_Yes")
76: 
80: @app.get("/", tags=["authentication"])
81: async def index(request: Request):
85:     return templates.TemplateResponse(
86:         request=request,
87:         name="vehicledata.html",
88:         context={
89:             "request": request,
90:             "context": "Rendering"
91:         }
92:     )
93: # Route to trigger the model training process
94: @app.get("/train")
95: async def trainRouteClient():
99:     try:
100:         train_pipeline = TrainPipeline()
101:         train_pipeline.run_pipeline()
102:         return Response("Training successful!!!")
104:     except Exception as e:
105:         return Response(f"Error Occurred! {e}")
```

*   **Line-by-Line Explanation**:
    *   `Line 39`: Declares helper class `DataForm` to extract variables from raw request structures.
    *   `Line 59`: Declares asynchronous method `get_vehicle_data()`.
    *   `Line 64`: Calls `await self.request.form()`. This reads raw form boundaries asynchronously without blocking the server event loop.
    *   `Line 65-75`: Extracts fields and saves them to instance attributes.
    *   `Line 80`: Declares `index` route handler for `GET /`.
    *   `Line 85`: Returns `vehicledata.html` using Jinja2 templates, rendering the prediction input form.
    *   `Line 94`: Declares route handler for `GET /train`.
    *   `Line 100-101`: Instantiates and executes the training pipeline, returning a success message.

---

### Code Block 3: Prediction Endpoint (Lines 107-163)
```python
107: # Initialize the prediction pipeline
108: model_predictor = VehicleDataClassifier()
109: # Route to handle form submission and make predictions
110: @app.post("/")
111: async def predictRouteClient(request: Request):
115:     try:
116:         form = DataForm(request)
117:         await form.get_vehicle_data()
119:         vehicle_data = VehicleData(
120:                                 Gender= form.Gender,
121:                                 Age = form.Age,
...
130:                                 Vehicle_Damage_Yes = form.Vehicle_Damage_Yes
131:                                 )
134:         vehicle_df = vehicle_data.get_vehicle_input_data_frame()
139:         value = model_predictor.predict(dataframe=vehicle_df)[0]
142:         status = "Response-Yes" if value == 1 else "Response-No"
145:         return templates.TemplateResponse(
146:             request=request,
147:             name="vehicledata.html",
148:             context={
149:                 "request": request,
150:                 "context": status,
151:             },
152:         )
154:     except Exception as e:
155:         return {"status": False, "error": f"{e}"}
158: if __name__ == "__main__":
159:     app_run(app, host=APP_HOST, port=APP_PORT)
```

*   **Line-by-Line Explanation**:
    *   `Line 108`: Instantiates `VehicleDataClassifier` globally during module load.
    *   `Line 110`: Declares route handler for form submissions (`POST /`).
    *   `Line 117`: Extracts data from the submitted form asynchronously.
    *   `Line 119-131`: Instantiates the `VehicleData` input wrapper class.
    *   `Line 134`: Converts the input data into a single-row DataFrame.
    *   `Line 139`: Calls `model_predictor.predict(dataframe=vehicle_df)` to get classification results.
    *   `Line 142`: Maps output prediction integers to user-friendly strings (`1` ➔ `"Response-Yes"`, `0` ➔ `"Response-No"`).
    *   `Line 145-152`: Renders the same HTML page, displaying the prediction result.
    *   `Line 158-159`: Starts the server on port 5000 if run directly.

---

# File 4: [demo.py](file:///c:/Projects/Vehicle-Insurance/demo.py)

*   **Purpose**: Script to trigger model training from command line shell environments.
*   **Why it exists**: Allows engineers to run training without launching the web server.

## Line-by-Line Walkthrough

### Code Block 1: Runner (Lines 1-28)
```python
1: from src.logger import logging
2: from src.exception import  MyException
3: import sys
...
25: from src.pipline.training_pipeline import TrainPipeline
26: 
27: pipline = TrainPipeline()
28: pipline.run_pipeline()
```

*   **Line-by-Line Explanation**:
    *   `Line 25`: Imports the `TrainPipeline` class.
    *   `Line 27`: Instantiates the training pipeline.
    *   `Line 28`: Executes the pipeline stages sequentially.

---

# File 5: [template.py](file:///c:/Projects/Vehicle-Insurance/template.py)

*   **Purpose**: Creates the initial project directories and empty file templates.
*   **Why it exists**: Automates the setup of boilerplate folders and module files.

## Line-by-Line Walkthrough

### Code Block 1: Folder Scaffolding generator (Lines 1-60)
```python
1: import os
2: from pathlib import Path
3: 
4: project_name = "src"
8: list_of_files = [
10:     f"{project_name}/__init__.py",
11:     f"{project_name}/components/__init__.py",
...
47: ]
51: for filepath in list_of_files:
52:     filepath = Path(filepath)
53:     filedir, filename = os.path.split(filepath)
54:     if filedir != "":
55:         os.makedirs(filedir, exist_ok=True)
56:     if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
57:         with open(filepath, "w") as f:
58:             pass
59:     else:
60:         print(f"file is already present at: {filepath}")
```

*   **Line-by-Line Explanation**:
    *   `Line 2`: Imports `Path` from standard library `pathlib` for file path normalization.
    *   `Line 8-47`: Declares a list of target project paths.
    *   `Line 51`: Loops through each path.
    *   `Line 53`: Splits directories from filenames using `os.path.split()`.
    *   `Line 54-55`: If directory structures are specified, creates them recursively.
    *   `Line 56-58`: If a file does not exist or has a size of 0 bytes, creates it using write mode `"w"`.
