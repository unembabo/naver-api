FROM python:3.12-slim

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api_server.py place_fetch.py ./

ENV PYTHONUNBUFFERED=1
EXPOSE 5000

CMD ["python", "api_server.py"]


# FROM python:3.9-slim

# RUN apt-get update && apt-get install -y \
#     pptp-linux \
#     network-manager-pptp \
#     iptables \
#     && rm -rf /var/lib/apt/lists/*

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install -r requirements.txt

# COPY . .

# COPY setup_proxy.sh /setup_proxy.sh
# RUN chmod +x /setup_proxy.sh

# COPY start.sh /start.sh
# RUN chmod +x /start.sh

# CMD ["/start.sh"]