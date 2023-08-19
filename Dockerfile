FROM python:3.8

RUN pip install flask requests flask_cors schedule

COPY proxy.py /app/proxy.py
COPY config.json /app/config.json # Temporary, will be overridden by ConfigMap

WORKDIR /app

CMD ["python", "proxy.py"]