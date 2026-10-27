import json
import os
import requests

# GitHub Secrets에서 Access Token 가져오기
ACCESS_TOKEN = os.environ.get("KAKAO_ACCESS_TOKEN")

# 환경변수가 없을 때를 대비해 REST_API_KEY와 REFRESH_TOKEN으로 즉시 갱신 시도
REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY")
REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")


def get_access_token():
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    if REST_API_KEY and REFRESH_TOKEN:
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": REST_API_KEY,
            "refresh_token": REFRESH_TOKEN,
        }
        res = requests.post(url, data=data)
        res.raise_for_status()
        return res.json().get("access_token")

    raise Exception("카카오 토큰 정보를 찾을 수 없습니다.")


def fetch_friends_uuid():
    token = get_access_token()
    url = "https://kapi.kakao.com/v1/api/talk/friends"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    result = response.json()
    friends = result.get("elements", [])

    print("==========================================")
    print(f"📋 동의한 친구 목록 (총 {result.get('total_count', 0)}명)")
    print("==========================================")

    if not friends:
        print(
            "⚠️ 조회된 친구가 없습니다. 상대방이 동의 링크를 완료했는지 확인해 주세요."
        )
        return

    # Secrets에 바로 복사해서 붙여넣을 수 있는 JSON 형태 생성
    uuid_dict = {}
    for friend in friends:
        name = friend.get("profile_nickname", "이름없음")
        uuid = friend.get("uuid")
        uuid_dict[name] = uuid
        print(f"• 닉네임: {name}")
        print(f"  UUID:   {uuid}")
        print("------------------------------------------")

    print("\n💡 [GitHub Secrets 복사용 JSON 데이터]")
    print(json.dumps(uuid_dict, ensure_ascii=False, indent=2))
    print("==========================================")


if __name__ == "__main__":
    try:
        fetch_friends_uuid()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        raise
