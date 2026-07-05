# Source Code: Data Ingestion, Validation & Transformation

This section documents the source files that fetch data from MongoDB Atlas, validate it against schemas, apply scaling transformations, and handle class balancing.

---

# File 1: [src/data\_access/proj1\_data.py](file:///c:/Projects/Vehicle-Insurance/src/data_access/proj1_data.py)

*   **Purpose**: Exports MongoDB records as a pandas DataFrame.
*   **Why it exists**: Decouples dataset queries from pipeline logic.
*   **Why it is needed**: The data ingestion component needs to query all database records without managing MongoClient connections directly.
*   **Who imports/calls it**: Called by `DataIngestion` during the ingestion phase.
*   **Dependencies**: `pymongo`, `pandas`, `numpy`, `src.configuration.mongo_db_connection.MongoDBClient`.
*   **Input**: `collection_name` (string), optional `database_name`.
*   **Output**: `pd.DataFrame` containing pre-processed MongoDB collection records.

## Line-by-Line Walkthrough

### Code Block 1: Connection and Data Exporting (Lines 1-57)
```python
1: import sys
2: import pandas as pd
3: import numpy as np
4: from typing import Optional
5: 
6: from src.configuration.mongo_db_connection import MongoDBClient
7: from src.constants import DATABASE_NAME
8: from src.exception import MyException
9: 
10: class Proj1Data:
11:     """
12:     A class to export MongoDB records as a pandas DataFrame.
13:     """
14:     def __init__(self) -> None:
15:         try:
16:             self.mongo_client = MongoDBClient(database_name=DATABASE_NAME)
17:         except Exception as e:
18:             raise MyException(e, sys)
19: 
20:     def export_collection_as_dataframe(self, collection_name: str, database_name: Optional[str] = None) -> pd.DataFrame:
21:         try:
22:             # Access specified collection from the default or specified database
23:             if database_name is None:
24:                 collection = self.mongo_client.database[collection_name]
25:             else:
26:                 collection = self.mongo_client[database_name][collection_name]
27: 
28:             # Convert collection data to DataFrame and preprocess
29:             print("Fetching data from mongoDB")
30:             df = pd.DataFrame(list(collection.find()))
31:             print(f"Data fecthed with len: {len(df)}")
32:             if "id" in df.columns.to_list():
33:                 df = df.drop(columns=["id"], axis=1)
34:             df.replace({"na":np.nan},inplace=True)
35:             return df
36: 
37:         except Exception as e:
38:             raise MyException(e, sys)
```

*   **Line-by-Line Explanation**:
    *   `Line 14-16`: Constructor instantiates the cached `MongoDBClient`.
    *   `Line 20`: Declares `export_collection_as_dataframe()`.
    *   `Line 23-26`: Resolves target collection. If no database is specified, uses the client's default database instance.
    *   `Line 30`: Calls `collection.find()`. This queries all documents in the collection, returning a cursor. Passing the list cast `list(collection.find())` maps documents to a list of dicts. `pd.DataFrame(...)` converts this list into a structured DataFrame, mapping keys to column headers.
    *   `Line 32-33`: Checks if the spreadsheet row identifier `id` exists in the columns and drops it using `.drop(columns=["id"], axis=1)` to prevent features from leaking identifier data.
    *   `Line 34`: Replaces the string `"na"` with `np.nan` in-place, formatting missing cells.
    *   `Line 35`: Returns the DataFrame.
*   **Syntax/OOP/Library Concepts**: Type Hinting `Optional[str]` indicates the parameter can be a string or `None`.
*   **Runtime & Memory Behavior**: Loading an entire collection via `list(collection.find())` pulls all records into RAM. For large datasets, this can cause high memory usage.
*   **Alternatives**: For larger datasets, use batch cursor processing or database aggregation pipelines instead of pulling all records into memory.

---

# File 2: [src/components/data\_ingestion.py](file:///c:/Projects/Vehicle-Insurance/src/components/data_ingestion.py)

