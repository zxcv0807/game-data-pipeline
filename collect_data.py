import os
import requests
import time
import json
import boto3
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('RIOT_API_KEY')
HEADERS = {
    "X-Riot-Token": API_KEY
}

def get_account_info_by_puuid(puuid):
    url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        account_info = response.json()
        return account_info.get('gameName'), account_info.get('tagLine')
    else:
        return None, None

def get_challenger_league_and_upload_to_s3():
    league_url = "https://kr.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
    
    print("챌린저 리그 데이터 요청을 시작합니다...")
    league_response = requests.get(league_url, headers=HEADERS)

    if league_response.status_code == 200:
        print("리그 정보 요청 성공!")
        league_data = league_response.json()
        
        # 최종 데이터를 저장할 빈 리스트 생성
        challenger_list = []

        print("\n--- 상위 20명 챌린저 정보 조회 및 데이터 수집 ---")
        # 더 많은 데이터를 위해 조회 인원을 20명으로 늘립니다.
        for i, entry in enumerate(league_data['entries'][:20]):
            user_puuid = entry.get('puuid')
            league_points = entry.get('leaguePoints', 0)

            if user_puuid:
                game_name, tag_line = get_account_info_by_puuid(user_puuid)
                
                if game_name and tag_line:
                    # 화면에 진행 상황 출력
                    print(f"  {i+1}번째 유저: {game_name}#{tag_line} 정보 수집 완료")
                    
                    # 수집한 데이터를 딕셔너리 형태로 정리
                    user_data = {
                        'summonerName': f"{game_name}#{tag_line}",
                        'puuid': user_puuid,
                        'leaguePoints': league_points,
                        'rank': entry.get('rank'),
                        'wins': entry.get('wins'),
                        'losses': entry.get('losses')
                    }
                    # 정리된 데이터를 리스트에 추가
                    challenger_list.append(user_data)
                else:
                    print(f"  {i+1}번째 유저: PUUID({user_puuid}) 정보 조회 실패")
            
            time.sleep(0.1)
        
        # S3에 업로드할 데이터가 있는지 확인
        if not challenger_list:
            print("수집된 데이터가 없어 S3에 업로드하지 않습니다.")
            return

        # 클라이언트 생성
        s3_client = boto3.client('s3')
        # S3 버킷 이름 설정
        bucket_name = 'zxcv0807-game-data-bucket'
        # 파일 이름 설정
        file_key = 'raw-data/challengers/challengers.json'

        try:
            # 1. 파이썬 리스트(challenger_list)를 JSON 형식의 문자열로 변환합니다.
            json_data = json.dumps(challenger_list, ensure_ascii=False, indent=4)

            # 2. S3 버킷에 파일을 업로드합니다.
            s3_client.put_object(
                Bucket=bucket_name,
                Key=file_key,
                Body=json_data,
                ContentType='application/json'
            )

            print(f"\n✅ 데이터 수집 및 업로드 완료! 총 {len(challenger_list)}명의 데이터가 S3 버킷 '{bucket_name}'의 '{file_key}' 경로에 저장되었습니다.")
            
        except Exception as e:
            print(f"\n❌ S3 업로드 중 에러가 발생했습니다: {e}")

    else:
        print(f"리그 정보 요청 실패. 상태 코드: {league_response.status_code}")

if __name__ == "__main__":
    get_challenger_league_and_upload_to_s3()