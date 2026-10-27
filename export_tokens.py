import os

refresh_token = os.environ.get("KAKAO_REFRESH_TOKEN", "")
rest_api_key = os.environ.get("KAKAO_REST_API_KEY")

print("==========================================")
print(f"REST_API_KEY:  {rest_api_key}")
print(f"REFRESH_TOKEN: {refresh_token}")
print("==========================================")
