import os
import glob
from src.cloud_storage.aws_storage import SimpleStorageService
from src.exception import MyException
from src.entity.estimator import MyModel
from src.utils.main_utils import load_object, save_object
import sys
from pandas import DataFrame


class Proj1Estimator:
    """
    This class is used to save and retrieve our model from s3 bucket and to do prediction
    """

    def __init__(self,bucket_name,model_path,):
        """
        :param bucket_name: Name of your model bucket
        :param model_path: Location of your model in bucket
        """
        self.bucket_name = bucket_name
        self.s3 = SimpleStorageService()
        self.model_path = model_path
        self.loaded_model:MyModel=None


    def is_model_present(self,model_path):
        try:
            return self.s3.s3_key_path_available(bucket_name=self.bucket_name, s3_key=model_path)
        except MyException as e:
            print(e)
            return False

    def load_model(self,)->MyModel:
        """
        Load the model from the model_path
        :return:
        """
        local_model_path = os.path.join("model", "model.pkl")

        # 1. Try to load from standard local path 'model/model.pkl'
        if os.path.exists(local_model_path):
            try:
                print(f"Loading model from local path: {local_model_path}")
                return load_object(local_model_path)
            except Exception as e:
                print(f"Failed to load model from local path {local_model_path}: {e}. Falling back...")

        # 2. Try to find the latest trained model in the artifact directory
        if os.path.exists("artifact"):
            model_paths = glob.glob(os.path.join("artifact", "*", "model_trainer", "trained_model", "model.pkl"))
            if model_paths:
                # Sort by modification time to get the latest trained model
                model_paths.sort(key=os.path.getmtime, reverse=True)
                latest_model_path = model_paths[0]
                try:
                    print(f"Loading model from latest artifact path: {latest_model_path}")
                    return load_object(latest_model_path)
                except Exception as e:
                    print(f"Failed to load model from artifact path {latest_model_path}: {e}. Falling back...")

        # 3. Fallback: Download the model from S3 and cache it locally
        print("Model not found locally. Fetching model from S3...")
        model = self.s3.load_model(self.model_path, bucket_name=self.bucket_name)

        # Cache downloaded model locally for fast subsequent loads
        try:
            os.makedirs(os.path.dirname(local_model_path), exist_ok=True)
            save_object(local_model_path, model)
            print(f"Successfully cached downloaded model locally at {local_model_path}")
        except Exception as e:
            print(f"Failed to cache model locally: {e}")

        return model

    def save_model(self,from_file,remove:bool=False)->None:
        """
        Save the model to the model_path
        :param from_file: Your local system model path
        :param remove: By default it is false that mean you will have your model locally available in your system folder
        :return:
        """
        try:
            self.s3.upload_file(from_file,
                                to_filename=self.model_path,
                                bucket_name=self.bucket_name,
                                remove=remove
                                )
        except Exception as e:
            raise MyException(e, sys)


    def predict(self,dataframe:DataFrame):
        """
        :param dataframe:
        :return:
        """
        try:
            if self.loaded_model is None:
                self.loaded_model = self.load_model()
            return self.loaded_model.predict(dataframe=dataframe)
        except Exception as e:
            raise MyException(e, sys)