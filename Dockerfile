# 1️⃣ Use a lightweight Python 3.11 image
FROM python:3.11-slim

# 2️⃣ Set the working directory inside the container
WORKDIR /app

# 3️⃣ Copy requirements and install them
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4️⃣ Copy all project files into the container
COPY . .

# 5️⃣ Expose port 8000 for the FastAPI app
EXPOSE 8000

# 6️⃣ Start the FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


