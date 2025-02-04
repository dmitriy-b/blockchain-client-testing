FROM docker:dind

# Install Docker Compose
# RUN apk add --no-cache py3-pip && \
#     pip3 install docker-compose

# Create working directory
WORKDIR /app

# Copy docker-compose file and HTML content into the container
COPY docker-compose.yml .
COPY .env .
COPY configs ./devnet
COPY validator-teku ./validator-data

RUN mkdir -p /consensus-data
RUN mkdir -p /execution-data

# Expose ports for services
EXPOSE 8545
EXPOSE 8551
EXPOSE 4000

# Start Docker daemon and bring up Docker Compose services
CMD ["sh", "-c", "dockerd-entrypoint.sh & sleep 5 && docker-compose up -d && tail -f /dev/null"]