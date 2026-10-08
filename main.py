import json
import os
import requests

# ==========================================
# 1. 설정 정보
# ==========================================
REST_API_KEY = "75fd7d26a80aa1cd9d53b29af37f356e"
DRIVE_URL = "https://drive.google.com/uc?export=download&id=1R5MBPTC-Ec1aby8Toow6Rcxgko6ofjve"
TOKEN_FILE = "kakao_code.json"
STATUS_FILE = "status.json"

# ==========================================
# 2. 카카오 토큰 자동 갱신 함수
# ==========================================
def refresh_kakao_token():
    with open(TOKEN_FILE, "r") as f:
        tokens = json.load(f)

    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": tokens.get("refresh_token")
    }

    response = requests.post(url, data=data)
    result = response.json()

    # 새로운 access_token 업데이트
    if "access_token" in result:
        tokens["access_token"] = result["access_token"]
        # refresh_token도 새로 갱신되어 들어온 경우 업데이트
        if "refresh_token" in result:
            tokens["refresh_token"] = result["refresh_token"]

        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=4)
        return tokens["access_token"]
    else:
        print("토큰 갱신 실패:", result)
        return tokens.get("access_token")

# ==========================================
# 3. 구글 드라이브 기도제목 불러오기 함수
# ==========================================
def get_prayers():
    response = requests.get(DRIVE_URL)
    response.encoding = "utf-8"
    prayers = [p.strip() for p in response.text.split("---") if p.strip()]
    return prayers

# ==========================================
# 4. 순서(Index) 관리 함수
# ==========================================
def get_next_index(total_count):
    current_index = 0
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            status = json.load(f)
            current_index = status.get("current_index", 0)

    # 전체 개수를 넘어서면 다시 0번(첫 번째)부터 로테이션
    next_index = (current_index + 1) % total_count if total_count > 0 else 0

    # 다음 실행을 위해 저장
    with open(STATUS_FILE, "w") as f:
        json.dump({"current_index": next_index}, f)

    return current_index

# ==========================================
# 5. 카카오톡 메시지 전송 함수 (시각화 강화)
# ==========================================
def send_kakao_message(access_token, message_text):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}

    QT_URL = "https://mobile.duranno.com/qtlite/bible/"

    # 본문 끝에 버튼으로 시선을 유도하는 문구 추가
    formatted_text = (
        f" [오늘의 기도제목]\n\n"
        f"{message_text}\n\n"
        f"─────────────\n"
        f"📖 오늘의 말씀/QT 묵상하기\n"
        f"아래 버튼을 터치해 주세요! 👇"
    )

    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": formatted_text,
            "link": {
                "web_url": QT_URL,
                "mobile_web_url": QT_URL
            },
            "button_title": "묵상하기(QT)"
        })
    }

    response = requests.post(url, headers=headers, data=payload)
    return response.json()

# ==========================================
# 메인 실행 로직
# ==========================================
if __name__ == "__main__":
    try:
        # 1. 토큰 갱신
        access_token = refresh_kakao_token()

        # 2. 기도제목 목록 읽기
        prayers = get_prayers()

        if not prayers:
            print("기도제목이 비어있습니다.")
        else:
            # 3. 오늘의 순서 확인
            idx = get_next_index(len(prayers))
            today_prayer = prayers[idx]

            # 4. 카카오톡 발송
            res = send_kakao_message(access_token, today_prayer)

            if res.get("result_code") == 0:
                print(f"[{idx + 1}/{len(prayers)} 번째 가정] 기도제목 발송 성공!")
            else:
                print("발송 실패:", res)

    except Exception as e:
        print("오류 발생:", e)