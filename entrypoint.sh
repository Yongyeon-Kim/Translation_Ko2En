#!/bin/bash
set -e

huggingface-cli login --token "$HUGGINGFACE_HUB_TOKEN"

python -m vllm.entrypoints.openai.api_server \
  --model google/gemma-3-12b-it \
  --port 8889 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192 \