*   **Purpose**: Pulls raw records from MongoDB and splits them into training and testing sets.
*   **Why it exists**: Provides clean, repeatable data partitions for subsequent validation and training steps.
*   **Who imports/calls it**: Called by `TrainPipeline`.
*   **Dependencies**: `pandas`, `sklearn.model_selection.train_test_split`, `src.data_access.proj1_data.Proj1Data`.

## Line-by-Line Walkthrough

### Code Block 1: Feature Store Export (Lines 1-46)
```python
1: import os
2: import sys
3: 
4: from pandas import DataFrame
5: from sklearn.model_selection import train_test_split
6: 
7: from src.entity.config_entity import DataIngestionConfig
8: from src.entity.artifact_entity import DataIngestionArtifact
9: from src.exception import MyException
10: from src.logger import logging
11: from src.data_access.proj1_data import Proj1Data
12: 
13: class DataIngestion:
14:     def __init__(self,data_ingestion_config:DataIngestionConfig=DataIngestionConfig()):
15:         try:
16:             self.data_ingestion_config = data_ingestion_config
17:         except Exception as e:
18:             raise MyException(e,sys)
19:         
20:     def export_data_into_feature_store(self)->DataFrame:
21:         try:
22:             logging.info(f"Exporting data from mongodb")
23:             my_data = Proj1Data()
24:             dataframe = my_data.export_collection_as_dataframe(collection_name=
25:                                                                    self.data_ingestion_config.collection_name)
26:             logging.info(f"Shape of dataframe: {dataframe.shape}")
27:             feature_store_file_path  = self.data_ingestion_config.feature_store_file_path
28:             dir_path = os.path.dirname(feature_store_file_path)
29:             os.makedirs(dir_path,exist_ok=True)
30:             logging.info(f"Saving exported data into feature store file path: {feature_store_file_path}")
31:             dataframe.to_csv(feature_store_file_path,index=False,header=True)
32:             return dataframe
33:         except Exception as e:
34:             raise MyException(e,sys)
```

*   **Line-by-Line Explanation**:
    *   `Line 14-16`: Constructor saves a configuration instance `DataIngestionConfig` (defining split ratios and paths).
    *   `Line 20`: Declares `export_data_into_feature_store()`.
    *   `Line 23-25`: Instantiates `Proj1Data()` and queries MongoDB to export collection data to a DataFrame.
    *   `Line 27-29`: Extracts the target directory path from the configuration and creates it.
    *   `Line 31`: Writes the DataFrame to a feature store CSV file at `artifact/<timestamp>/data_ingestion/feature_store/data.csv`. Setting `index=False` prevents pandas from adding an unnamed index column.

---

### Code Block 2: Data Splitting and Orchestration (Lines 48-104)
```python
48:     def split_data_as_train_test(self,dataframe: DataFrame) ->None:
56:         logging.info("Entered split_data_as_train_test method of Data_Ingestion class")
57:         try:
58:             train_set, test_set = train_test_split(dataframe, test_size=self.data_ingestion_config.train_test_split_ratio)
59:             logging.info("Performed train test split on the dataframe")
64:             dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
65:             os.makedirs(dir_path,exist_ok=True)
68:             train_set.to_csv(self.data_ingestion_config.training_file_path,index=False,header=True)
69:             test_set.to_csv(self.data_ingestion_config.testing_file_path,index=False,header=True)
71:             logging.info(f"Exported train and test file path.")
72:         except Exception as e:
73:             raise MyException(e, sys) from e
74: 
75:     def initiate_data_ingestion(self) ->DataIngestionArtifact:
83:         logging.info("Entered initiate_data_ingestion method of Data_Ingestion class")
84:         try:
86:             dataframe = self.export_data_into_feature_store()
90:             self.split_data_as_train_test(dataframe)
98:             data_ingestion_artifact = DataIngestionArtifact(trained_file_path=self.data_ingestion_config.training_file_path,
99:             test_file_path=self.data_ingestion_config.testing_file_path)
101:             logging.info(f"Data ingestion artifact: {data_ingestion_artifact}")
102:             return data_ingestion_artifact
103:         except Exception as e:
104:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 48`: Declares `split_data_as_train_test()`.
    *   `Line 58`: Calls `train_test_split()` from scikit-learn. Splits the dataset into training (`train_set`) and testing (`test_set`) sets using the configured split ratio (0.25 test size).
    *   `Line 64-65`: Creates directories for the partitioned files.
    *   `Line 68-69`: Exports training data to `train.csv` and testing data to `test.csv`.
    *   `Line 75`: Declares `initiate_data_ingestion()`.
    *   `Line 86`: Triggers MongoDB data export to the feature store CSV.
    *   `Line 90`: Triggers the training and testing partition splits.
    *   `Line 98-99`: Instantiates and returns a `DataIngestionArtifact` containing the paths to `train.csv` and `test.csv`.

