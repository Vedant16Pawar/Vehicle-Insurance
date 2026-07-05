# Source Code: Infrastructure & Core Utilities

This section details the core system files responsible for configuration management, logger setup, traceback diagnostics, and basic file serialization.

---

# File 1: [src/logger/\_\_init\_\_.py](file:///c:/Projects/Vehicle-Insurance/src/logger/__init__.py)

*   **Purpose**: Sets up rotating file logging and console logging.
*   **Why it exists**: Provides tracing details of database pipelines, validation checks, and exceptions in a production environment.
*   **Why it is needed**: Standardizes the logging system across all components so logs can be written to both local files (for debugging) and terminal streams (for container execution tracing).
*   **When it executes**: Instantly when the `src.logger` package is imported by any module (module-level auto-execution).
*   **Who imports/calls it**: Imported by every pipeline component, exception handling module, database connector, and FastAPI route.
*   **Dependencies**: `logging`, `os`, `from_root`, `datetime`, `logging.handlers.RotatingFileHandler`.
*   **Execution flow**:
    1.  Calculates root directory using `from_root()`.
    2.  Creates the `logs/` folder if missing.
    3.  Generates a dynamic filename with a timestamp.
    4.  Initializes a RotatingFileHandler (limits size to 5MB, keeps 3 backups).
    5.  Initializes a StreamHandler (writes to console).
    6.  Attaches handlers to the root logger.
*   **Input**: None.
*   **Output**: Side effect (Configures the global Python root logger).

## Line-by-Line Walkthrough

### Code Block 1: Imports and Constants Setup (Lines 1-11)
```python
1: import logging
2: import os
3: from logging.handlers import RotatingFileHandler
4: from from_root import from_root
5: from datetime import datetime
6: 
7: # Constants for log configuration
8: LOG_DIR = 'logs'
9: LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
10: MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
11: BACKUP_COUNT = 3  # Number of backup log files to keep
```

*   **Line-by-Line Explanation**:
    *   `Line 1`: Imports the standard Python `logging` module. This module provides a flexible framework for generating log messages.
    *   `Line 2`: Imports the standard `os` module for interacting with the operating system filesystem.
    *   `Line 3`: Imports `RotatingFileHandler` from standard library `logging.handlers`. This handler allows log files to rotate when they reach a certain size, preventing disk storage depletion.
    *   `Line 4`: Imports `from_root` from the third-party package `from_root`. This function determines the absolute path of the project's root folder, preventing relative import path errors when running scripts from different directories.
    *   `Line 5`: Imports `datetime` from the standard `datetime` package to retrieve system timestamps.
    *   `Line 8`: Defines the target directory name `'logs'` where log files are stored.
    *   `Line 9`: Declares `LOG_FILE` dynamically using `datetime.now().strftime(...)` to generate a unique filename representing the start time of execution (e.g., `07_05_2026_14_37_47.log`).
    *   `Line 10`: Declares `MAX_LOG_SIZE` as `5242880` bytes (5 MB), the size threshold at which rotation is triggered.
    *   `Line 11`: Declares `BACKUP_COUNT` as `3`. When the current log file exceeds 5MB, it is renamed (e.g., `<name>.log.1`), and a new file is opened. Up to 3 backup files are kept; older files are deleted automatically.
*   **Syntax/OOP/Library Concepts**: String interpolation (`f-string`) is used to inject the date format.
*   **Runtime & Memory Behavior**: Modest memory usage. Variable strings are initialized once during module loading.
*   **Interview Questions**:
    *   *Why use a RotatingFileHandler instead of standard file writing?* It prevents the log file from growing indefinitely and consuming all disk space on the server.

---

### Code Block 2: File Paths and Logger Setup (Lines 13-28)
```python
13: # Construct log file path
14: log_dir_path = os.path.join(from_root(), LOG_DIR)
15: os.makedirs(log_dir_path, exist_ok=True)
16: log_file_path = os.path.join(log_dir_path, LOG_FILE)
17: 
18: def configure_logger():
19:     """
20:     Configures logging with a rotating file handler and a console handler.
21:     """
22:     # Create a custom logger
23:     logger = logging.getLogger()
24:     logger.setLevel(logging.DEBUG)
25:     
26:     # Define formatter
27:     formatter = logging.Formatter("[ %(asctime)s ] %(name)s - %(levelname)s - %(message)s")
```

