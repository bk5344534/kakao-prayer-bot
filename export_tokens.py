import os

refresh_token = os.environ.get("KAKAO_REFRESH_TOKEN", "")
rest_api_key = os.environ.get("KAKAO_REST_API_KEY", "")

with open("my_tokens.txt", "w", encoding="utf-8") as f:
    f.write(f"REST_API_KEY={rest_api_key}\n")
    f.write(f"REFRESH_TOKEN={refresh_token}\n")

print("토큰 정보가 my_tokens.txt 파일로 저장되었습니다.")
