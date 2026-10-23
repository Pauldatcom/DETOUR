FROM python:3.13-slim

WORKDIR /app

COPY . /app/

EXPOSE 8766

CMD ["python3", "app.py", "--host", "0.0.0.0", "--port", "8766"]