*   **Line-by-Line Explanation**:
    *   `Line 14`: Joins the absolute project root path and the `'logs'` folder name to generate the absolute path `log_dir_path`.
    *   `Line 15`: Calls `os.makedirs()` to recursively create the logs folder if it does not exist. The parameter `exist_ok=True` prevents a `FileExistsError` if the directory already exists.
    *   `Line 16`: Joins `log_dir_path` and `LOG_FILE` to build the full file path.
    *   `Line 18`: Defines `configure_logger()` to wrap the setup logic.
    *   `Line 23`: Calls `logging.getLogger()` without arguments. This retrieves the **Root Logger** (a singleton object). Config changes made to this logger apply globally to all loggers in the runtime process.
    *   `Line 24`: Sets the root logger threshold level to `logging.DEBUG`. This ensures that all events (DEBUG, INFO, WARNING, ERROR, CRITICAL) are processed and passed to the individual handlers.
    *   `Line 27`: Instantiates a `logging.Formatter` specifying the log layout: timestamp, logger name, level, and the log message.
*   **Syntax/OOP/Library Concepts**: Singleton design pattern is used by Python's logging library (`getLogger()`).
*   **Runtime & Memory Behavior**: Disk I/O occurs if `os.makedirs` needs to create the directory. The formatter object is initialized in heap memory.
*   **Alternatives**: Python standard logging can be configured using a `logging.config.dictConfig` or JSON configuration file.

---

### Code Block 3: Registering Handlers (Lines 29-44)
```python
29:     # File handler with rotation
30:     file_handler = RotatingFileHandler(log_file_path, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
31:     file_handler.setFormatter(formatter)
32:     file_handler.setLevel(logging.DEBUG)
33:     
34:     # Console handler
35:     console_handler = logging.StreamHandler()
36:     console_handler.setFormatter(formatter)
37:     console_handler.setLevel(logging.INFO)
38:     
39:     # Add handlers to the logger
40:     logger.addHandler(file_handler)
41:     logger.addHandler(console_handler)
42: 
43: # Configure the logger
44: configure_logger()
```

*   **Line-by-Line Explanation**:
    *   `Line 30`: Instantiates `RotatingFileHandler` with the log path, max size, and backup count.
    *   `Line 31`: Assigns our custom formatter to the file handler.
    *   `Line 32`: Sets the file handler's logging level to `logging.DEBUG` to capture every detail.
    *   `Line 35`: Instantiates a `StreamHandler`, which writes log events to `sys.stderr` by default (console stream).
    *   `Line 36`: Assigns our custom formatter to the console handler.
    *   `Line 37`: Sets the console handler's logging level to `logging.INFO`. This filters out verbose `DEBUG` logs from standard stdout streams while keeping them in the file logs.
    *   `Line 40`: Adds `file_handler` to the root logger.
    *   `Line 41`: Adds `console_handler` to the root logger.
    *   `Line 44`: Calls `configure_logger()` immediately at the module level.
*   **Runtime & Memory Behavior**: When another file imports `logging` or `from src.logger import logging`, this block executes instantly, setting up the global logging environment. The root logger holds references to these handlers in its internal `handlers` list.

---

# File 2: [src/exception/\_\_init\_\_.py](file:///c:/Projects/Vehicle-Insurance/src/exception/__init__.py)

*   **Purpose**: Implements custom exception parsing and exception logging.
*   **Why it exists**: Native tracebacks can be lengthy and hard to read in system log outputs. This captures exact file names and line numbers where errors occur.
*   **Why it is needed**: Standardizes error handling and ensures every exception raised automatically writes an error log detail to the rotating file handler.
*   **When it executes**: When a custom exception `MyException` is initialized.
*   **Who imports/calls it**: Imported by every module that raises exceptions inside `try-except` blocks.
*   **Dependencies**: `sys`, `logging`.
*   **Execution flow**:
    1.  Extracts execution traceback info via `sys.exc_info()`.
    2.  Extracts the exact filename and line number from the traceback object.
    3.  Formats a clean diagnostic string.
    4.  Logs the message to `logging.error`.
    5.  Sets the message string as the exception's core text.

## Line-by-Line Walkthrough

### Code Block 1: Error Formatting Function (Lines 1-25)
```python
1: import sys
2: import logging
3: 
4: def error_message_detail(error: Exception, error_detail: sys) -> str:
5:     """
6:     Extracts detailed error information including file name, line number, and the error message.
7:     """
8:     # Extract traceback details (exception information)
9:     _, _, exc_tb = error_detail.exc_info()
10: 
11:     # Get the file name where the exception occurred
12:     file_name = exc_tb.tb_frame.f_code.co_filename
13: 
14:     # Create a formatted error message string with file name, line number, and the actual error
15:     line_number = exc_tb.tb_lineno
16:     error_message = f"Error occurred in python script: [{file_name}] at line number [{line_number}]: {str(error)}"
17:     
18:     # Log the error for better tracking
19:     logging.error(error_message)
20:     
21:     return error_message
```