---

# File 3: [src/components/data\_validation.py](file:///c:/Projects/Vehicle-Insurance/src/components/data_validation.py)

*   **Purpose**: Validates the schema of the ingested dataset.
*   **Why it exists**: Prevents downstream component failures caused by schema changes or missing columns in raw database records.
*   **Who imports/calls it**: Called by `TrainPipeline` after ingestion.
*   **Dependencies**: `json`, `pandas`, `PyYAML`, `src.utils.main_utils.read_yaml_file`.
*   **Input**: `DataIngestionArtifact`.
*   **Output**: `DataValidationArtifact` (contains boolean validation status).

## Line-by-Line Walkthrough

### Code Block 1: Schema Checks (Lines 17-74)
```python
17: class DataValidation:
18:     def __init__(self, data_ingestion_artifact: DataIngestionArtifact, data_validation_config: DataValidationConfig):
23:         try:
24:             self.data_ingestion_artifact = data_ingestion_artifact
25:             self.data_validation_config = data_validation_config
26:             self._schema_config =read_yaml_file(file_path=SCHEMA_FILE_PATH)
27:         except Exception as e:
28:             raise MyException(e,sys)
29: 
30:     def validate_number_of_columns(self, dataframe: DataFrame) -> bool:
38:         try:
39:             status = len(dataframe.columns) == len(self._schema_config["columns"])
40:             logging.info(f"Is required column present: [{status}]")
41:             return status
42:         except Exception as e:
43:             raise MyException(e, sys)
44: 
45:     def is_column_exist(self, df: DataFrame) -> bool:
53:         try:
54:             dataframe_columns = df.columns
55:             missing_numerical_columns = []
56:             missing_categorical_columns = []
57:             for column in self._schema_config["numerical_columns"]:
58:                 if column not in dataframe_columns:
59:                     missing_numerical_columns.append(column)
60: 
61:             if len(missing_numerical_columns)>0:
62:                 logging.info(f"Missing numerical column: {missing_numerical_columns}")
63: 
64:             for column in self._schema_config["categorical_columns"]:
65:                 if column not in dataframe_columns:
66:                     missing_categorical_columns.append(column)
67: 
68:             if len(missing_categorical_columns)>0:
69:                 logging.info(f"Missing categorical column: {missing_categorical_columns}")
71:             return False if len(missing_categorical_columns)>0 or len(missing_numerical_columns)>0 else True
72:         except Exception as e:
73:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 18`: Constructor takes the ingestion artifact and validation configuration.
    *   `Line 26`: Loads schema requirements from `config/schema.yaml` into a dictionary helper object `self._schema_config`.
    *   `Line 30`: Declares `validate_number_of_columns()`.
    *   `Line 39`: Compares the dataframe's column count against the count defined in the schema configuration.
    *   `Line 45`: Declares `is_column_exist()`.
    *   `Line 57-59`: Loops through the configured `numerical_columns`. If any are missing, adds them to `missing_numerical_columns`.
    *   `Line 64-66`: Loops through `categorical_columns` to check for missing categories.
    *   `Line 71`: Returns `False` if any categorical or numerical columns are missing; otherwise, returns `True`.

---

