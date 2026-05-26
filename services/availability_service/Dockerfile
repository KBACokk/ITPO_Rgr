FROM python:3.11-slim
WORKDIR /app
COPY services/availability_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gen/ /app/
COPY services/availability_service/ /app/
ENV PYTHONPATH=/app
CMD ["python", "server.py"]
