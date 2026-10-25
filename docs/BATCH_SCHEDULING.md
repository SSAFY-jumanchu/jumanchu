# 배치 스케줄링 가이드

> 주만추 배치를 **자동으로 돌리는 법**. 정책 표는 [API_스키마_v1.5.md §10.3](API_스키마_v1.5.md).
> 핵심: 배치 명령은 "한 번 실행하고 끝"이라, **정해진 시각에 대신 실행해줄 스케줄러**를 붙여야 자동이 된다.

---

## 0. 배치는 2종류

| 종류 | 명령 | 성격 | 스케줄 |
|---|---|---|---|
| **데이터 적재** | `python manage.py run_batch {daily\|weekly\|hourly}` | 의존 순서대로 한 번 실행 | cron형(특정 시각) |
| **실시간 워머** | `python manage.py warm_loop` | 스스로 30초마다 반복하는 상시 루프 | 부팅 시 1회 기동 |

- `run_batch daily` = 가격→지표→DNA→장투점수 / `weekly` = 마스터·메타·재무 / `hourly` = 뉴스.
- `warm_loop` = 인기종목 **시세+체결강도**를 ~30초마다 Redis 워밍(랭킹 시세·거래비율용). cron은 분 단위라 못 해서 **루프 프로그램**으로 만든 것. (`warm_popular_prices` + `warm_volume_power` 묶음)

---

## 1. ⚡ 빠른 시작 (데모 — 스케줄러 없이 수동)

발표용이면 **자동화 없이 발표 전에 손으로** 한 번 돌리는 게 가장 안전·간단하다.

```bash
# (전제) DB·Redis 기동
docker compose up -d db redis

cd backend
python manage.py run_batch daily      # 가격→지표→DNA→장투점수
# (선택) python manage.py run_batch weekly / hourly
# (선택) 랭킹 거래비율 워밍을 한 번:  python manage.py warm_volume_power
```

> `run_batch ... --dry-run` 으로 실행 단계만 미리 확인할 수 있다.

---

## 2. 전제 (어느 환경이든 공통)

스케줄러가 명령을 칠 때 아래가 안 맞으면 **조용히 실패**한다:

1. **DB(Postgres)·Redis 기동** — 안 떠 있으면 배치 실패
2. **올바른 위치** — `manage.py` 가 있는 `backend/` 에서 실행 (cwd)
3. **python 경로** — 어떤 파이썬인지 명확히 (전역 vs venv)
4. **`.env` 로딩** — Django settings 가 `BASE_DIR.parent/.env`(=`backend/../.env`) + `backend/.env` 를 읽음
5. **로그 남기기** — 자동이라 안 보이니 `>> *.log 2>&1` 필수

---

## 3. 환경별 자동화

### 3-1. Windows 작업 스케줄러 (로컬 데모 PC)

```powershell
# 관리자 PowerShell에서
powershell -ExecutionPolicy Bypass -File .\deploy\register_batch_tasks.ps1
# 해제: ... register_batch_tasks.ps1 -Unregister
```
4개 작업 등록: `Jumanchu-Daily`(평일 **16:00**) · `Jumanchu-Weekly`(**월 09:30**) · `Jumanchu-Hourly`(매시) · `Jumanchu-VolWarmer`(시작 시 상시 루프). 로그는 `logs/batch/*.log`.

> 🕐 **시각은 PC 가동시간(평일 09:00~18:00) 안으로** 맞춰 둠 — 그 시간 밖이면 PC가 꺼져서 안 돈다. daily는 KR 마감(15:30) 후·종료(18:00) 전인 16:00.
> 💤 **`-WakeToRun`**: 작업 시각에 PC가 *절전(sleep)* 이면 깨워서 실행한다. **단 완전 종료(shutdown)는 못 깨운다**(전원이 꺼져 있어 불가). Windows 전원 옵션에서 '절전 타이머 허용'이 켜져 있어야 함(보통 기본 켜짐).
> ⚠️ **Docker Desktop 주의**: DB/Redis를 Docker Desktop으로 띄우면 *로그인 세션*에서만 살아있고, **로그인 시 자동 시작**(Docker Desktop 설정)이 켜져 있어야 켤 때 DB가 뜬다. 스크립트는 **현재 사용자 + 로그인 시 실행**으로 등록한다. 무인 서버라면 Principal을 SYSTEM/S4U로, DB/Redis를 시스템 서비스로.
> 워머를 지금 바로 켜려면: `Start-ScheduledTask -TaskName Jumanchu-VolWarmer`

