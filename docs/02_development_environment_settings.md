# 프로젝트 생성 및 Git 연동

## 1단계: Git 초시화 및 Github 연동
1. 현재 폴더를 Git 저장소로 만든다.
```bash
git init
```
2. Github와 연동한다.
Github 사이트에서 game-data-pipeline 라는 새로운 저장소를 생성한다.
현재 로컬 폴더와 Github 원격 저장소를 연결한다.
```bash
# 현재 로컬 폴더와 Github 원격 저장소를 연결
git remote add origin https://github.com/zxcv0807/game-data-pipeline.git

#기본 브랜치 이름은 'main'으로 설정
git branch -M main
```

## 2단계: python 가상 환경 설정
1. 가상 환경 생성
```bash
# 'venv'라는 이름의 가상 환경을 만들기기
python -m venv venv

# 가상 환경 활성화
.\venv\Scripts\activate
```