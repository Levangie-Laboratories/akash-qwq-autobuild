# QwQ-32B-Preview Deployment on Akash

This repository contains all the necessary files to deploy the Qwen QwQ-32B-Preview language model on the Akash decentralized cloud. The model is served via a FastAPI application that provides a simple chat interface.

## Model Information

QwQ-32B-Preview is a 32.5B parameter language model developed by the Qwen Team, focused on advanced reasoning capabilities. It features:
- Full 32,768 token context window
- Strong performance in math and coding tasks
- 64 layers with attention heads

## Prerequisites

- Docker installed on your local machine
- Akash CLI set up with funded account
- A Docker registry account (Docker Hub, GHCR, etc.)

## Files Overview

- `app.py`: FastAPI server for model inference
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container configuration
- `deploy.yaml`: Akash SDL (Stack Definition Language) file

## Deployment Instructions

### 1. Build the Docker Image

```bash
# Build the image
docker build -t your-registry/qwq-32b:latest .

# Push to registry
docker push your-registry/qwq-32b:latest
```

### 2. Update the SDL File

Edit `deploy.yaml` and update the image reference with your actual registry path:

```yaml
services:
  qwq-model:
    image: your-registry/qwq-32b:latest  # Replace with your actual image path
```

### 3. Deploy to Akash

```bash
# Create deployment
akash tx deployment create deploy.yaml --from <your-key> --chain-id akashnet-2 -y

# List deployments to get DSEQ
akash query deployment list --owner <your-address> --chain-id akashnet-2

# View bids (replace DSEQ with your deployment sequence number)
akash query market bid list --owner <your-address> --dseq DSEQ --chain-id akashnet-2

# Accept a bid (replace variables accordingly)
akash tx market lease create --chain-id akashnet-2 --dseq DSEQ --provider PROVIDER --from <your-key> -y

# Send manifest
akash provider send-manifest deploy.yaml --dseq DSEQ --provider PROVIDER --from <your-key> --chain-id akashnet-2

# View lease status
akash provider lease-status --dseq DSEQ --provider PROVIDER --from <your-key> --chain-id akashnet-2

# Get service URI
akash provider lease-url --dseq DSEQ --provider PROVIDER --from <your-key> --chain-id akashnet-2
```

## Using the API

Once deployed, you can access the model through the provided API endpoints:

### Health Check

```bash
curl https://your-deployment-url/health
```

### Chat Endpoint

```bash
curl -X POST https://your-deployment-url/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Tell me about quantum computing"}
    ],
    "max_tokens": 500,
    "temperature": 0.7
  }'
```

## Resource Considerations

This deployment is configured for high-performance hardware:

- 8 CPU units
- 64GB RAM
- 100GB persistent storage
- 16GB shared memory
- 1 NVIDIA A100 GPU (preferred)

Adjust the resources in `deploy.yaml` if needed, but note that this model requires substantial hardware to run efficiently.

## Troubleshooting

- **No bids received**: Try increasing the bid amount in the SDL file
- **Container crashes**: Check if the provider has sufficient GPU memory (A100 80GB recommended)
- **Slow inference**: Consider reducing the context length or using quantized models

## Security Considerations

The current deployment exposes the API publicly. For production use:

1. Add authentication to the FastAPI server
2. Configure TLS for the API endpoints
3. Consider implementing rate limiting