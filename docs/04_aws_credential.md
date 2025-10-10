# AWS 자격 증명 설정

## 1단계: AWS CLI 설치
```bash
pip install awscli
```
## 2단계: AWS CLI 설정
AWS IAM에서 발급받은 액세스 키 ID (Access Key ID)와 비밀 액세스 키(Secret Access Key)를 준비한다.
```bash
aws configure
```
를 실행하면 아래 4가지 정보를 차례대로 입력한다.

AWS Access Key ID: [준비한 액세스 키 ID를 붙여넣으세요]
AWS Secret Access Key: [준비한 비밀 액세스 키를 붙여넣으세요]
Default region name: [주로 사용할 AWS 리전 입력, 예: ap-northeast-2]
Default output format: [json 이라고 입력]

이 설정은 한 번 해두면 컴퓨터에 저장되어 앞으로 모든 AWS 연동 작업에 사용된다.