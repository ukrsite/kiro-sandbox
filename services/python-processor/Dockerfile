FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt .
RUN apk add --no-cache gcc musl-dev libffi-dev && \
    apk upgrade --no-cache zlib && \
    pip install --no-cache-dir -r requirements.txt
COPY src ./src
EXPOSE 5000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"]
