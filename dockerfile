# get python runtime as parent image
FROM python:3.9-slim

# set working directory
WORKDIR /bounce-cast

# system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy server directory
COPY server/ server/

# Expose the udp port for wt
EXPOSE 4433/udp

# run the server on start
CMD ["python3", "server/http3_server.py", "-c", "server/certificate.pem", "-k", "server/certificate.key", "--fps", "60", "--grav", "980", "--vel", "1000.0", "1000.0", "--cor", "0.97"]
