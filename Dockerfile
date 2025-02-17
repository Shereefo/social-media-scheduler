FROM python:3.12-slim

WORKDIR /app  # ✅ Ensures Python runs inside /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]