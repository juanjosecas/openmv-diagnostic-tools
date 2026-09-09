# ============================================================
# 10_monitor_usb_openmv.ps1
#
# OBJETIVO:
# Monitorear cambios de dispositivos USB y puertos COM mientras
# se reproduce una falla intermitente.
#
# NO modifica drivers ni dispositivos.
# Detener con Ctrl+C.
# ============================================================

param(
    [int]$IntervalSeconds = 2,
    [string]$LogFile = "openmv_usb_monitor.log"
)

function Get-UsbSnapshot {
    $items = @()

    try {
        $items += Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
            Where-Object {
                $_.InstanceId -like "USB*" -or
                $_.FriendlyName -match "OpenMV|Camera|Serial|COM|STM"
            } |
            ForEach-Object {
                [PSCustomObject]@{
                    Type         = "PNP"
                    Status       = $_.Status
                    Class        = $_.Class
                    FriendlyName = $_.FriendlyName
                    InstanceId   = $_.InstanceId
                }
            }
    }
    catch {}

    try {
        $items += Get-CimInstance Win32_SerialPort -ErrorAction SilentlyContinue |
            ForEach-Object {
                [PSCustomObject]@{
                    Type         = "COM"
                    Status       = "OK"
                    Class        = "Ports"
                    FriendlyName = $_.Name
                    InstanceId   = $_.PNPDeviceID
                }
            }
    }
    catch {}

    return $items | Sort-Object Type, InstanceId -Unique
}

function Snapshot-ToMap {
    param($Snapshot)

    $map = @{}
    foreach ($item in $Snapshot) {
        $key = "$($item.Type)|$($item.InstanceId)"
        $map[$key] = $item
    }
    return $map
}

function Write-LogLine {
    param([string]$Text)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $line = "[$timestamp] $Text"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

Write-Host "=============================================="
Write-Host " MONITOR USB / COM - OPENMV"
Write-Host "=============================================="
Write-Host "Intervalo : $IntervalSeconds s"
Write-Host "Log       : $LogFile"
Write-Host "Detener   : Ctrl+C"
Write-Host ""

"# OpenMV USB monitor" | Set-Content -Path $LogFile
"# Inicio: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Add-Content -Path $LogFile

$anterior = Snapshot-ToMap (Get-UsbSnapshot)
Write-LogLine "Estado inicial: $($anterior.Count) dispositivos candidatos"

foreach ($key in ($anterior.Keys | Sort-Object)) {
    $d = $anterior[$key]
    Write-LogLine "PRESENTE | $($d.Status) | $($d.Class) | $($d.FriendlyName) | $($d.InstanceId)"
}

Write-Host ""
Write-Host "Monitoreando cambios..."
Write-Host ""

while ($true) {
    Start-Sleep -Seconds $IntervalSeconds

    $actual = Snapshot-ToMap (Get-UsbSnapshot)

    foreach ($key in $actual.Keys) {
        if (-not $anterior.ContainsKey($key)) {
            $d = $actual[$key]
            Write-LogLine "CONECTADO | $($d.Status) | $($d.Class) | $($d.FriendlyName) | $($d.InstanceId)"
        }
        else {
            $old = $anterior[$key]
            $new = $actual[$key]
            if ($old.Status -ne $new.Status -or $old.FriendlyName -ne $new.FriendlyName) {
                Write-LogLine "CAMBIO | $($old.Status) -> $($new.Status) | $($new.FriendlyName) | $($new.InstanceId)"
            }
        }
    }

    foreach ($key in $anterior.Keys) {
        if (-not $actual.ContainsKey($key)) {
            $d = $anterior[$key]
            Write-LogLine "DESCONECTADO | $($d.Status) | $($d.Class) | $($d.FriendlyName) | $($d.InstanceId)"
        }
    }

    $anterior = $actual
}
