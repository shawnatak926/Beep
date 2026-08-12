# Beep Discord Bot

디스코드에서 시간표와 당직표를 조회하고, 수업 시작/종료 알림을 보내는 Python 봇입니다.

## 기능

- `!시간표`, `!우성민`
  - 대구소프트웨어고등학교 2학년 3반 시간표 출력
  - 컴시간에서 실시간 조회 시도 후 실패하면 기본 시간표 사용
- `!당직`
  - 구글 스프레드시트 기반 당직표 출력
- `!clear 숫자`
  - 최근 메시지 삭제
- `!clean 이름 숫자`
  - 특정 유저 메시지 삭제

## 자동 알림

- 평일 `08:40` 1교시 시작 알림
- 각 교시 종료 후 다음 수업 알림
- 매일 `16:30` 당직표 전송

## 요구사항

- Python 3.12 권장
- Discord Bot Token
- 전송 대상 채널 ID

## 설치

```bash
pip install -r requirements.txt
```

## 환경변수

`.env` 파일 또는 서버 환경변수에 아래 값을 설정합니다.

```env
DISCORD_BOT_TOKEN=your-discord-bot-token
DISCORD_CHANNEL_ID=1488451289976275037
```

예시는 [`.env.example`](/Users/shawnatak/Documents/GitHub/python/Beep/Untitled/.env.example)에 있습니다.

## 실행

```bash
python bot.py
```

## 디스호스트 설정

- `STARTUP_FILE`: `bot.py`
- `PY_PACKAGES`: 비워두거나 아래 값 사용

```txt
discord.py apscheduler requests python-dotenv
```

- 환경변수
  - `DISCORD_BOT_TOKEN`
  - `DISCORD_CHANNEL_ID`

Git 자동 반영을 쓰지 않으면, 디스호스트 `파일` 탭에 `bot.py`, `requirements.txt`를 직접 업로드한 뒤 재시작해야 합니다.

## 파일 구성

- [bot.py](/Users/shawnatak/Documents/GitHub/python/Beep/Untitled/bot.py)
  - 봇 실행 파일
- [requirements.txt](/Users/shawnatak/Documents/GitHub/python/Beep/Untitled/requirements.txt)
  - Python 의존성
- [timetable.png](/Users/shawnatak/Documents/GitHub/python/Beep/Untitled/timetable.png)
  - 참고용 시간표 이미지

## 주의사항

- 봇 토큰은 코드에 직접 넣지 말고 환경변수로 관리합니다.
- `!clear`, `!clean`은 서버 채널에서만 사용하는 것을 권장합니다.
- 자동 알림이 동작하려면 봇이 해당 채널을 볼 수 있고 메시지 전송 권한이 있어야 합니다.
