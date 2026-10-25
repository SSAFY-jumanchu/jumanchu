#Requires -Version 5.1
<#
=====================================================================
 register_batch_tasks.ps1 — 주만추 Windows 작업 스케줄러 등록
=====================================================================
 run_batch / warm_loop 를 Windows 작업 스케줄러에 4개 작업으로 등록한다.
 (schtasks.exe 가 아니라 ScheduledTasks 모듈: Register-ScheduledTask)

   (1) Jumanchu-Daily     평일 16:00     run_batch daily   (장 마감 15:30 후·PC 가동시간 내)
   (2) Jumanchu-Weekly    월요일 09:30   run_batch weekly  (마스터/메타/재무)
   (3) Jumanchu-Hourly    매시 정각      run_batch hourly  (뉴스 수집)
   (4) Jumanchu-VolWarmer 시스템 시작 시 warm_loop  (인기랭킹 시세·체결강도 ~30초 워밍, 죽으면 재시작)

 시각은 호스트 로컬(KST). PC 가동시간(평일 09:00~18:00) 안으로 맞춰 둠.
 -WakeToRun: 작업 시각에 PC가 *절전(sleep)* 이면 깨워서 실행. 단 완전 종료(shutdown)는
   못 깨운다(전원 꺼짐) → 그래서 시각을 가동시간 안에 둔 것. (절전→깨우기는 Windows
   전원 옵션의 '절전 타이머 허용'이 켜져 있어야 함, 보통 기본 켜짐)
 경로는 이 스크립트 위치(deploy/) 기준 자동 산출.

 실행 (관리자 PowerShell):
     powershell -ExecutionPolicy Bypass -File .\deploy\register_batch_tasks.ps1
 해제:
     powershell -ExecutionPolicy Bypass -File .\deploy\register_batch_tasks.ps1 -Unregister

 ⚠️ DB/Redis 의존: 배치는 Postgres·Redis가 떠 있어야 동작한다. 데모 PC에서 Docker
    Desktop으로 DB를 띄우는 경우, 작업은 '로그인 세션'에서 실행돼야 Docker가 살아있다
    → 본 스크립트는 현재 사용자 + Interactive(로그인 시 실행)로 등록한다.
    무인 서버라면 Principal을 SYSTEM/S4U로 바꾸고 DB/Redis를 시스템 서비스로 올려야 한다.
=====================================================================
#>
[CmdletBinding()]
param([switch]$Unregister)

$ErrorActionPreference = 'Stop'

# ── 경로/상수 (deploy/ 기준 자동 산출) ──────────────────────────────
$DeployDir = $PSScriptRoot
$Root      = Split-Path $DeployDir -Parent          # ...\jumanchu\jumanchu
$Backend   = Join-Path $Root 'backend'              # manage.py 위치
$LogDir    = Join-Path $Root 'logs\batch'
$Python    = (Get-Command python -ErrorAction Stop).Source
$PwshExe   = (Get-Command powershell -ErrorAction Stop).Source

$Tasks = 'Jumanchu-Daily', 'Jumanchu-Weekly', 'Jumanchu-Hourly', 'Jumanchu-VolWarmer'

function Remove-TaskIfExists {
    param([string]$Name)
    if (Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $Name -Confirm:$false
        Write-Host "  제거: $Name"
    }
}

if ($Unregister) {
    Write-Host '작업 해제...'
    $Tasks | ForEach-Object { Remove-TaskIfExists $_ }
    Write-Host '완료.'
    return
}

