import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__name__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Config:

    # General Config
    S3_BUCKET  = os.environ.get("S3_BUCKET")
    OUTPUT_S3_BUCKET  = os.environ.get("OUTPUT_S3_BUCKET")
    SCRAPE_OPS_API_KEY  = os.environ.get("SCRAPE_OPS_API_KEY")
    
    # Bright Data credentials
    BRIGHT_DATA_HOST = os.getenv("BRIGHT_DATA_HOST")
    BRIGHT_DATA_PORT = os.getenv("BRIGHT_DATA_PORT")
    BRIGHT_DATA_USERNAME = os.getenv("BRIGHT_DATA_USERNAME")
    BRIGHT_DATA_PASSWORD = os.getenv("BRIGHT_DATA_PASSWORD")