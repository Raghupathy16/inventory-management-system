FROM python:3.12-slim

WORKDIR /app

# We use PyMySQL (pure Python driver), so no MySQL client build tools are
# needed here — keeping the image lean.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# --reload is fine for development; production would drop this and add
# multiple workers, which we'll revisit in Phase 18 (Deployment).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
