FROM python:3.13-slim

WORKDIR /app

COPY . /app/

EXPOSE 8765

CMD ["python3", "app.py", "--demo", "--host", "0.0.0.0", "--port", "8765"]