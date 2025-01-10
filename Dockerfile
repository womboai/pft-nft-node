FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get -y install libpq-dev gcc wget git

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

CMD ["python", "main.py"]
