FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    default-mysql-client

RUN mkdir /app
ADD . /app
WORKDIR /app

RUN pip install pip -U
RUN pip install -r /app/requirements.txt

ENTRYPOINT ["sh", "/app/entrypoint.sh" ]
CMD ["default"]