### Code Block 2: Validation Orchestration (Lines 84-150)
```python
84:     def initiate_data_validation(self) -> DataValidationArtifact:
93:         try:
94:             validation_error_msg = ""
95:             logging.info("Starting data validation")
96:             train_df, test_df = (DataValidation.read_data(file_path=self.data_ingestion_artifact.trained_file_path),
97:                                  DataValidation.read_data(file_path=self.data_ingestion_artifact.test_file_path))
98: 
99:             # Checking col len of dataframe for train/test df
100:             status = self.validate_number_of_columns(dataframe=train_df)
101:             if not status:
102:                 validation_error_msg += f"Columns are missing in training dataframe. "
106:             status = self.validate_number_of_columns(dataframe=test_df)
107:             if not status:
108:                 validation_error_msg += f"Columns are missing in test dataframe. "
113:             # Validating col dtype for train/test df
114:             status = self.is_column_exist(df=train_df)
115:             if not status:
116:                 validation_error_msg += f"Columns are missing in training dataframe. "
119:             status = self.is_column_exist(df=test_df)
120:             if not status:
121:                 validation_error_msg += f"Columns are missing in test dataframe."
125:             validation_status = len(validation_error_msg) == 0
127:             data_validation_artifact = DataValidationArtifact(
128:                 validation_status=validation_status,
129:                 message=validation_error_msg,
130:                 validation_report_file_path=self.data_validation_config.validation_report_file_path
131:             )
134:             report_dir = os.path.dirname(self.data_validation_config.validation_report_file_path)
135:             os.makedirs(report_dir, exist_ok=True)
138:             validation_report = {
139:                 "validation_status": validation_status,
140:                 "message": validation_error_msg.strip()
141:             }
143:             with open(self.data_validation_config.validation_report_file_path, "w") as report_file:
144:                 json.dump(validation_report, report_file, indent=4)
147:             return data_validation_artifact
149:         except Exception as e:
150:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 84`: Declares `initiate_data_validation()`.
    *   `Line 96-97`: Reads `train.csv` and `test.csv` into DataFrames.
    *   `Line 100-108`: Checks the column count for both training and testing sets.
    *   `Line 114-121`: Confirms the presence of all configured numerical and categorical columns.
    *   `Line 125`: Sets `validation_status` to `True` if no error messages were generated; otherwise, sets it to `False`.
    *   `Line 127`: Instantiates the validation artifact.
    *   `Line 134-135`: Creates the directory for the report file.
    *   `Line 138-141`: Formats the status details into a dictionary.
    *   `Line 143-144`: Opens the report path and saves the validation results as JSON using `json.dump()`.
    *   `Line 147`: Returns the `DataValidationArtifact`.
*   **Production Improvements/Issues**:
    *   *YAML Extension Bug*: The target file path is configured as `report.yaml` in the constants, but this method uses `json.dump()` to write validation results in JSON format rather than YAML.

---

# File 4: [src/components/data\_transformation.py](file:///c:/Projects/Vehicle-Insurance/src/components/data_transformation.py)

*   **Purpose**: Encodes categoricals, standardizes numerical features, scales premiums, and balances classes.
*   **Why it exists**: Prepares the raw dataset for training.
*   **Who imports/calls it**: Called by `TrainPipeline`.
*   **Dependencies**: `pandas`, `numpy`, `imblearn.combine.SMOTEENN`, `sklearn.preprocessing.StandardScaler`, `sklearn.preprocessing.MinMaxScaler`, `sklearn.compose.ColumnTransformer`, `sklearn.pipeline.Pipeline`, `src.utils.main_utils`.

## Line-by-Line Walkthrough

