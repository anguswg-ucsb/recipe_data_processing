import os
from dotenv import load_dotenv
import ast

BASE_DIR = os.path.abspath(os.path.dirname(__name__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Config:

    # OpenAPI API Key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # URI of S3 bucket to put raw data into
    RAW_S3_URI = os.getenv("RAW_S3_URI")

    # Bright Data credentials
    BRIGHT_DATA_HOST = os.getenv("BRIGHT_DATA_HOST")
    BRIGHT_DATA_PORT = os.getenv("BRIGHT_DATA_PORT")
    BRIGHT_DATA_USERNAME = os.getenv("BRIGHT_DATA_USERNAME")
    BRIGHT_DATA_PASSWORD = os.getenv("BRIGHT_DATA_PASSWORD")

    # NordVPN credentials
    NORDVPN_USERNAME = os.getenv("NORDVPN_USERNAME")
    NORDVPN_PASSWORD = os.getenv("NORDVPN_PASSWORD")

    # Base directory and path configurations
    BASE_DIR_NAME = "recipes_out"
    BASE_DIR_PATH = os.getenv("BASE_DIR_PATH")
    
    # directory for json files
    JSON_DIR_NAME = "recipes_json"
    
    # Define paths for raw, processed, and output directories
    BASE_DIR = os.path.join(BASE_DIR_PATH, BASE_DIR_NAME)
    RAW_DIR = os.path.join(BASE_DIR, "raw")
    PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")

    # Define path for json directory
    JSON_DIR = os.path.join(BASE_DIR_PATH, JSON_DIR_NAME)

    # Create a list of directories to check and create
    directories = [BASE_DIR, RAW_DIR, PROCESSED_DIR, OUTPUT_DIR]

    # Loop through the list of directories and create them if they don't exist
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

            # Print directories, if created
            print(f"Directory created: {directory}")

    json_directory = [JSON_DIR]

    # Loop through the list of directories and create them if they don't exist
    for directory in json_directory:
        if not os.path.exists(directory):
            os.makedirs(directory)

            # Print directories, if created
            print(f"Directory created: {directory}")

    # Reprocess flag configuration
    REPROCESS_FLAG = ast.literal_eval(os.getenv("REPROCESS_FLAG"))

    # Print whether reprocessing is enabled or not
    if REPROCESS_FLAG:
        print("Reprocessing is enabled.")
    else:
        print("Reprocessing is not enabled.")




