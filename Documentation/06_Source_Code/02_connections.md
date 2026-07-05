# Source Code: Database & Cloud Storage Connections

This section documents the connection drivers and storage client services interacting with MongoDB Atlas and AWS S3 buckets.

---

# File 1: [src/configuration/aws\_connection.py](file:///c:/Projects/Vehicle-Insurance/src/configuration/aws_connection.py)

*   **Purpose**: Creates and caches connections to AWS S3.
*   **Why it exists**: Isolates credential retrieval and client initialization from individual storage queries.
*   **Why it is needed**: Rather than reconnecting on every file upload or download, this class maintains shared S3 resources.
*   **Who imports/calls it**: Imported by the `SimpleStorageService` class.
*   **Dependencies**: `boto3`, `os`, `botocore.config.Config`, `src.constants`.
*   **Execution flow**:
    1.  Checks if the shared connection objects (`s3_resource`, `s3_client`) already exist.
    2.  If not, retrieves environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.
    3.  Throws exceptions if environment credentials are not configured.
    4.  Defines request and read timeout configurations.
    5.  Establishes S3 resource and client connections using `boto3`.

## Line-by-Line Walkthrough

### Code Block 1: Connection Initialization (Lines 1-45)
```python
1: import boto3
2: import os
3: from botocore.config import Config
4: from src.constants import AWS_SECRET_ACCESS_KEY_ENV_KEY, AWS_ACCESS_KEY_ID_ENV_KEY, REGION_NAME
5: 
6: 
7: class S3Client:
8: 
9:     s3_client=None
10:     s3_resource = None
11:     def __init__(self, region_name=REGION_NAME):
12:         """ 
13:         This Class gets aws credentials from env_variable and creates an connection with s3 bucket 
14:         and raise exception when environment variable is not set
15:         """
16: 
17:         if S3Client.s3_resource==None or S3Client.s3_client==None:
18:             __access_key_id = os.getenv(AWS_ACCESS_KEY_ID_ENV_KEY, )
19:             __secret_access_key = os.getenv(AWS_SECRET_ACCESS_KEY_ENV_KEY, )
20:             if __access_key_id is None:
21:                 raise Exception(f"Environment variable: {AWS_ACCESS_KEY_ID_ENV_KEY} is not not set.")
22:             if __secret_access_key is None:
23:                 raise Exception(f"Environment variable: {AWS_SECRET_ACCESS_KEY_ENV_KEY} is not set.")
24:         
25:             # Set connection and read timeouts to 5 seconds to prevent long hangs on S3 requests
26:             timeout_config = Config(
27:                 connect_timeout=5,
28:                 read_timeout=5,
29:                 retries={'max_attempts': 2}
30:             )
31: 
32:             S3Client.s3_resource = boto3.resource('s3',
33:                                             aws_access_key_id=__access_key_id,
34:                                             aws_secret_access_key=__secret_access_key,
35:                                             region_name=region_name,
36:                                             config=timeout_config
37:                                             )
38:             S3Client.s3_client = boto3.client('s3',
39:                                         aws_access_key_id=__access_key_id,
40:                                         aws_secret_access_key=__secret_access_key,
41:                                         region_name=region_name,
42:                                         config=timeout_config
43:                                         )
44:         self.s3_resource = S3Client.s3_resource
45:         self.s3_client = S3Client.s3_client
```

*   **Line-by-Line Explanation**:
    *   `Line 1`: Imports `boto3`, the official AWS Software Development Kit (SDK) for Python.
    *   `Line 3`: Imports `Config` from `botocore.config` to configure client timeout and retry options.
    *   `Line 7`: Declares class `S3Client`.
    *   `Line 9-10`: Declares class-level attributes `s3_client` and `s3_resource` initialized as `None`. This implements a Singleton-like caching pattern.
    *   `Line 11`: Defines constructor accepting the region name (defaults to `us-east-1`).
    *   `Line 17`: Checks if either class-level connection is `None`. If already instantiated, the constructor skips connecting again and immediately loads cached objects on lines 44-45.
    *   `Line 18-19`: Fetches credentials from environment variables using `os.getenv()`.
    *   `Line 20-23`: Checks if credentials exist; if missing, throws a generic `Exception`.
    *   `Line 26-30`: Instantiates a `Config` object specifying a 5-second connection timeout, a 5-second read timeout, and a limit of 2 retry attempts. This prevents the server from hanging indefinitely if AWS S3 is unreachable.
    *   `Line 32-37`: Calls `boto3.resource('s3', ...)` to create a high-level, object-oriented connection resource and saves it to class-level `S3Client.s3_resource`.
    *   `Line 38-43`: Calls `boto3.client('s3', ...)` to create a low-level service client and saves it to class-level `S3Client.s3_client`.
    *   `Line 44-45`: Assigns the class-level cached variables to the instance variables `self.s3_resource` and `self.s3_client`.
