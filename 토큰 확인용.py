from dotenv import load_dotenv
import os

# .env 파일의 절대 경로를 명시적으로 지정
dotenv_path = 'C:\\Users\\hajin\\.vscode\\discordbot\\DISCORD_TOKEN.env'  # 경로에서 슬래시 하나가 빠지지 않도록 확인
load_dotenv(dotenv_path=dotenv_path)

# DISCORD_TOKEN 환경 변수 로드
TOKEN = os.getenv('DISCORD_TOKEN')

# 토큰 값 확인
print(TOKEN)

if TOKEN is None:
    print("DISCORD_TOKEN을 .env 파일에서 찾을 수 없습니다.")
else:
    print("토큰이 성공적으로 로드되었습니다.")

