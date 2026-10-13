import json
import os
import requests

# ==========================================
# 1. 설정 정보
# ==========================================

# GitHub Secrets에서 가져올 카카오 REST API 키
REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY")

# GitHub Secrets에서 가져올 카카오 Refresh Token
REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")

# Google Docs (구글 문서) 기도제목 파일 URL (텍스트 추출용)
DRIVE_URL = "https://docs.google.com/document/d/1jyA3_rwx8KS9b2ZEpiSxLhy_qyU0WvoptakcnpWu1xs/export?format=txt"

# 기도제목 수정용 단축 링크
EDIT_DOCS_URL = "https://docs.google.com/document/d/1jyA3_rwx8KS9b2ZEpiSxLhy_qyU0WvoptakcnpWu1xs/edit?usp=sharing"

# 기도제목 순번 저장 파일
STATUS_FILE = "status.json"

# QT 버튼을 눌렀을 때 열리는 주소
QT_URL = "https://mobile.duranno.com/qtlite/bible/"


# ==========================================
# 2. 기본 설정 확인
# ==========================================

def check_settings():
    """
    GitHub Secrets가 제대로 설정되어 있는지 확인합니다.
    """
    if not REST_API_KEY:
        raise Exception(
            "KAKAO_REST_API_KEY가 설정되어 있지 않습니다."
        )

    if not REFRESH_TOKEN:
        raise Exception(
            "KAKAO_REFRESH_TOKEN이 설정되어 있지 않습니다."
        )


# ==========================================
# 3. 카카오 Access Token 갱신
# ==========================================

def refresh_kakao_token():
    """
    GitHub Secrets에 저장된 Refresh Token을 사용하여
    새로운 Access Token을 발급받습니다.
    """
    url = "https://kauth.kakao.com/oauth/token"

    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": REFRESH_TOKEN
    }

    response = requests.post(url, data=data)

    # HTTP 오류가 발생하면 예외 발생
    response.raise_for_status()

    result = response.json()

    # 새로운 Access Token 확인
    if "access_token" not in result:
        raise Exception(
            f"카카오 Access Token 갱신 실패: {result}"
        )

    access_token = result["access_token"]

    print("카카오 Access Token 갱신 성공")

    return access_token


# ==========================================
# 4. Google Docs에서 기도제목 가져오기
# ==========================================

def get_prayers():
    """
    Google Docs 문서에 저장된 기도제목 텍스트를 가져옵니다.
    --- 구분자로 잘라 배열로 반환합니다.
    """
    response = requests.get(DRIVE_URL)

    # HTTP 오류가 발생하면 예외 발생
    response.raise_for_status()

    response.encoding = "utf-8"

    prayers = [
        p.strip()
        for p in response.text.split("---")
        if p.strip()
    ]

    return prayers


# ==========================================
# 5. 기도제목 순서(Index) 관리
# ==========================================

def get_next_index(total_count):
    """
    status.json에 저장된 현재 순번을 읽고
    이번에 사용할 기도제목 번호를 결정합니다.
    """
    current_index = 0

    # status.json이 있으면 기존 순번을 읽습니다.
    if os.path.exists(STATUS_FILE):
        with open(
            STATUS_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            status = json.load(f)
            current_index = status.get(
                "current_index",
                0
            )

    # 전체 기도제목 개수를 넘으면 처음으로 돌아갑니다.
    if total_count > 0:
        next_index = (
            current_index + 1
        ) % total_count
    else:
        next_index = 0

    # 다음 실행을 위한 순번 저장
    with open(
        STATUS_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            {
                "current_index": next_index
            },
            f,
            ensure_ascii=False,
            indent=4
        )

    # 이번 실행에서 사용할 번호 반환
    return current_index


# ==========================================
# 6. 다음날 가정 이름 추출 함수
# ==========================================

def get_family_name(prayer_text):
    """
    기도제목 텍스트의 첫 번째 줄에서 가정 이름을 추출합니다.
    """
    first_line = prayer_text.strip().split("\n")[0].strip()
    return first_line


# ==========================================
# 7. 카카오톡 나와의 채팅으로 메시지 보내기
# ==========================================

def send_kakao_message(
    access_token,
    message_text,
    next_family_name
):
    """
    카카오톡 '나와의 채팅'으로
    오늘의 기도제목, 다음날 가정 안내, 기도제목 수정 링크를 보냅니다.
    """
    url = (
        "https://kapi.kakao.com/"
        "v2/api/talk/memo/default/send"
    )

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # 카카오톡에 표시할 메시지
    formatted_text = (
        "[오늘의 기도제목]\n\n"
        f"{message_text}\n\n"
        "─────────────────\n"
        f"📢 내일은 {next_family_name} 차례입니다. 기도제목 확인해 주세요.\n"
        f"✏️ 기도제목 수정하기:\n{EDIT_DOCS_URL}\n"
        "─────────────────\n"
        "📖 오늘의 말씀/QT 묵상하기\n"
        "아래 버튼을 터치해 주세요!"
    )

    # 카카오톡 메시지 템플릿
    template = {
        "object_type": "text",
        "text": formatted_text,
        "link": {
            "web_url": QT_URL,
            "mobile_web_url": QT_URL
        },
        "button_title": "묵상하기(QT)"
    }

    payload = {
        "template_object": json.dumps(
            template,
            ensure_ascii=False
        )
    }

    response = requests.post(
        url,
        headers=headers,
        data=payload
    )

    response.raise_for_status()

    return response.json()


# ==========================================
# 8. 메인 실행
# ==========================================

if __name__ == "__main__":

    try:
        print("==============================")
        print("오늘의 기도제목 봇 시작")
        print("==============================")

        # ----------------------------------
        # 1) GitHub Secrets 확인
        # ----------------------------------
        check_settings()
        print("GitHub Secrets 확인 완료")

        # ----------------------------------
        # 2) 카카오 Access Token 갱신
        # ----------------------------------
        access_token = refresh_kakao_token()

        # ----------------------------------
        # 3) Google Docs 기도제목 가져오기
        # ----------------------------------
        prayers = get_prayers()

        if not prayers:
            raise Exception(
                "Google Docs에서 기도제목을 찾을 수 없습니다."
            )

        print(
            f"기도제목 {len(prayers)}개를 확인했습니다."
        )

        # ----------------------------------
        # 4) 오늘 및 내일 기도제목 선택
        # ----------------------------------
        idx = get_next_index(
            len(prayers)
        )

        today_prayer = prayers[idx]

        # 다음날 순번 계산 (마지막 번호 다음은 0번)
        next_idx = (idx + 1) % len(prayers)
        next_prayer = prayers[next_idx]

        # 다음날 가정 이름(첫 줄) 추출
        next_family = get_family_name(next_prayer)

        print(
            f"오늘의 기도제목: {idx + 1}/{len(prayers)}"
        )
        print(
            f"내일 차례 가정: {next_family}"
        )

        # ----------------------------------
        # 5) 카카오톡 나와의 채팅으로 보내기
        # ----------------------------------
        result = send_kakao_message(
            access_token,
            today_prayer,
            next_family
        )

        # ----------------------------------
        # 6) 결과 확인
        # ----------------------------------
        if result.get("result_code") == 0:
            print(
                f"[{idx + 1}/{len(prayers)}] "
                "카카오톡 나와의 채팅으로 발송 성공!"
            )
        else:
            print("카카오톡 발송 결과:")
            print(result)

        print("==============================")
        print("오늘의 기도제목 봇 종료")
        print("==============================")

    except Exception as e:
        print("==============================")
        print("오류가 발생했습니다.")
        print("==============================")
        print(str(e))
        raise
