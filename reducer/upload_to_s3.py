########################################################
########################################################

import os
import subprocess
import random
import time 

from config import Config

# Base directory for test JSONs
test_base_dir = os.path.join(Config.BASE_DIR_PATH, "recipes_json")

# URI of S3 bucket to put raw data into
RAW_S3_URI = Config.RAW_S3_URI

# # list the files in the directory
filenames = os.listdir(test_base_dir)

file_paths = [os.path.join(test_base_dir, file) for file in filenames if os.path.isfile(os.path.join(test_base_dir, file)) and file != ".DS_Store"]
len(file_paths)

len(file_paths)
upload_files = file_paths[0:1000]


# json.load(file_paths[2])
# with open(file_paths[4], 'r') as file:
#     data = json.load(file)
# data
# final_list = []

# for file in file_paths:
#     if file not in to_drop:
#         final_list.append(file)
# len(final_list)

# file_paths = [file_paths[2], file_paths[5]]
random.shuffle(file_paths)

# file = file_paths[-1]
# file_paths = file_paths[:len(file_paths)-1]

for file in file_paths:
    print(f"file: {file}")

    sleep_time = random.randint(1, 3)

    print(f"Sleeping for {sleep_time} seconds...")
    time.sleep(sleep_time)

    subprocess.run(f"aws s3 cp {file} {RAW_S3_URI}", shell=True)
    # subprocess.process.call(f"aws s3 cp {test_base_dir}{file} s3://recipe-scrapers-jsons/", shell=True)

    print(f"===" * 10)