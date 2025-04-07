import os
import csv
import chardet
import requests
import re
import sys

# 설정
csv.field_size_limit(sys.maxsize)
API_URL = "http://localhost:8889/v1/completions"
MODEL = "google/gemma-3-12b-it"
MAX_TOKENS_PER_REQUEST = 8192
APPROX_CHARS_PER_TOKEN = 3
MAX_INPUT_CHARS = (MAX_TOKENS_PER_REQUEST - 512) * APPROX_CHARS_PER_TOKEN

SYSTEM_PROMPT_TEMPLATE = """당신은 한국과 영어 번역가로 입력된 텍스트 "{sentence}"에 대한 번역 작업을 수행해주세요. 반드시 [규칙]을 바탕으로 답변을 작성합니다.
[규칙]
1. "{sentence}"는 한국어 텍스트입니다.
2. "{sentence}"의 한국어를 영어로 번역해야 합니다.
3. "{sentence}"에 포함된 영어는 번역을 하지 않습니다.
4. "{sentence}"가 숫자 및 특수문자를 포함하더라도 문장의 의미를 해치지 않으면 번역 대상에 포함합니다.
5. 번역 외에는 어떠한 작업도 수행하지 않습니다.
6. 답변 예시: "1. 일반사항1.1 적용범위(1) 이 기준은 법령 및 규정의 준수,"는 영어로 "1.Construction in general 1.1 Scope of Application (1) This standard applies to compliance with laws and regulations,"로 번역됩니다.
7. 답변 형식은 다음과 같습니다:
답변: 번역
"""

# 의미 단위 자르기 (기존 유지)
def split_text_by_structure(text: str, max_chars: int = 2000):
    paragraphs = re.split(r'(?=\n?\d+\.\d+)', text.strip())
    final_chunks = []

    for para in paragraphs:
        if len(para.strip()) == 0:
            continue
        if len(para) <= max_chars:
            final_chunks.append(para.strip())
        else:
            clauses = re.split(r'(?=\(\d+\))', para)
            temp = ""
            for clause in clauses:
                if len(temp + clause) > max_chars:
                    final_chunks.append(temp.strip())
                    temp = clause
                else:
                    temp += clause
            if temp:
                final_chunks.append(temp.strip())
    return final_chunks

# 번역 요청
def translate_text(text: str) -> str:
    chunks = split_text_by_structure(text.strip(), max_chars=MAX_INPUT_CHARS)
    translated_chunks = []

    for chunk in chunks:
        prompt = SYSTEM_PROMPT_TEMPLATE.replace("{sentence}", chunk)
        full_prompt = f"<bos><start_of_turn>user\n{prompt}<start_of_turn>model\n"

        payload = {
            "model": MODEL,
            "prompt": full_prompt,
            "temperature": 0.7,
            "max_tokens": 1024
        }

        try:
            response = requests.post(API_URL, json=payload)
            result = response.json()
            translated = result['choices'][0]['text'].replace("답변:", "").strip()
            print(f"[TRANSLATED] : {translated}")
            translated_chunks.append(translated)
        except Exception as e:
            translated_chunks.append(f"[ERROR] : {e}")

    return " ".join(translated_chunks)

# 인코딩 감지
def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read())
        print(f"[ENCODING] : {result['encoding']}")
        return result["encoding"]

# CSV 처리
def process_csv(input_path, output_path):
    encoding = detect_encoding(input_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(input_path, "r", encoding=encoding) as infile, \
         open(output_path, "w", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["name_en", "contents_en"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            code_type = row.get("codeType", "").strip()
            code = row.get("code", "").strip()

            if code_type not in ["KDS", "KCS"]:
                continue
            if not code.isdigit():
                continue

            name = row.get("name", "")
            contents = row.get("contents", "")

            name_en = translate_text(name) if name.strip() else ""
            contents_en = translate_text(contents) if contents.strip() else ""

            row["name_en"] = name_en
            row["contents_en"] = contents_en
            writer.writerow(row)

# 디렉토리 내 모든 CSV 처리
def translate_all_csv_files(input_list=["./data/KCS", "./data/KDS"], 
                            output_list=["./data/KCS/output", "./data/KDS/output"]):
    for input_dir, output_dir in zip(input_list, output_list):
        os.makedirs(output_dir, exist_ok=True)
        for filename in os.listdir(input_dir):
            if not filename.endswith(".csv"):
                continue
            
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            if os.path.exists(output_path):
                print(f"[ALREADY EXISTS] : {output_path}")
                continue

            print(f"[TRANSLATING] : {filename}")
            process_csv(input_path, output_path)
            print(f"[SAVE COMPLETED] : {output_path}")

# 실행
if __name__ == "__main__":
    translate_all_csv_files()