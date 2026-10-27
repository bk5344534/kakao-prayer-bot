import base64
import json
import os
from nacl import encoding, public
import requests

# ==========================================
# 1. 설정 정보
# ==========================================

# GitHub Secrets에서 가져올 카카오 REST API 키
REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY")

# GitHub Secrets에서 가져올 카카오 Refresh Token
REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")

# GitHub Secrets 자동 업데이트용 환경변수 (PAT 및 Repository 정보)
GH_PAT = os.environ.get("GH_PAT")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")  # 예: "username/repo"

# GitHub Secrets에서 이름:UUID 매핑 정보 가져오기
RECEIVER_MAP_ENV = os.environ.get("KAKAO_RECEIVER_UUIDS")

if RECEIVER_MAP_ENV:
    try:
        RECEIVER_MAP = json.loads(RECEIVER_MAP_ENV)
    except Exception:
        RECEIVER_MAP = {}
else:
    # Secrets가 없을 경우 예시 데이터 (로컬 테스트용)
    RECEIVER_MAP = {
        "이지의": "실제_UUID는_GitHub_Secrets에만_안전하게_저장됩니다"
    }

# ==========================================
# [ 핵심 ] 메시지를 발송할 수신자 명단 직접 지정
# ==========================================
# Secrets에 여러 명이 등록되어 있어도, 아래 리스트에 포함된 사람에게만 메시지가 발송됩니다.
# 예시: ["이지의"], ["이지의", "김철수"]
TARGET_NAMES = ["이지의"]

# 지정된 이름들에 해당하는 UUID만 매핑 테이블에서 추출 (최대 5명)
RECEIVER_UUIDS = [
    RECEIVER_MAP[name] for name in TARGET_NAMES if name in RECEIVER_MAP
]

# Google Docs 기도제목 파일 URL
DRIVE_URL = "https://docs.google.com/document/d/1jyA3_rwx8KS9b2ZEpiSxLhy_qyU0WvoptakcnpWu1xs/export?format=txt"

# 기도제목 수정용 링크
EDIT_DOCS_URL = "https://docs.google.com/document/d/1jyA3_rwx8KS9b2ZEpiSxLhy_qyU0WvoptakcnpWu1xs/edit?usp=sharing"

# 기도제목 순번 저장 파일
STATUS_FILE = "status.json"

# QT 버튼 주소
QT_URL = "https://mobile.duranno.com/qtlite/bible/"


# ==========================================
# 2. 기본 설정 확인
# ==========================================


def check_settings():
    """GitHub Secrets 및 수신자 설정 확인"""
    if not REST_API_KEY:
        raise Exception("KAKAO_REST_API_KEY가 설정되어 있지 않습니다.")

    if not REFRESH_TOKEN:
        raise Exception("KAKAO_REFRESH_TOKEN이 설정되어 있지 않습니다.")

    if not RECEIVER_UUIDS:
        raise Exception(
            f"선택한 발송 대상({TARGET_NAMES})의 UUID를 Secrets에서 찾을 수"
            " 없거나 대상이 비어 있습니다."
        )


# ==========================================
# 3. GitHub Secrets 자동 업데이트 함수 (신규)
# ==========================================


def update_github_secret(secret_name, secret_value):
    """GitHub API를 사용해 Secrets 값을 자동으로 업데이트합니다."""
    if not GH_PAT or not GITHUB_REPOSITORY:
        print(
            "⚠️ GH_PAT 또는 GITHUB_REPOSITORY가 설정되지 않아 Secrets를 자동"
            " 업데이트할 수 없습니다."
        )
        return

    headers = {
        "Authorization": f"token {GH_PAT}",
        "Accept": "application/vnd.github.v3+json",
    }

    # 1. 저장소의 Public Key 가져오기 (암호화용)
    key_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/secrets/public-key"
    res = requests.get(key_url, headers=headers)
    res.raise_for_status()
    key_data = res.json()

    public_key = key_data["key"]
    key_id = key_data["key_id"]

    # 2. Secret 값 암호화 (Libsodium / PyNaCl)
    public_key_obj = public.PublicKey(
        public_key.encode("utf-8"), encoding.Base64Encoder
    )
    sealed_box = public.SealedBox(public_key_obj)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    encrypted_value = base64.b64encode(encrypted).decode("utf-8")

    # 3. GitHub Secrets 업데이트 요청
    secret_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/secrets/{secret_name}"
    payload = {"encrypted_value": encrypted_value, "key_id": key_id}

    put_res = requests.put(secret_url, headers=headers, json=payload)
    if put_res.status_code in [201, 204]:
        print(f"✅ GitHub Secret '{secret_name}' 자동 갱신 성공!")
    else:
        print(
            f"❌ GitHub Secret 갱신 실패: {put_res.status_code} {put_res.text}"
        )


# ==========================================
# 4. 카카오 Access Token 갱신 (보완)
# ==========================================