→ [deploy/register_batch_tasks.ps1](../deploy/register_batch_tasks.ps1)

### 3-2. Linux cron (배포 서버)

```bash
sudo mkdir -p /var/log/jumanchu && sudo chown $USER /var/log/jumanchu
# deploy/jumanchu.cron 안의 BACKEND/PY 경로 치환 후
crontab deploy/jumanchu.cron        # 확인: crontab -l
```
- `TZ=Asia/Seoul` 로 KST 고정, `flock -n` 으로 **중복 적재 방지**.
- 워머(30초 루프)는 cron 부적합 → `@reboot` 또는 **systemd 서비스 권장**(파일 하단에 unit 예시).

→ [deploy/jumanchu.cron](../deploy/jumanchu.cron)

### 3-3. Docker (참고 — 미완성 예시)

[deploy/docker-compose.scheduler.yml](../deploy/docker-compose.scheduler.yml) — `ofelia`(cron 사이드카) + `volwarmer` 서비스 패턴.
> ⚠️ 현재 backend **Dockerfile·컨테이너 서비스가 없어** 그대로는 안 뜬다. backend 컨테이너화 후 사용. 데모는 3-1/3-2 권장.

---

## 4. `warm_loop` 동작

- 한 사이클마다 `warm_popular_prices`(인기 시세) + `warm_volume_power`(체결강도)를 호출해 랭킹용 Redis 캐시(`stock:rankprice:*`·`stock:volpower:*`)를 데움.
- `--interval`(기본 30초) 주기 무한 루프. 한 사이클이 실패해도 루프는 안 죽음(다음 주기 재시도).
- **`close_old_connections()`** 로 Neon 유휴 연결을 정리 — 장수명 루프 안전.
- 시장시간 게이트는 없음(항상 워밍). 장 마감 시 KIS가 빈/정지 응답이라 캐시가 빌 뿐 무해. 실제론 PC 가동시간(09–18)에만 돈다.
- 테스트: `--once`(1사이클 후 종료) · `--size/--chunk`(워머 옵션 전달).

```bash
python manage.py warm_loop --once     # 1사이클만 검증
```

---

## 5. 운영 주의 / 한계 (인지 필수)

| 항목 | 내용 |
|---|---|
| **타임존** | 스케줄 시각은 호스트 로컬(KST 가정). cron은 `TZ=Asia/Seoul` 명시. US 서머타임은 `_is_market_open`의 zoneinfo가 처리. |
| **공휴일 미고려** | `_is_market_open`은 공휴일을 모른다 → 휴장일에도 `daily`가 돈다. daily는 멱등(재적재 무해)이라 큰 문제 없음. 워머(warm_loop)는 게이트가 없어 항상 워밍하나, 휴장 시 KIS가 빈/정지 응답이라 무해. (KR/US 공휴일 캘린더는 후속) |
| **동시 실행 방지** | 배치가 길어져 다음 트리거와 겹치면 중복 적재 위험 → Linux `flock -n`, Windows 작업 `MultipleInstances IgnoreNew`로 차단. |
| **실패 감지/알림** | `run_batch`는 실패 단계 있으면 **비-0 종료**. 야간 실패를 아침에 모르지 않으려면 종료코드를 받아 Slack/메일로 알리는 래퍼 권장(미구현 — 후속). 우선은 `*.log` 확인. |
| **로그 분리·로테이션** | 데이터배치/워머 로그를 별도 파일로(daily/weekly/hourly/volwarmer.log). Linux는 `logrotate`, Docker는 logging `max-size/max-file`. |
| **워머 좀비 방지** | 워머가 살아만 있고 KIS 인증 만료 등으로 아무것도 못 워밍할 수 있음 → 로그 모니터링/헬스체크는 후속 과제. |

---

## 참고

- 정책 표: [API_스키마_v1.5.md §10.3](API_스키마_v1.5.md)
- 산출물: [register_batch_tasks.ps1](../deploy/register_batch_tasks.ps1) · [jumanchu.cron](../deploy/jumanchu.cron) · [docker-compose.scheduler.yml](../deploy/docker-compose.scheduler.yml)
- 오케스트레이터: `backend/stocks/management/commands/run_batch.py` · 워머: `warm_loop.py` (= `warm_popular_prices` + `warm_volume_power`)
