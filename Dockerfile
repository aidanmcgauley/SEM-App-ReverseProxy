FROM python:3.8

RUN pip install flask requests flask_cors schedule

COPY proxy.py /app/proxy.py

WORKDIR /app

CMD ["python", "proxy.py"]