FROM python:3.12-slim


WORKDIR /app


RUN apt-get update \
    && apt-get -y install libpq-dev gcc wget

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./imagenode /app/imagenode

CMD 
CMD ["python", "-m", "imagenode.chatbots.pft_image_bot"]