*   **Syntax/OOP/Library Concepts**: Double leading underscore (e.g. `__access_key_id`) denotes local private scope within the constructor method. Class attributes (`S3Client.s3_resource`) persist across multiple instances of the class.
*   **Interview Questions**:
    *   *What is the difference between boto3.client and boto3.resource?* `boto3.client` is a low-level service interface that maps 1-to-1 with the AWS S3 HTTP API. `boto3.resource` is a high-level, object-oriented wrapper built on top of clients, exposing resource identifiers and sub-resources.

---

# File 2: [src/configuration/mongo\_db\_connection.py](file:///c:/Projects/Vehicle-Insurance/src/configuration/mongo_db_connection.py)

*   **Purpose**: Establishes a TLS-validated connection to MongoDB Atlas.
*   **Why it exists**: Provides access to the vehicle dataset stored in Atlas cluster collections.
*   **Why it is needed**: The training pipeline relies on this connector to query and extract data during the ingestion phase.
*   **Who imports/calls it**: Imported by the `Proj1Data` class (data access layer).
*   **Dependencies**: `os`, `sys`, `pymongo`, `certifi`, `dotenv.load_dotenv`, `src.exception.MyException`.

## Line-by-Line Walkthrough

### Code Block 1: Setup and Client Initialization (Lines 1-69)
```python
1: import os
2: import sys
3: import pymongo
4: import certifi
5: from dotenv import load_dotenv
6: 
7: load_dotenv()
8: 
9: from src.exception import MyException
10: from src.logger import logging
11: from src.constants import DATABASE_NAME , MONGODB_URL_KEY
12: 
13: # MONGODB_URL_KEY = "MONGODB_URL" 
14: 
15: # Load the certificate authority file to avoid timeout errors when connecting to MongoDB
16: ca = certifi.where()
17: 
18: class MongoDBClient:
19:     """
20:     MongoDBClient is responsible for establishing a connection to the MongoDB database.
21:     """
22: 
23:     client = None  # Shared MongoClient instance across all MongoDBClient instances
24: 
25:     def __init__(self, database_name: str = DATABASE_NAME) -> None:
26:         try:
27:             # Check if a MongoDB client connection has already been established; if not, create a new one
28:             if MongoDBClient.client is None:
29:                 mongo_db_url = os.getenv(MONGODB_URL_KEY)  # Retrieve MongoDB URL from environment variables
30:                 if mongo_db_url is None:
31:                     raise Exception(f"Environment variable '{MONGODB_URL_KEY}' is not set.")
32:                 
33:                 # Establish a new MongoDB client connection
34:                 MongoDBClient.client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)
35:                 
36:             # Use the shared MongoClient for this instance
37:             self.client = MongoDBClient.client
38:             self.database = self.client[database_name]  # Connect to the specified database
39:             self.database_name = database_name
40:             logging.info("MongoDB connection successful.")
41:             
42:         except Exception as e:
43:             # Raise a custom exception with traceback details if connection fails
44:             raise MyException(e, sys)
```

*   **Line-by-Line Explanation**:
    *   `Line 3`: Imports `pymongo`, the Python driver for MongoDB.
    *   `Line 4`: Imports `certifi`, which provides Mozilla's root certificates.
    *   `Line 5`: Imports `load_dotenv` from `dotenv` to load environment variables from a local `.env` file.
    *   `Line 7`: Invokes `load_dotenv()`. This parses any `.env` file in the project folder and adds the variables to `os.environ`.
    *   `Line 16`: Calls `certifi.where()` to get the absolute path to the local root certificates bundle. This is assigned to `ca` and passed to the driver to prevent SSL/TLS handshake failures.
    *   `Line 23`: Declares a class-level variable `client = None` to store a cached client.
    *   `Line 25`: Declares constructor, accepting a custom database name (defaults to `Proj1` constant).
    *   `Line 28`: Checks if `MongoDBClient.client` is `None` to implement caching.
    *   `Line 29`: Fetches the connection URL from environment variables using the key `MONGODB_URL`.
    *   `Line 30-31`: If missing, raises an exception.
    *   `Line 34`: Instantiates a `pymongo.MongoClient` with the database URL, passing the root certificate bundle path to the `tlsCAFile` parameter for SSL verification.
    *   `Line 37-38`: Sets `self.client` to the cached connection, and accesses the database using dict-style indexing `self.client[database_name]`.
    *   `Line 40`: Logs success.
    *   `Line 44`: Catches any connection failure and wraps it inside a `MyException` object.
