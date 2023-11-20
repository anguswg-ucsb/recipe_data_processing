import os
from dotenv import load_dotenv
import ast

BASE_DIR = os.path.abspath(os.path.dirname(__name__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Config:

    # Base directory and path configurations
    BASE_DIR_NAME = "recipes_out"
    BASE_DIR_PATH = os.getenv("BASE_DIR_PATH")

    # Define paths for raw, processed, and output directories
    BASE_DIR = os.path.join(BASE_DIR_PATH, BASE_DIR_NAME)
    RAW_DIR = os.path.join(BASE_DIR, "raw")
    PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")

    # Create a list of directories to check and create
    directories = [BASE_DIR, RAW_DIR, PROCESSED_DIR, OUTPUT_DIR]

    # Loop through the list of directories and create them if they don't exist
    for directory in directories:
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




