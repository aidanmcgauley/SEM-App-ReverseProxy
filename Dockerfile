FROM python:3.8-slim-buster

RUN pip install Flask requests flask_cors schedule

COPY proxy.py /app/proxy.py
COPY config.json /app/config.json

WORKDIR /app

EXPOSE 80

CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]