*   **Interview Questions**:
    *   *Why pass tlsCAFile=certifi.where() to MongoClient?* MongoDB Atlas clusters require TLS encryption. If the Python environment cannot verify Atlas's SSL certificate using standard system directories, connection handshakes will fail. `certifi` provides a reliable, updated bundle of root certificates.

---

# File 3: [src/cloud\_storage/aws\_storage.py](file:///c:/Projects/Vehicle-Insurance/src/cloud_storage/aws_storage.py)

*   **Purpose**: Exposes utility functions for S3 storage interactions.
*   **Why it exists**: Simplifies file operations (exist checks, folder creation, CSV reading, model pickling, and file uploads).
*   **Who imports/calls it**: Used by the `Proj1Estimator` class (model loader), model evaluation stage, and model pusher stage.
*   **Dependencies**: `boto3`, `pandas`, `pickle`, `src.configuration.aws_connection.S3Client`, `src.exception.MyException`, `src.logger`.

## Line-by-Line Walkthrough

### Code Block 1: Class Definition & S3 Read Methods (Lines 15-74)
```python
15: class SimpleStorageService:
16:     """
17:     A class for interacting with AWS S3 storage, providing methods for file management...
18:     """
19:     def __init__(self):
20:         s3_client = S3Client()
21:         self.s3_resource = s3_client.s3_resource
22:         self.s3_client = s3_client.s3_client
23: 
24:     def s3_key_path_available(self, bucket_name, s3_key) -> bool:
25:         try:
26:             bucket = self.get_bucket(bucket_name)
27:             file_objects = [file_object for file_object in bucket.objects.filter(Prefix=s3_key)]
28:             return len(file_objects) > 0
29:         except Exception as e:
30:             raise MyException(e, sys)
31: 
32:     @staticmethod
33:     def read_object(object_name: str, decode: bool = True, make_readable: bool = False) -> Union[StringIO, str]:
34:         try:
35:             func = (
36:                 lambda: object_name.get()["Body"].read().decode()
37:                 if decode else object_name.get()["Body"].read()
38:             )
39:             conv_func = lambda: StringIO(func()) if make_readable else func()
40:             return conv_func()
41:         except Exception as e:
42:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 19`: Constructor initializes connection by instantiating the cached `S3Client()`.
    *   `Line 24`: Declares `s3_key_path_available()`. Checks if a file path (key) exists in a bucket.
    *   `Line 26`: Gets the bucket resource.
    *   `Line 27`: Filters bucket objects matching the prefix `s3_key`. If the returned list size is greater than 0, the path exists.
    *   `Line 32`: Declares static method `read_object()`.
    *   `Line 35-38`: Declares lambda `func` that retrieves the S3 object data stream via `.get()["Body"]`, reads the bytes, and decodes them to a string if `decode=True`.
    *   `Line 39`: Declares lambda `conv_func` that wraps string output inside a `StringIO` stream if `make_readable=True` (allowing it to be read by `pd.read_csv`).
    *   `Line 40`: Invokes and returns the result of `conv_func()`.

---