### Code Block 1: ColumnTransformer Object Setup (Lines 36-73)
```python
36:     def get_data_transformer_object(self) -> Pipeline:
37:         """
38:         Creates and returns a data transformer object for the data, 
39:         including scaling and column selection.
40:         """
41:         try:
42:             # Initialize transformers
43:             numeric_transformer = StandardScaler()
44:             min_max_scaler = MinMaxScaler()
45:             logging.info("Transformers Initialized: StandardScaler-MinMaxScaler")
46: 
47:             # Load schema configurations
48:             num_features = self._schema_config['num_features']
49:             mm_columns = self._schema_config['mm_columns']
50:             logging.info("Cols loaded from schema.")
51: 
52:             # Creating preprocessor pipeline
53:             preprocessor = ColumnTransformer(
54:                 transformers=[
55:                     ("StandardScaler", numeric_transformer, num_features),
56:                     ("MinMaxScaler", min_max_scaler, mm_columns)
57:                 ],
58:                 remainder='passthrough'  # Leaves other columns as they are
59:             )
60: 
61:             # Wrapping everything in a single pipeline
62:             final_pipeline = Pipeline(steps=[("Preprocessor", preprocessor)])
63:             return final_pipeline
64:         except Exception as e:
65:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 36`: Declares `get_data_transformer_object()`.
    *   `Line 43-44`: Instantiates `StandardScaler` (for z-score scaling) and `MinMaxScaler` (for scaling variables between 0 and 1).
    *   `Line 48-49`: Reads lists of target features from the schema configuration: `num_features` (`['Age', 'Vintage']`) and `mm_columns` (`['Annual_Premium']`).
    *   `Line 53-59`: Instantiates a `ColumnTransformer` object. This applies scaling methods to specific subsets of columns while leaving the remaining columns untouched using the `remainder='passthrough'` parameter.
    *   `Line 62`: Wraps the preprocessor inside a scikit-learn `Pipeline` object and returns it.

---

### Code Block 2: Custom Mapping Functions (Lines 74-105)
```python
74:     def _map_gender_column(self, df):
75:         """Map Gender column to 0 for Female and 1 for Male."""
76:         logging.info("Mapping 'Gender' column to binary values")
77:         df['Gender'] = df['Gender'].map({'Female': 0, 'Male': 1}).astype(int)
78:         return df
79: 
80:     def _create_dummy_columns(self, df):
81:         """Create dummy variables for categorical features."""
82:         logging.info("Creating dummy variables for categorical features")
83:         df = pd.get_dummies(df, drop_first=True)
84:         return df
85: 
86:     def _rename_columns(self, df):
87:         """Rename specific columns and ensure integer types for dummy columns."""
88:         logging.info("Renaming specific columns and casting to int")
89:         df = df.rename(columns={
90:             "Vehicle_Age_< 1 Year": "Vehicle_Age_lt_1_Year",
91:             "Vehicle_Age_> 2 Years": "Vehicle_Age_gt_2_Years"
92:         })
93:         for col in ["Vehicle_Age_lt_1_Year", "Vehicle_Age_gt_2_Years", "Vehicle_Damage_Yes"]:
94:             if col in df.columns:
95:                 df[col] = df[col].astype('int')
96:         return df
97: 
98:     def _drop_id_column(self, df):
99:         """Drop the 'id' column if it exists."""
100:         logging.info("Dropping 'id' column")
101:         drop_col = self._schema_config['drop_columns']
102:         if drop_col in df.columns:
103:             df = df.drop(drop_col, axis=1)
104:         return df
```

*   **Line-by-Line Explanation**:
    *   `Line 74`: Maps the string categories `"Female"` and `"Male"` to binary integers `0` and `1`.
    *   `Line 80`: Call `pd.get_dummies(df, drop_first=True)` to one-hot encode categorical features. Specifying `drop_first=True` drops the first alphabetical category to prevent multicollinearity.
    *   `Line 86`: Renames columns containing special character symbols (e.g., `<` and `>`) to valid alphanumeric column headers and casts them to standard integers.
    *   `Line 98`: Drops the identifier column specified in `schema.yaml` (`_id`).

---

