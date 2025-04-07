FROM pytorch/pytorch:2.1.2-cuda11.8-cudnn8-devel

WORKDIR /workspace

RUN apt-get update && apt-get install -y git dos2unix && \
    pip install huggingface-hub vllm

COPY entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["bash", "/entrypoint.sh"]
