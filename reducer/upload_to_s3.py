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

# chunk the list of files into groups of 9
def chunk_list(input_list, chunk_size=9):
    result = []

    for i in range(0, len(input_list), chunk_size):
        group = input_list[i:i + chunk_size]
        result.append(group)

    return result

# subset the list of files to upload
upload_files = file_paths[0:18]
# upload_files = file_paths[9:18]
file_paths[18:]
# chunk the list of files into groups of 9
chunked_paths = chunk_list(upload_files)
[len(i) for i in chunked_paths]

# subdirectory = "/Users/anguswatters/Desktop/recipes_json/"

for i, chunk in enumerate(chunked_paths):
    print(f"i / len(chunked_paths): {i} / {len(chunked_paths)}")
    # print(f"chunk: {chunk}")
    print(f"len(chunk): {len(chunk)}")

    sleep_time = random.randint(3, 5)
    print(f"Sleeping for {sleep_time} seconds...")
    time.sleep(sleep_time)

    for path in chunk:
        # print(f"path: {path}")
        print(f"os.path.basename(path): {os.path.basename(path)}")
        
        s3_copy_cmd = f"aws s3 cp {path} {RAW_S3_URI}"
        print(f"S3 copy command: \n - '{s3_copy_cmd}'")

        # Run S3 copy command
        subprocess.run(s3_copy_cmd, shell=True)
        # print(f"===" * 5)


    # " --include ".join(chunk)
    
    # include_chunk = "".join([f' --include "{os.path.basename(i)}"' for i in chunk])

    # copy chunk of JSONs to S3
    # s3_copy_cmd = f"aws s3 cp {' '.join(chunk)} {RAW_S3_URI}"
    # s3_copy_cmd = f'aws s3 cp {subdirectory} {RAW_S3_URI} --recursive --exclude "*" {include_chunk}'
    # aws s3 cp yourSubFolder s3://mybucket/ --recursive --include "a*.txt" --include "b*.txt" --exclude="c*.txt" --exclude="d*.txt"
    # print(f"S3 copy command: \n - '{s3_copy_cmd}'")

    # # Run S3 copy command
    # subprocess.run(s3_copy_cmd, shell=True)
    # subprocess.run(f"aws s3 cp {' '.join(chunk)} {RAW_S3_URI}", shell=True)
    # aws s3 cp /Users/anguswatters/Desktop/recipes_json s3://recipes-raw-bucket/ --recursive --exclude "*"  --include "Users/anguswatters/Desktop/recipes_json/1144468_www_food_com*.json" --include "Users/anguswatters/Desktop/recipes_json/1633500_www_yummly_com*.json"
    print("===" * 10)

for chunk in chunked:
    for i in chunk:
        print(os.path.basename(i))
    print("===" * 10)

chunked[0]

5*9

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

########################################################
########################################################

import os
import subprocess
import random
import time 

from config import Config

# Base directory for test JSONs
chunked_dir = os.path.join(Config.BASE_DIR_PATH, "recipes_json_chunks")

# URI of S3 bucket to put raw data into
RAW_S3_URI = Config.RAW_S3_URI

# # list the files in the directory
chunked_subdirs = os.listdir(chunked_dir)

# list of subdirectories to recursively upload to S3 bucket
subdir_paths = [os.path.join(chunked_dir, subdir) for subdir in chunked_subdirs if os.path.isdir(os.path.join(chunked_dir, subdir)) and subdir != ".DS_Store"]
subdir_paths[999:1000]
subdir_paths[1005:1006]
len(subdir_paths)

# for subdir in subdir_paths[0:1000]:
for i, subdir in enumerate(subdir_paths[1005:100000]):
    print(f"i / len(subdir_paths): {i} / {len(subdir_paths)}")
    sleep_time = random.randint(1, 2)
    print(f"Sleeping for {sleep_time} seconds...")
    time.sleep(sleep_time)

    print(f"subdir: {subdir}")
    
    s3_copy_cmd = f"aws s3 cp {subdir} {RAW_S3_URI} --recursive"
    print(f"S3 copy command: \n - '{s3_copy_cmd}'")

    # Run S3 copy command
    subprocess.run(s3_copy_cmd, shell=True)

    print(f"===" * 5)



file_paths = [os.path.join(chunked_dir, file) for file in filenames if os.path.isfile(os.path.join(test_base_dir, file)) and file != ".DS_Store"]


len(file_paths)

# chunk the list of files into groups of 9
def chunk_list(input_list, chunk_size=9):
    result = []

    for i in range(0, len(input_list), chunk_size):
        group = input_list[i:i + chunk_size]
        result.append(group)

    return result

# subset the list of files to upload
upload_files = file_paths[0:18]
# upload_files = file_paths[9:18]
file_paths[18:]
# chunk the list of files into groups of 9
chunked_paths = chunk_list(upload_files)
[len(i) for i in chunked_paths]

# subdirectory = "/Users/anguswatters/Desktop/recipes_json/"

for i, chunk in enumerate(chunked_paths):
    print(f"i / len(chunked_paths): {i} / {len(chunked_paths)}")
    # print(f"chunk: {chunk}")
    print(f"len(chunk): {len(chunk)}")

    sleep_time = random.randint(3, 5)
    print(f"Sleeping for {sleep_time} seconds...")
    time.sleep(sleep_time)

    for path in chunk:
        # print(f"path: {path}")
        print(f"os.path.basename(path): {os.path.basename(path)}")
        
        s3_copy_cmd = f"aws s3 cp {path} {RAW_S3_URI}"
        print(f"S3 copy command: \n - '{s3_copy_cmd}'")

        # Run S3 copy command
        subprocess.run(s3_copy_cmd, shell=True)
        # print(f"===" * 5)


    # " --include ".join(chunk)
    
    # include_chunk = "".join([f' --include "{os.path.basename(i)}"' for i in chunk])

    # copy chunk of JSONs to S3
    # s3_copy_cmd = f"aws s3 cp {' '.join(chunk)} {RAW_S3_URI}"
    # s3_copy_cmd = f'aws s3 cp {subdirectory} {RAW_S3_URI} --recursive --exclude "*" {include_chunk}'
    # aws s3 cp yourSubFolder s3://mybucket/ --recursive --include "a*.txt" --include "b*.txt" --exclude="c*.txt" --exclude="d*.txt"
    # print(f"S3 copy command: \n - '{s3_copy_cmd}'")

    # # Run S3 copy command
    # subprocess.run(s3_copy_cmd, shell=True)
    # subprocess.run(f"aws s3 cp {' '.join(chunk)} {RAW_S3_URI}", shell=True)
    # aws s3 cp /Users/anguswatters/Desktop/recipes_json s3://recipes-raw-bucket/ --recursive --exclude "*"  --include "Users/anguswatters/Desktop/recipes_json/1144468_www_food_com*.json" --include "Users/anguswatters/Desktop/recipes_json/1633500_www_yummly_com*.json"
    print("===" * 10)

for chunk in chunked:
    for i in chunk:
        print(os.path.basename(i))
    print("===" * 10)

random.shuffle(file_paths)

for file in file_paths:
    print(f"file: {file}")

    sleep_time = random.randint(1, 3)

    print(f"Sleeping for {sleep_time} seconds...")
    time.sleep(sleep_time)

    subprocess.run(f"aws s3 cp {file} {RAW_S3_URI}", shell=True)
    # subprocess.process.call(f"aws s3 cp {test_base_dir}{file} s3://recipe-scrapers-jsons/", shell=True)

    print(f"===" * 10)