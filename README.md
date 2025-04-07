# 한국어 → 영어 CSV 자동 번역 파이프라인

이 프로젝트는 `./data/KCS/` 및 `./data/KDS/` 디렉토리에 존재하는 CSV 파일 내 `name`, `contents` 필드의 한국어 텍스트를 영어로 자동 번역하여, `output` 하위 디렉토리에 저장하는 파이프라인입니다.  
번역에는 로컬에서 실행되는 VLLM API 서버(`google/gemma-3-12b-it` 모델 사용)를 활용합니다.

---

## 🗂️ 폴더 구조

```
.
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── translation.py  ← 번역 메인 로직
├── .env
├── data
│   ├── KCS
│   │   ├── output/*.csv (결과 파일)
│   │   └── *.csv (입력 파일)
│   └── KDS
│   │   ├── output/*.csv (결과 파일)
│       └── *.csv (입력 파일)
└── vllm/ (VLLM 로컬 실행 관련)
```

---

## ⚙️ 실행 방법

1. `.env` 파일에 Hugging Face 토큰 설정

   ```dotenv
   HUGGINGFACE_HUB_TOKEN=your_token_here
   ```

2. Docker 이미지 빌드 및 컨테이너 실행

   ```bash
   docker-compose up --build
   ```

3. 번역 실행

   ```bash
   docker exec -it vllm-chat-api python translation.py
   ```

---

## 🛠️ 번역 서버 구성

이 프로젝트는 VLLM 기반의 OpenAI 호환 API 서버를 사용합니다. `entrypoint.sh`를 통해 다음 명령어로 실행됩니다:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model google/gemma-3-12b-it \
  --port 8889 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192
```

---

## 📐 번역 chunk 분할 기준

`translation.py` 내에서는 긴 텍스트를 의미 단위로 나누기 위해 `split_text_by_structure()` 함수를 사용합니다. 이 함수는 다음과 같은 기준에 따라 chunk(번역 단위)를 나눕니다:

### 1. 문단 기준 분할 (1차 분리)

- 정규식: `(?=\n?\d+\.\d+)`
- 의미: `1.`, `2.3`, `3.1` 등 숫자+점 형태로 시작하는 **조항 단위**
- 예시:
  ```
  1. 일반사항
  1.1 적용범위
  ```

### 2. 괄호 조항 기준 분할 (2차 분리)

- 정규식: `(?=\(\d+\))`
- 의미: `(1)`, `(2)` 등 **소항목 단위**
- 예시:
  ```
  (1) 이 기준은...
  (2) 건설 공사의...
  ```

### 3. 최대 길이 제한

- 설정값: `MAX_INPUT_CHARS`
- 목적: VLLM API가 허용하는 최대 입력 길이(토큰 수 기준)를 초과하지 않도록 각 chunk의 길이를 제한

```python
MAX_INPUT_CHARS = (MAX_TOKENS_PER_REQUEST - 512) * APPROX_CHARS_PER_TOKEN
```

---

## 💬 예시 출력 로그

```
[ENCODING] : EUC-KR
[TRANSLATING] : example.csv
[TRANSLATED] : 1. General Information 1.1 Scope of Application ...
[SAVE COMPLETED] : ./data/KCS/output/example.csv
```