### Code Block 3: Transformation Execution and Class Balancing (Lines 106-176)
```python
106:     def initiate_data_transformation(self) -> DataTransformationArtifact:
110:         try:
111:             logging.info("Data Transformation Started !!!")
112:             if not self.data_validation_artifact.validation_status:
113:                 raise Exception(self.data_validation_artifact.message)
115:             # Load train and test data
116:             train_df = self.read_data(file_path=self.data_ingestion_artifact.trained_file_path)
117:             test_df = self.read_data(file_path=self.data_ingestion_artifact.test_file_path)
120:             input_feature_train_df = train_df.drop(columns=[TARGET_COLUMN], axis=1)
121:             target_feature_train_df = train_df[TARGET_COLUMN]
123:             input_feature_test_df = test_df.drop(columns=[TARGET_COLUMN], axis=1)
124:             target_feature_test_df = test_df[TARGET_COLUMN]
128:             # Apply custom transformations in specified sequence
129:             input_feature_train_df = self._map_gender_column(input_feature_train_df)
130:             input_feature_train_df = self._drop_id_column(input_feature_train_df)
131:             input_feature_train_df = self._create_dummy_columns(input_feature_train_df)
132:             input_feature_train_df = self._rename_columns(input_feature_train_df)
134:             input_feature_test_df = self._map_gender_column(input_feature_test_df)
135:             input_feature_test_df = self._drop_id_column(input_feature_test_df)
136:             input_feature_test_df = self._create_dummy_columns(input_feature_test_df)
137:             input_feature_test_df = self._rename_columns(input_feature_test_df)
140:             preprocessor = self.get_data_transformer_object()
144:             input_feature_train_arr = preprocessor.fit_transform(input_feature_train_df)
146:             input_feature_test_arr = preprocessor.transform(input_feature_test_df)
150:             smt = SMOTEENN(sampling_strategy="minority")
151:             input_feature_train_final, target_feature_train_final = smt.fit_resample(
152:                 input_feature_train_arr, target_feature_train_df
153:             )
154:             input_feature_test_final, target_feature_test_final = smt.fit_resample(
155:                 input_feature_test_arr, target_feature_test_df
156:             )
159:             train_arr = np.c_[input_feature_train_final, np.array(target_feature_train_final)]
160:             test_arr = np.c_[input_feature_test_final, np.array(target_feature_test_final)]
163:             save_object(self.data_transformation_config.transformed_object_file_path, preprocessor)
164:             save_numpy_array_data(self.data_transformation_config.transformed_train_file_path, array=train_arr)
165:             save_numpy_array_data(self.data_transformation_config.transformed_test_file_path, array=test_arr)
168:             return DataTransformationArtifact(
169:                 transformed_object_file_path=self.data_transformation_config.transformed_object_file_path,
170:                 transformed_train_file_path=self.data_transformation_config.transformed_train_file_path,
171:                 transformed_test_file_path=self.data_transformation_config.transformed_test_file_path
172:             )
175:         except Exception as e:
176:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 112`: Checks the validation status from the previous stage. If validation failed, raises an exception and halts execution.
    *   `Line 116-117`: Loads the split CSV files from data ingestion into DataFrames.
    *   `Line 120-124`: Separates input features from target columns (`Response`).
    *   `Line 129-137`: Applies our custom column mapping, identifier dropping, dummy encoding, and column renaming methods to both training and testing datasets.
    *   `Line 144`: Fits and transforms the training features using our `ColumnTransformer` object.
    *   `Line 146`: Applies the fitted transformations to the testing features.
    *   `Line 150`: Instantiates a `SMOTEENN` sampler specifying `"minority"` to oversample the minority class.
    *   `Line 151-156`: Calls `fit_resample()` to perform oversampling and data cleaning on both training and testing sets, returning balanced feature arrays and targets.
    *   `Line 159-160`: Concatenates the balanced features and target arrays along columns using NumPy's column bind function `np.c_`.
    *   `Line 163-165`: Serializes the preprocessing pipeline object as `preprocessing.pkl` and saves the balanced datasets as `.npy` array files.
    *   `Line 168`: Instantiates and returns the `DataTransformationArtifact`.
*   **Interview Questions**:
    *   *What does np.c_ do?* It translates slice objects to concatenation along the second axis (column-wise concatenation). It is a convenient shorthand for merging 2D arrays side-by-side.
    *   *Why fit the preprocessor on training data but only call transform on testing data?* Fitting computes parameters like mean and standard deviation from the training set. Calling `transform` on the test set scales it using these same training parameters, preventing data leakage from the test set into the model.