def refresh_kakao_token():
    """Refresh Token으로 새로운 Access Token 발급

    (새로운 Refresh Token이 함께 내려오면 GitHub Secrets를 자동 갱신합니다.)
    """
    url = "https://kauth.kakao.com/oauth/token"

    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": REFRESH_TOKEN,
    }

    response = requests.post(url, data=data)
    response.raise_for_status()

    result = response.json()

    if "access_token" not in result:
        raise Exception(f"카카오 Access Token 갱신 실패: {result}")

    # 새로운 Refresh Token이 발급되었는지 확인 후 Secrets 업데이트
    new_refresh_token = result.get("refresh_token")
    if new_refresh_token and new_refresh_token != REFRESH_TOKEN:
        print(
            "🔄 새로운 Kakao Refresh Token 발급됨. GitHub Secrets 업데이트를"
            " 시도합니다..."
        )
        update_github_secret("KAKAO_REFRESH_TOKEN", new_refresh_token)

    access_token = result["access_token"]
    print("카카오 Access Token 갱신 성공")

    return access_token


# ==========================================
# 5. Google Docs에서 기도제목 가져오기
# ==========================================


def get_prayers():
    """Google Docs에서 기도제목 텍스트 가져오기"""
    response = requests.get(DRIVE_URL)
    response.raise_for_status()
    response.encoding = "utf-8"

    prayers = [
        p.strip() for p in response.text.split("---") if p.strip()
    ]

    return prayers


# ==========================================
# 6. 기도제목 순서(Index) 관리
# ==========================================


def get_next_index(total_count):
    """현재 순번 읽기 및 다음 순번 저장"""
    current_index = 0

    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status = json.load(f)
            current_index = status.get("current_index", 0)

    if total_count > 0:
        next_index = (current_index + 1) % total_count
    else:
        next_index = 0

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"current_index": next_index},
            f,
            ensure_ascii=False,
            indent=4,
        )

    return current_index


# ==========================================
# 7. 다음날 가정 이름 추출
# ==========================================


def get_family_name(prayer_text):
    """첫 번째 줄에서 가정 이름 추출"""
    first_line = prayer_text.strip().split("\n")[0].strip()
    return first_line


# ==========================================
# 8. 카카오톡 메시지 전송 함수
# ==========================================


def create_template(message_text, next_family_name):
    """공통 메시지 템플릿 생성"""
    formatted_text = (
        "[오늘의 기도제목]\n\n"
        f"{message_text}\n\n"
        "──────────────\n"
        f"📢 내일은 {next_family_name} 차례입니다. 기도제목 확인해 주세요.\n"
        "✏️ 기도제목 수정: 여기를 터치하세요!\n"
        "──────────────\n"
        "📖 오늘의 말씀/QT 묵상하기\n"
        "아래 버튼을 터치해 주세요!"
    )

    return {
        "object_type": "text",
        "text": formatted_text,
        "link": {
            "web_url": EDIT_DOCS_URL,
            "mobile_web_url": EDIT_DOCS_URL,
        },
        "buttons": [
            {
                "title": "묵상하기(QT)",
                "link": {"web_url": QT_URL, "mobile_web_url": QT_URL},
            }
        ],
    }


def send_kakao_message_to_friends(
    access_token, receiver_uuids, message_text, next_family_name
):
    """상대방(친구)에게 메시지 보내기 (최대 5명)"""
    url = "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    template = create_template(message_text, next_family_name)

    payload = {
        "receiver_uuids": json.dumps(receiver_uuids),
        "template_object": json.dumps(template, ensure_ascii=False),
    }

    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()


# ==========================================
# 9. 메인 실행
# ==========================================

if __name__ == "__main__":
    try:
        print("==============================")
        print("오늘의 기도제목 봇 시작")
        print("==============================")

        # 1) 기본 설정 및 수신자 확인
        check_settings()
        print(f"선택된 발송 대상자: {TARGET_NAMES}")

        # 2) Access Token 갱신 (필요시 Refresh Token 자동 업데이트)
        access_token = refresh_kakao_token()

        # 3) Google Docs 기도제목 가져오기
        prayers = get_prayers()
        if not prayers:
            raise Exception("Google Docs에서 기도제목을 찾을 수 없습니다.")

        print(f"기도제목 {len(prayers)}개를 확인했습니다.")

        # 4) 오늘 및 내일 기도제목 선택
        idx = get_next_index(len(prayers))
        today_prayer = prayers[idx]

        next_idx = (idx + 1) % len(prayers)
        next_prayer = prayers[next_idx]
        next_family = get_family_name(next_prayer)

        print(f"오늘의 기도제목: {idx + 1}/{len(prayers)}")
        print(f"내일 차례 가정: {next_family}")

        # 5) 선택된 상대방(친구)에게 메시지 전송
        res_friends = send_kakao_message_to_friends(
            access_token, RECEIVER_UUIDS, today_prayer, next_family
        )
        successful_uuids = res_friends.get("successful_receiver_uuids", [])
        if successful_uuids:
            print(
                f"상대방 메시지 발송 성공! (성공 대상: {TARGET_NAMES}, 인원:"
                f" {len(successful_uuids)}명)"
            )
        else:
            print(f"상대방 메시지 발송 실패: {res_friends}")

        print("==============================")
        print("오늘의 기도제목 봇 종료")
        print("==============================")

    except Exception as e:
        print("==============================")
        print("오류가 발생했습니다.")
        print("==============================")
        print(str(e))
        raise
