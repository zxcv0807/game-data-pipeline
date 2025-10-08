import os
import requests
import time # time 라이브러리 추가
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('RIOT_API_KEY')
HEADERS = {
    "X-Riot-Token": API_KEY
}

def get_account_info_by_puuid(puuid):
    """
    puuid를 사용하여 계정 정보(게임 이름, 태그라인)를 가져옵니다.
    """
    # ACCOUNT-V1 API 엔드포인트 (서버 주소가 다름에 유의)
    url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
    
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        account_info = response.json()
        return account_info.get('gameName'), account_info.get('tagLine')
    else:
        # 요청 실패 시 None 반환
        return None, None

def get_challenger_league_and_names():
    """
    KR 서버 챌린저 리그 정보를 가져온 후, 각 유저의 puuid로 계정 정보를 조회합니다.
    """
    league_url = "https://kr.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
    
    print("챌린저 리그 데이터 요청을 시작합니다...")
    league_response = requests.get(league_url, headers=HEADERS)

    if league_response.status_code == 200:
        print("리그 정보 요청 성공!")
        league_data = league_response.json()

        print("\n--- 상위 5명 챌린저 이름 및 정보 조회 ---")
        for i, entry in enumerate(league_data['entries'][:5]):
            user_puuid = entry.get('puuid')
            league_points = entry.get('leaguePoints', 0)

            if user_puuid:
                # puuid로 계정 정보 조회 함수 호출
                game_name, tag_line = get_account_info_by_puuid(user_puuid)
                
                if game_name and tag_line:
                    print(f"{i+1}. 이름: {game_name}#{tag_line}, LP: {league_points}")
                else:
                    print(f"{i+1}. PUUID: {user_puuid}의 계정 정보 조회 실패")
            
            # API 요청 횟수 제한(Rate Limit)을 준수하기 위해 잠시 대기합니다.
            time.sleep(0.1)

    else:
        print(f"리그 정보 요청 실패. 상태 코드: {league_response.status_code}")
        print(f"에러 메시지: {league_response.text}")

if __name__ == "__main__":
    get_challenger_league_and_names()