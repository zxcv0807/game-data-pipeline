# docker-compose 명령어 정리

1. docker-compose up
```bash
# 백그라운드 실행
docker-compose up -d
```
2. docker-compose down
```bash
# 가장 기본적인 명령어. 
docker-compose down

# 모든 데이터까지 전부 삭제
docker-compose down --volumes