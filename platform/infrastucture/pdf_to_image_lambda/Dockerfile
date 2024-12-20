FROM public.ecr.aws/lambda/python:3.12

# Install system dependencies required for pdf2image and Poppler
RUN dnf update -y && \
    dnf install -y poppler-utils && \
    dnf clean all

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "lambda_function.handler" ]