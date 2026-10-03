FROM python:3.9-slim

FROM python:3.9-slim

RUN pip install "setuptools<58" "eventlet==0.30.2"

RUN pip install --no-cache-dir ryu

COPY app/monitored_switch.py /app/monitored_switch.py

ENV PYTHONPATH=/app

EXPOSE 6653 6654 6655 6656

CMD ["ryu-manager"]