*   **Line-by-Line Explanation**:
    *   `Line 1`: Imports Python standard `sys` module, used to read system variables and stack frames.
    *   `Line 2`: Imports `logging` to log the diagnostic trace immediately.
    *   `Line 4`: Defines `error_message_detail()`. It takes the error object and the `sys` module as parameters.
    *   `Line 9`: Calls `sys.exc_info()`. It returns a tuple of three values: `(type, value, traceback)`. We discard the first two using dummy variables `_` and unpack the traceback object as `exc_tb`.
    *   `Line 12`: Navigates the stack frames in the traceback. `exc_tb.tb_frame` reaches the active frame object, `f_code` refers to the code object being executed, and `co_filename` pulls the absolute file path.
    *   `Line 15`: Retrieves `tb_lineno` (the line number where the exception occurred).
    *   `Line 16`: Formats the error diagnostic string with file path, line number, and error details.
    *   `Line 19`: Triggers `logging.error(error_message)` to write the formatted error to logs immediately.
    *   `Line 21`: Returns the generated string.
*   **Syntax/OOP/Library Concepts**: Tuple unpacking is used: `_, _, exc_tb = error_detail.exc_info()`.
*   **Runtime & Memory Behavior**: Accessing frame metadata has minor overhead because frames are managed on the Python interpreter stack.
*   **Alternatives**: The standard `traceback` library offers `traceback.format_exc()` which generates complete text tracebacks. However, our custom function produces a concise single-line log entry.

---

### Code Block 2: Custom Exception Class (Lines 27-48)
```python
27: class MyException(Exception):
28:     """
29:     Custom exception class for handling errors in the US visa application.
30:     """
31:     def __init__(self, error_message: str, error_detail: sys):
32:         """
33:         Initializes the USvisaException with a detailed error message.
34:         """
35:         # Call the base class constructor with the error message
36:         super().__init__(error_message)
37: 
38:         # Format the detailed error message using the error_message_detail function
39:         self.error_message = error_message_detail(error_message, error_detail)
40: 
41:     def __str__(self) -> str:
42:         """
43:         Returns the string representation of the error message.
44:         """
45:         return self.error_message
```

*   **Line-by-Line Explanation**:
    *   `Line 27`: Declares class `MyException` inheriting from the built-in base `Exception`.
    *   `Line 31`: The constructor `__init__` accepts `error_message` (string or exception) and `error_detail` (the `sys` module).
    *   `Line 36`: Calls `super().__init__(error_message)`. This passes the core error message to the parent `Exception` class.
    *   `Line 39`: Calls `error_message_detail()` to construct and log the detailed diagnostic string, saving it to `self.error_message`.
    *   `Line 41`: Implements the magic method `__str__` to customize string conversion behavior (e.g., when running `print(e)` or `str(e)`).
    *   `Line 45`: Returns the detailed formatted message string.
*   **Interview Questions**:
    *   *Why inherit from standard Exception?* It guarantees that the custom exception can be caught by generic `except Exception as e` blocks and behaves correctly within Python's built-in error propagation mechanisms.
    *   *What does sys.exc_info() return?* It returns a tuple of `(exception_type, exception_value, exception_traceback)` representing the exception currently being handled.

---

# File 3: [src/utils/main\_utils.py](file:///c:/Projects/Vehicle-Insurance/src/utils/main_utils.py)

*   **Purpose**: Helper functions to read/write YAML, and load/save serialized files (using `dill` and `numpy`).
*   **Why it exists**: Isolates file I/O operations from business logic.
*   **Why it is needed**: Reduces code duplication across components. For example, both model training and evaluation require loading objects, and both validation and transformation read configuration YAML files.
*   **Who imports/calls it**: Called by data validation, data transformation, model trainer, model evaluation, and estimator classes.
*   **Dependencies**: `os`, `sys`, `numpy`, `dill`, `yaml`, `src.logger`, `src.exception.MyException`.

## Line-by-Line Walkthrough

