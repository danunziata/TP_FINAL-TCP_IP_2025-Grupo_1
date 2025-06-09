FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY modbus_cm4000_server.py .

EXPOSE 5020

CMD ["python", "modbus_cm4000_server.py"] 