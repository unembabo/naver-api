FROM python:3.12-slim

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api_server.py place_fetch.py ./

ENV PYTHONUNBUFFERED=1
EXPOSE 5001

CMD ["python", "api_server.py"]

