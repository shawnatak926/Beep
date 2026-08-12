# Beep Discord Bot

디스코드에서 시간표와 당직표를 조회하고, 수업 시작/종료 알림을 보내는 Python 봇입니다.

## 기능

- `!도움말`
  - 사용 가능한 명령어 출력
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

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
python bot.py
```

## 봇 초대

아래 링크로 디스코드 서버에 봇을 초대할 수 있습니다.

[봇 초대 링크](https://discord.com/api/oauth2/authorize?client_id=1488450783459676210&permissions=76800&scope=bot)

## 디스호스트 설정

- `STARTUP_FILE`: `bot.py`
- `PY_PACKAGES`: 비워두거나 아래 값 사용

```txt
discord.py apscheduler requests python-dotenv
```

Git 자동 반영을 쓰지 않으면, 디스호스트 `파일` 탭에 `bot.py`, `requirements.txt`를 직접 업로드한 뒤 재시작해야 합니다.

## 파일 구성

- [bot.py](/Users/shawnatak/Documents/GitHub/python/Beep/Untitled/bot.py)
  - 봇 실행 파일
- [requirements.txt](/Users/shawnatak/Documents/GitHub/python/Beep/Untitled/requirements.txt)
  - Python 의존성
- [timetable.png](/Users/shawnatak/Documents/GitHub/python/Beep/Untitled/timetable.png)
  - 참고용 시간표 이미지

## 주의사항

- `!clear`, `!clean`은 서버 채널에서만 사용하는 것을 권장합니다.
- 자동 알림이 동작하려면 봇이 해당 채널을 볼 수 있고 메시지 전송 권한이 있어야 합니다.