if (-not (Test-Path (Join-Path $Backend 'manage.py'))) {
    throw "manage.py 를 못 찾음: $Backend  (deploy/ 가 프로젝트 안에 위치하는지 확인)"
}
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# manage.py 명령 1개를 powershell 액션으로 (cwd=backend, 전 스트림을 로그에 append)
function New-ManageAction {
    param([string]$ManageArgs, [string]$LogName)
    # -u: 출력 버퍼링 끔(무한 루프 워머도 로그에 즉시). -X utf8: UTF-8 모드(작업스케줄러 CP949
    # 콘솔에서 한글·em-dash(—)·화살표(→) 출력 시 UnicodeEncodeError 방지). *>>: 전 스트림 로그 append.
    $inner = "Set-Location -LiteralPath '$Backend'; & '$Python' -u -X utf8 manage.py $ManageArgs *>> '$LogDir\$LogName'"
    # -WindowStyle Hidden: 창 안 뜨게(백그라운드 실행).
    return New-ScheduledTaskAction -Execute $PwshExe `
        -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "' + $inner + '"')
}

# 현재 사용자 + 로그인 시 실행 + 최고 권한
$principal = New-ScheduledTaskPrincipal -UserId ("$env:USERDOMAIN\$env:USERNAME") `
    -LogonType Interactive -RunLevel Highest

# 데이터 배치: 겹치면 새 인스턴스 무시(중복 적재 방지), 놓친 건 가능할 때 실행,
# 절전(sleep)이면 깨워서 실행(-WakeToRun). ※ 완전 종료는 못 깨움.
$batchSettings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -WakeToRun

# 시간별(매시) 트리거 — Once + 1시간 반복(throwaway 트리거의 Repetition 복사: 5.1 호환)
$hourlyTrigger = New-ScheduledTaskTrigger -Once -At '00:00'
$hourlyTrigger.Repetition = (New-ScheduledTaskTrigger -Once -At '00:00' `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)).Repetition

Write-Host '작업 등록...'
$Tasks | ForEach-Object { Remove-TaskIfExists $_ }   # 멱등: 기존 제거 후 재등록

Register-ScheduledTask -TaskName 'Jumanchu-Daily' -Principal $principal -Settings $batchSettings `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At '16:00') `
    -Action (New-ManageAction 'run_batch daily' 'daily.log') `
    -Description '주만추 일배치: 가격→지표→DNA→장투점수 (장 마감 후, PC 가동시간 내)' | Out-Null
Write-Host '  + Jumanchu-Daily (평일 16:00)'

Register-ScheduledTask -TaskName 'Jumanchu-Weekly' -Principal $principal -Settings $batchSettings `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At '09:30') `
    -Action (New-ManageAction 'run_batch weekly' 'weekly.log') `
    -Description '주만추 주배치: 마스터·메타·재무 (월요일 가동시간)' | Out-Null
Write-Host '  + Jumanchu-Weekly (월 09:30)'

Register-ScheduledTask -TaskName 'Jumanchu-Hourly' -Principal $principal -Settings $batchSettings `
    -Trigger $hourlyTrigger `
    -Action (New-ManageAction 'run_batch hourly' 'hourly.log') `
    -Description '주만추 시간배치: 뉴스 수집' | Out-Null
Write-Host '  + Jumanchu-Hourly (매시 정각)'

# 워머: 시스템 시작 시 1회 기동 → warm_loop 가 스스로 30초 루프(인기랭킹 시세+체결강도 워밍).
# ExecutionTimeLimit Zero = 무제한(루프 죽이지 않음), 죽으면 1분 간격 재시작.
$warmerSettings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName 'Jumanchu-VolWarmer' -Principal $principal -Settings $warmerSettings `
    -Trigger (New-ScheduledTaskTrigger -AtStartup) `
    -Action (New-ManageAction 'warm_loop' 'volwarmer.log') `
    -Description '주만추 인기랭킹 시세·체결강도 Redis 워머 (~30초 루프)' | Out-Null
Write-Host '  + Jumanchu-VolWarmer (시작 시 상시 루프)'

Write-Host ''
Write-Host "완료. 로그: $LogDir"
Write-Host '워머는 다음 부팅부터 자동. 지금 바로 켜려면:'
Write-Host '  Start-ScheduledTask -TaskName Jumanchu-VolWarmer'
