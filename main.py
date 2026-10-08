import requests
import json

# 1단계에서 복사한 디스코드 웹후크 URL을 여기에 붙여넣으세요.
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1557706724591407213/wppyx5Mw5KBvmXl4-Wi3XehAFCUXkMH5NVd2z_GG85DH8DihXosvdP4a2vWr9qZNz6gX"

def send_to_discord():
    # 여기에 전송할 기도제목 내용을 작성하거나 기존 파일/구글드라이브 로직 연동
    message_content = "[오늘의 기도제목]\n\n오늘도 주님 안에서 승리하는 하루 되세요!"

    payload = {
        "content": message_content
    }

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 204 or response.status_code == 200:
        print("디스코드 전송 성공!")
    else:
        print(f"전송 실패: {response.status_code}, {response.text}")

if __name__ == "__main__":
    send_to_discord()