### Code Block 1: YAML Handling (Lines 1-32)
```python
1: import os
2: import sys
3: 
4: import numpy as np
5: import dill
6: import yaml
7: from pandas import DataFrame
8: 
9: from src.exception import MyException
10: from src.logger import logging
11: 
12: 
13: def read_yaml_file(file_path: str) -> dict:
14:     try:
15:         with open(file_path, "rb") as yaml_file:
16:             return yaml.safe_load(yaml_file)
17: 
18:     except Exception as e:
19:         raise MyException(e, sys) from e
20: 
21: 
22: def write_yaml_file(file_path: str, content: object, replace: bool = False) -> None:
23:     try:
24:         if replace:
25:             if os.path.exists(file_path):
26:                 os.remove(file_path)
27:         os.makedirs(os.path.dirname(file_path), exist_ok=True)
28:         with open(file_path, "w") as file:
29:             yaml.dump(content, file)
30:     except Exception as e:
31:         raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 1-7`: Imports external modules. `dill` is imported for enhanced object serialization. `yaml` is imported to parse YAML configurations.
    *   `Line 13`: Declares `read_yaml_file()`.
    *   `Line 15`: Opens the YAML file in binary read mode (`"rb"`). Using binary mode ensures compatibility across different operating systems.
    *   `Line 16`: Calls `yaml.safe_load()` to parse the file into a Python dictionary. `safe_load` prevents code execution vulnerabilities during YAML loading.
    *   `Line 22`: Declares `write_yaml_file()`.
    *   `Line 24-26`: If `replace=True` and the file exists, it deletes the file using `os.remove()`.
    *   `Line 27`: Extracts the directory portion of the path using `os.path.dirname()` and creates it recursively using `os.makedirs()`.
    *   `Line 28`: Opens the path in write mode (`"w"`).
    *   `Line 29`: Calls `yaml.dump()` to serialize the Python object into YAML syntax in the file.
*   **Syntax/OOP/Library Concepts**: `with` statement acts as a context manager, ensuring the file descriptor is closed automatically even if errors occur inside the block.
*   **Interview Questions**:
    *   *Why use safe_load instead of load in PyYAML?* `yaml.load` can instantiate arbitrary Python objects, leaving the app open to code injection attacks. `safe_load` limits parsing to standard types (lists, dicts, strings, numbers).

---

### Code Block 2: dill Object Serialization (Lines 34-45 & 75-87)
```python
34: def load_object(file_path: str) -> object:
35:     """
36:     Returns model/object from project directory.
37:     """
38:     try:
39:         with open(file_path, "rb") as file_obj:
40:             obj = dill.load(file_obj)
41:         return obj
42:     except Exception as e:
43:         raise MyException(e, sys) from e

75: def save_object(file_path: str, obj: object) -> None:
76:     logging.info("Entered the save_object method of utils")
77:     try:
78:         os.makedirs(os.path.dirname(file_path), exist_ok=True)
79:         with open(file_path, "wb") as file_obj:
80:             dill.dump(obj, file_obj)
81:         logging.info("Exited the save_object method of utils")
82:     except Exception as e:
83:         raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 34`: Declares `load_object()` to load serialized Python objects.
    *   `Line 39`: Opens the target file path in binary read mode (`"rb"`).
    *   `Line 40`: Calls `dill.load()` to parse the binary file back into a live Python object in heap memory.
    *   `Line 75`: Declares `save_object()`.
    *   `Line 78`: Ensures the target directory exists.
    *   `Line 79`: Opens the file in binary write mode (`"wb"`).
    *   `Line 80`: Serializes the Python object using `dill.dump()`.
*   **Syntax/OOP/Library Concepts**: `dill` is an extension of Python's standard `pickle` module. It can serialize lambda functions, nested classes, and complete Machine Learning preprocessing pipelines that standard `pickle` struggles with.
*   **Runtime & Memory Behavior**: De-serializing transfers binary state from disk into live objects in RAM.
*   **Interview Questions**:
    *   *What is the difference between pickle and dill?* `pickle` cannot serialize complex code constructs like lambdas or dynamically defined methods. `dill` supports serializing almost any Python object type.

---

### Code Block 3: NumPy Array Serialization (Lines 47-72)
```python
47: def save_numpy_array_data(file_path: str, array: np.array):
48:     """
49:     Save numpy array data to file
50:     """
51:     try:
52:         dir_path = os.path.dirname(file_path)
53:         os.makedirs(dir_path, exist_ok=True)
54:         with open(file_path, 'wb') as file_obj:
55:             np.save(file_obj, array)
56:     except Exception as e:
57:         raise MyException(e, sys) from e
58: 
59: 
60: def load_numpy_array_data(file_path: str) -> np.array:
61:     """
62:     load numpy array data from file
63:     """
64:     try:
65:         with open(file_path, 'rb') as file_obj:
66:             return np.load(file_obj)
67:     except Exception as e:
68:         raise MyException(e, sys) from e
```

*   **Line-by-Line Explanation**:
    *   `Line 47`: Declares `save_numpy_array_data()`.
    *   `Line 52-53`: Ensures parent directories are created.
    *   `Line 54`: Opens target path in binary write mode (`"wb"`).
    *   `Line 55`: Calls `np.save()` to serialize the numpy array.
    *   `Line 60`: Declares `load_numpy_array_data()`.
    *   `Line 65`: Opens array file in binary read mode (`"rb"`).
    *   `Line 66`: Calls `np.load()` to parse the binary format back into a NumPy array object.
*   **Runtime & Memory Behavior**: NumPy `.npy` format is highly optimized. It uses a clean binary structure that maps directly to memory arrays, allowing fast read and write operations.