### Code Block 2: Bucket & Model Loaders (Lines 75-138)
```python
75:     def get_bucket(self, bucket_name: str) -> Bucket:
76:         try:
77:             bucket = self.s3_resource.Bucket(bucket_name)
78:             return bucket
79:         except Exception as e:
80:             raise MyException(e, sys) from e
81: 
82:     def get_file_object(self, filename: str, bucket_name: str) -> Union[List[object], object]:
83:         try:
84:             bucket = self.get_bucket(bucket_name)
85:             file_objects = [file_object for file_object in bucket.objects.filter(Prefix=filename)]
86:             func = lambda x: x[0] if len(x) == 1 else x
87:             file_objs = func(file_objects)
88:             return file_objs
89:         except Exception as e:
90:             raise MyException(e, sys) from e
91: 
92:     def load_model(self, model_name: str, bucket_name: str, model_dir: str = None) -> object:
93:         try:
94:             model_file = model_dir + "/" + model_name if model_dir else model_name
95:             file_object = self.get_file_object(model_file, bucket_name)
96:             model_obj = self.read_object(file_object, decode=False)
97:             model = pickle.loads(model_obj)
98:             return model
99:         except Exception as e:
100:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 77`: Calls `self.s3_resource.Bucket(bucket_name)` to get a Bucket resource instance.
    *   `Line 82`: Declares `get_file_object()`.
    *   `Line 85`: Queries objects matching `Prefix=filename`.
    *   `Line 86-87`: Declares a lambda that returns the first object if only one exists, or the entire list otherwise.
    *   `Line 92`: Declares `load_model()`.
    *   `Line 94`: Builds the model S3 path string.
    *   `Line 95`: Retrieves the S3 target file object.
    *   `Line 96`: Reads the binary stream by passing `decode=False` to `read_object()`.
    *   `Line 97`: De-serializes the binary stream using `pickle.loads()` to restore the original Python model object in memory.

---

### Code Block 3: Write, Upload & DataFrame Integrations (Lines 139-238)
```python
139:     def create_folder(self, folder_name: str, bucket_name: str) -> None:
140:         try:
141:             self.s3_resource.Object(bucket_name, folder_name).load()
142:         except ClientError as e:
143:             if e.response["Error"]["Code"] == "404":
144:                 folder_obj = folder_name + "/"
145:                 self.s3_client.put_object(Bucket=bucket_name, Key=folder_obj)
146: 
147:     def upload_file(self, from_filename: str, to_filename: str, bucket_name: str, remove: bool = True):
148:         try:
149:             self.s3_resource.meta.client.upload_file(from_filename, bucket_name, to_filename)
150:             if remove:
151:                 os.remove(from_filename)
152:         except Exception as e:
153:             raise MyException(e, sys) from e
154: 
155:     def upload_df_as_csv(self, data_frame: DataFrame, local_filename: str, bucket_filename: str, bucket_name: str) -> None:
156:         try:
157:             data_frame.to_csv(local_filename, index=None, header=True)
158:             self.upload_file(local_filename, bucket_filename, bucket_name)
159:         except Exception as e:
160:             raise MyException(e, sys) from e
161: 
162:     def get_df_from_object(self, object_: object) -> DataFrame:
163:         try:
164:             content = self.read_object(object_, make_readable=True)
165:             df = read_csv(content, na_values="na")
166:             return df
167:         except Exception as e:
168:             raise MyException(e, sys) from e
169: 
170:     def read_csv(self, filename: str, bucket_name: str) -> DataFrame:
171:         try:
172:             csv_obj = self.get_file_object(filename, bucket_name)
173:             df = self.get_df_from_object(csv_obj)
174:             return df
175:         except Exception as e:
176:             raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 139`: Declares `create_folder()`. In S3, directories are logical structures defined by trailing slashes in key names.
    *   `Line 141`: Checks if the path already exists by calling `.load()`.
    *   `Line 142-143`: If S3 throws a `ClientError` with code `404` (Not Found), it proceeds to create the folder.
    *   `Line 144-145`: Appends a trailing slash and calls `.put_object()` to create the directory prefix.
    *   `Line 147`: Declares `upload_file()`.
    *   `Line 149`: Uploads the local file using `self.s3_resource.meta.client.upload_file()`.
    *   `Line 150-151`: If `remove=True`, deletes the local source file using `os.remove()` after upload completes.
    *   `Line 155`: Declares `upload_df_as_csv()`.
    *   `Line 157-158`: Saves the pandas DataFrame locally as a CSV, then uploads it to the bucket.
    *   `Line 162`: Declares `get_df_from_object()`.
    *   `Line 164`: Reads the S3 object data stream using `make_readable=True`.
    *   `Line 165`: Parses the stream into a pandas DataFrame using `pd.read_csv`, converting string `"na"` to `NaN` values.
    *   `Line 170`: Declares `read_csv()`, wrapping key lookup and DataFrame conversion.
