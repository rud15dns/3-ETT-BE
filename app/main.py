from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import fitz
from app.routes.feedback_router import router as feedback_router
from app.routes.kakao_auth_router import router as kakao_auth_router
from app.routes.archive_router import router as archive_router
from fastapi.middleware.cors import CORSMiddleware
from app.utils.rulebook import validate_rulebook
import base64
import httpx
import time
import uuid
import json

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 프론트엔드 도메인만 허용할 수 있습니다.
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)


app.include_router(kakao_auth_router)
app.include_router(archive_router)
app.include_router(feedback_router)

class TextIn(BaseModel):
    text: str

def validate_response(results):
    """
    validate_rulebook 결과를 받아서
    {"isTrue": bool, "details" : ... } 구조로 반환한다.
    """
    if not results:
        return {"isTrue": False, "details": None}
    return {"isTrue": True, "details":results}

def extract_text_from_pdf(data: bytes) -> str:
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            return "\n".join(page.get_text() or "" for page in doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 처리 실패: {e}")
    
    
@app.get('/')
def home():
    return {"message" : "Welcome Home"}

@app.post("/validate")
def rulebook_endpoint(payload: TextIn):
    results = validate_rulebook(payload.text)
    return validate_response(results)


# @app.post("/validate-pdf")
# async def validate_pdf(file: UploadFile = File(...)):
#     data = await file.read()

#     text = extract_text_from_pdf(data)

#     results = validate_rulebook(text)
#     return validate_response(results)


# @app.post("/validate-image")
# async def validate_image(file: UploadFile = File(...)):
#     data = await file.read()

#     b64 = base64.b64encode(data).decode("utf-8")

#     body = {
#         "version": "V2",
#         "requestId": str(uuid.uuid4()),
#         "timestamp": int(round(time.time() * 1000)),
#         "images": [
#             {
#                 # 파일 확장자에 맞춰 format 지정 (png, jpg 등)
#                 "format": file.filename.rsplit(".", 1)[-1].lower(),
#                 "name": "uploaded-image",
#                 "data": b64,
#                 "url": None
#             }
#         ]
#     }

#     headers = {
#         "Content-Type": "application/json",
#         "X-OCR-SECRET": OCR_SECRET
#     }
#     async with httpx.AsyncClient() as client:
#         resp = await client.post(OCR_ENDPOINT, json=body, headers=headers)
#     if resp.status_code != 200:
#         raise HTTPException(status_code=resp.status_code,
#                             detail=f"OCR API 호출 실패: {resp.text}")

#     resp_json = resp.json()
#     # 텍스트 추출
#     texts = [f["inferText"] for f in resp_json["images"][0]["fields"]]
#     ocr_text = " ".join(texts)

#     # print(ocr_text) # 제대로 처리됨.
#     results = validate_rulebook(ocr_text)
#     return validate_response(results)
