# set base image
FROM python:3.9-alpine3.13
LABEL maintainer="philip"

# do not buffer python console outputs
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000
# by default, we are not in development mode
# we set this argument to true in docker-compose.yml in order to install the dev dependencies
# we need linting and testing tools in development but do not need them in production
ARG DEV=false

# 1. create virtual environment to add dependencies
# 2. upgrade package manager pip
# 3. install the list of requirements inside the virtual environment (inside docker image)
# 4. remove the tmp directory
# 5. add new user (other than root user) inside the docker image; for safety reasons
# 6. create a directory for storing media, static files (change ownership, permissions of the directory)
RUN python -m venv /py && \
  /py/bin/pip install --upgrade pip && \
  apk add --update --no-cache postgresql-client jpeg-dev && \
  apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev zlib zlib-dev&& \
  /py/bin/pip install -r /tmp/requirements.txt && \
  if [ $DEV = "true" ]; \
    then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
  fi && \
  rm -rf /tmp && \
  apk del .tmp-build-deps && \
  adduser \
    --disabled-password \
    --no-create-home \
    django-user && \
  mkdir -p /vol/web/media && \
  mkdir -p /vol/web/static && \
  chown -R django-user:django-user /vol && \
  chmod -R 755 /vol/web

# update the path environment variable (where executables can be run)
# add the virtral environment path to the path environment variable
ENV PATH="/py/bin:$PATH"

# switch to our non-root user
USER django-user
