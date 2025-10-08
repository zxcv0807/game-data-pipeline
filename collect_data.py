import os
import requests
from dotenv import load_dotenv

# .env 파일에서 환경 변수(API 키)를 불러옵니다.
load_dotenv()
API_KEY = os.getenv('RIOT_API_KEY')

def get_challenger_league_data():
    """
    KR 서버의 챌린저 리그 정보를 API를 통해 가져옵니다.
    가장 기본이 되는 API 호출 테스트입니다.
    """
    # API 엔드포인트 URL (한국 서버의 챌린저 리그 정보)
    url = "https://kr.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"

    # API 요청 시 헤더에 API 키를 포함하여 보냅니다.
    headers = {
        "X-Riot-Token": API_KEY
    }

    print("챌린저 리그 데이터 요청을 시작합니다...")

    # requests 라이브러리를 사용해 API에 GET 요청을 보냅니다.
    response = requests.get(url, headers=headers)

    # 요청이 성공했는지 확인합니다 (상태 코드 200 = 성공)
    if response.status_code == 200:
        print("API 요청 성공!")
        # JSON 형식의 응답 데이터를 파이썬 딕셔너리로 변환합니다.
        data = response.json()
        
        # 데이터가 너무 많으니, 상위 5명의 소환사 이름만 출력해봅니다.
        print("--- 상위 5명 챌린저 소환사 ---")
        for i, entry in enumerate(data['entries'][:5]):
            print(f"{i+1}. {entry['puuid']}")
        
        return data
    else:
        print(f"API 요청 실패. 상태 코드: {response.status_code}")
        print(f"에러 메시지: {response.text}")
        return None

# 이 스크립트 파일이 직접 실행될 때만 아래 함수를 호출합니다.
if __name__ == "__main__":
    get_challenger_league_data()