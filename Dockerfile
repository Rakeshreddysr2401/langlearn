# 1️⃣ Use a lightweight Python image
FROM python:3.11-slim

# 2️⃣ Set the working directory inside the container
WORKDIR /app

# 3️⃣ Copy requirements and install them
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4️⃣ Copy all project files into the container
COPY . .

# 5️⃣ Run as a non-root user
RUN useradd --create-home appuser
USER appuser

# 6️⃣ Expose the port the app actually binds to
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# 7️⃣ Start the FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
