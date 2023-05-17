FROM python:3.10
# setting the working directory in the Docker image
WORKDIR /usr/src/app

# creating a virtual environment and activate it
RUN python -m venv venv
ENV PATH="/usr/src/app/venv/bin:$PATH"

# installing dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# coppying the current directory contents into the Docker image
COPY . .

# setting the PYTHONPATH to the directory where files were copied
ENV PYTHONPATH /usr/src/app

# setting the entrypoint to run your Python script
ENTRYPOINT ["python", "main.py"]