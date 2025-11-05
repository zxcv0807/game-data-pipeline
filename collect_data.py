import os
import requests
import time
import json
import boto3
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('RIOT_API_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_FILE_KEY = 'raw-data/league_data/league_data.json'
HEADERS = {
    "X-Riot-Token": API_KEY
}

# 수집할 리그 목록 정의
LEAGUES_TO_FETCH = {
    'challenger': 'https://kr.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5',
    'grandmaster': 'https://kr.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5',
    'master': 'https://kr.api.riotgames.com/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5'
}

def get_account_info_by_puuid(puuid):
    time.sleep(1.3)
    url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        account_info = response.json()
        return account_info.get('gameName'), account_info.get('tagLine')
    else:
        print(f"  [경고] PUUID({puuid}) 정보 조회 실패: {response.status_code}")
        return None, None

def collect_all_league_data():
    # 챌린저, 그랜드마스터, 마스터 리그 데이터를 모두 수집
    all_players_list = []

    for league_name, league_url in LEAGUES_TO_FETCH.items():
        print(f"\n--- {league_name.upper()} 리그 데이터 수집 시작 ---")
        league_response = requests.get(league_url, headers=HEADERS)

        if league_response.status_code != 200:
            print(f"[실패] {league_name} 리그 정보 요청 실패: {league_response.status_code}")
            continue
        
        league_data = league_response.json()
        players = league_data.get('entries', [])

        # 마스터 티어는 데이터가 너무 많으므로, 상위 100명만 샘플링
        if league_name == 'master' and len(players) > 100:
            print(f"  마스터 티어 플레이어 {len(players)}명 중 상위 100명만 수집합니다.")
            players = sorted(players, key=lambda p: p.get('leaguePoints', 0), reverse=True)[:100]

        print(f"{league_name} 리그에서 {len(players)}명의 플레이어 정보 수집 중...")

        for i, entry in enumerate(players):
            user_puuid = entry.get('puuid')
            league_points = entry.get('leaguePoints', 0)

            if not user_puuid:
                continue
            
            game_name, tag_line = get_account_info_by_puuid(user_puuid)

            if game_name and tag_line:
                user_data = {
                    'tier': league_name.upper(),
                    'summonerName': f"{game_name}#{tag_line}",
                    'puuid': user_puuid,
                    'leaguePoints': league_points,
                    'rank': entry.get('rank'),
                    'wins': entry.get('wins'),
                    'losses': entry.get('losses')
                }
                all_players_list.append(user_data)

                if (i + 1) % 20 == 0:
                    print(f"{i+1} / {len(players)} 명 처리 완료...")

    if not all_players_list:
        print("수집된 데이터가 없습니다. S3 업로드를 건너뜁니다.")
        return
        
    # S3에 업로드
    print(f"\n--- 총 {len(all_players_list)}명의 통합 데이터를 S3에 업로드합니다 ---")
    s3_client = boto3.client('s3')
    try:
        json_data = json.dumps(all_players_list, ensure_ascii=False, indent=4)
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=S3_FILE_KEY,
            Body=json_data,
            ContentType='application/json'
        )
        print(f"✅ S3 업로드 완료! 경로: {S3_BUCKET_NAME}/{S3_FILE_KEY}")

    except Exception as e:
        print(f"\n S3 업로드 중 에러가 발생했습니다: {e}")
        raise


if __name__ == "__main__":
    collect_all_league_data()