# FROM public.ecr.aws/lambda/python:3.8

# # # Install pip
# # RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
# #     python3 get-pip.py && \
# #     rm get-pip.py

# # Install required Python libraries
# RUN pip install transformers torch

# # Install the package from GitHub
# RUN pip install git+https://github.com/chambliss/foodbert.git

# # Set the working directory
# WORKDIR ${LAMBDA_TASK_ROOT}

# # Create a directory to store the model
# RUN mkdir -p ./model

# # Copy function code
# COPY extract_ingredients_lambda/extract_ingredients_lambda.py ${LAMBDA_TASK_ROOT}

# # Download and save the model from HuggingFace
# RUN python3 - <<EOF
# from transformers import DistilBertForTokenClassification

# # HuggingFace path to model
# HF_MODEL_PATH = "chambliss/distilbert-for-food-extraction"

# # Download the model from HuggingFace
# model = DistilBertForTokenClassification.from_pretrained(HF_MODEL_PATH)

# # Specify the directory where you want to save the model
# save_directory = './model/chambliss-distilbert-for-food-extraction'

# # Save the model and its configuration to the specified directory
# model.save_pretrained(save_directory)
# EOF

# # Set the CMD to your handler
# CMD [ "extract_ingredients_lambda.extract_ingredients_lambda" ]

FROM public.ecr.aws/lambda/python:3.11-x86_64
# FROM public.ecr.aws/lambda/python:3.11.2023.12.13.21

WORKDIR ${LAMBDA_TASK_ROOT}

# Install git
RUN yum install -y git \ 
    && pip install git+https://github.com/chambliss/foodbert.git \
    && yum -y clean all

# RUN yum install -y git
# RUN yum install -y git && yum -y clean all
	
# # install our dependencies
# RUN python3 -m pip install -r requirements.txt --target ${LAMBDA_TASK_ROOT}

# Copy the earlier created requirements.txt file to the container
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the python requirements from requirements.txt
RUN pip install -r requirements.txt

# # Install the FoodModel package from GitHub
# RUN pip install git+https://github.com/chambliss/foodbert.git

# Copy main python function over
COPY extract_ingredients_lambda.py ./

# Create a model directory
RUN mkdir model

# Download and save the model from HuggingFace
RUN python3 - <<EOF
from transformers import DistilBertForTokenClassification

# HuggingFace path to model
HF_MODEL_PATH = "chambliss/distilbert-for-food-extraction"

# Download the model from HuggingFace
model = DistilBertForTokenClassification.from_pretrained(HF_MODEL_PATH)

# Specify the directory where you want to save the model
save_directory = './model/chambliss-distilbert-for-food-extraction'

# Save the model and its configuration to the specified directory
model.save_pretrained(save_directory)
EOF

# Set the CMD to your handler
CMD [ "extract_ingredients_lambda.extract_ingredients_lambda" ]

