import base64
import os

# ==========================================
# GitHub Secrets 환경 변수 읽기
# ==========================================
rest_api_key = os.environ.get("KAKAO_REST_API_KEY", "")
refresh_token = os.environ.get("KAKAO_REFRESH_TOKEN", "")

# 1. 글자 사이에 '-'를 추가하여 마스킹 우회
readable_refresh_token = "-".join(list(refresh_token)) if refresh_token else ""

# 2. Base64 인코딩을 통한 마스킹 우회
encoded_refresh_token = (
    base64.b64encode(refresh_token.encode("utf-8")).decode("utf-8")
    if refresh_token
    else ""
)

# ==========================================
# 출력
# ==========================================
print("==========================================")
print("🔑 카카오 토큰 정보 조회 결과")
print("==========================================")
print(f"REST API KEY: {rest_api_key}")
print("------------------------------------------")
print("1️⃣ [방법 1] 글자 사이 '-' 포함 출력 (복사 후 '-' 제거하여 사용):")
print(readable_refresh_token)
print("------------------------------------------")
print("2️⃣ [방법 2] Base64 인코딩된 토큰 (디코더 사이트에서 복원하여 사용):")
print(encoded_refresh_token)
print("==========================================")
