# syntax=docker/dockerfile:1
# get a slim version of a python image
FROM python:3.11.4-slim
# do not generate compiled python files (.pyc) to save spaces
ENV PYTHONDONTWRITEBYTECODE=1
# no buffering of stdout and stderr
ENV PYTHONUNBUFFERED=1
# set root dir for relative imports
ENV PYTHONPATH=/app
# create working dir in container
WORKDIR /app
# create non-privileged user for app
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "10001" \
    appuser
# install system dependencies for python-magic and remove cache files afterwards
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    exiftool \
    && rm -rf /var/lib/apt/lists/*
# install requirements
COPY requirements.txt /app/requirements.txt
COPY template/ /app/template
RUN python -m pip install -U --upgrade pip --no-cache-dir -r /app/requirements.txt
# copy source code into container
COPY . .
# set permissions for source code
RUN chown -R appuser:appuser /app
# switch to the non-privileged user
USER appuser
# run the app
CMD ["python", "app/main.py"]