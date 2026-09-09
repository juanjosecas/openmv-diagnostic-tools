# ============================================================
# 09_diagnostico_windows_openmv.ps1
#
# OBJETIVO:
# Relevar desde Windows posibles problemas de comunicación
# entre una cámara OpenMV y la computadora.
#
# NO instala nada.
# NO modifica drivers.
# NO reinicia dispositivos.
# ============================================================

Clear-Host

function Titulo {
    param([string]$Texto)
    Write-Host ""
    Write-Host "----------------------------------------------"
    Write-Host $Texto
    Write-Host "----------------------------------------------"
}

Write-Host "=============================================="
Write-Host " DIAGNOSTICO WINDOWS - OPENMV / USB"
Write-Host "=============================================="

Titulo "[1] INFORMACION DE WINDOWS"
try {
    $windows = Get-CimInstance Win32_OperatingSystem
    Write-Host "Equipo       :" $env:COMPUTERNAME
    Write-Host "Usuario      :" $env:USERNAME
    Write-Host "Windows      :" $windows.Caption
    Write-Host "Version      :" $windows.Version
    Write-Host "Build        :" $windows.BuildNumber
    Write-Host "Arquitectura :" $windows.OSArchitecture
}
catch {
    Write-Host "ERROR obteniendo informacion de Windows:"
    Write-Host $_
}

Titulo "[2] DISPOSITIVOS USB PRESENTES"
try {
    $usb = Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -like "USB*" }
    if (-not $usb) {
        Write-Host "WARNING: no se encontraron dispositivos USB."
    }
    else {
        $usb | Sort-Object Class, FriendlyName | Format-Table Status, Class, FriendlyName, InstanceId -AutoSize
    }
}
catch {
    Write-Host "ERROR leyendo dispositivos USB:"
    Write-Host $_
}

Titulo "[3] CANDIDATOS OPENMV / CAMARA / SERIAL"
try {
    $candidatos = Get-PnpDevice -PresentOnly | Where-Object {
        $_.FriendlyName -match "OpenMV|Camera|Serial|COM|STM|USB" -or
        $_.Manufacturer -match "OpenMV|STMicroelectronics"
    }

    if (-not $candidatos) {
        Write-Host "WARNING: no se encontraron dispositivos candidatos."
    }
    else {
        $candidatos | Sort-Object Class, FriendlyName | Format-Table Status, Class, FriendlyName, Manufacturer, InstanceId -AutoSize
    }
}
catch {
    Write-Host "ERROR buscando dispositivos candidatos:"
    Write-Host $_
}

Titulo "[4] PUERTOS COM"
try {
    $puertos = Get-CimInstance Win32_SerialPort
    if (-not $puertos) {
        Write-Host "No hay puertos COM activos."
    }
    else {
        $puertos | Select-Object DeviceID, Name, Description, Manufacturer, PNPDeviceID | Format-Table -AutoSize
    }
}
catch {
    Write-Host "ERROR leyendo puertos COM:"
    Write-Host $_
}

Titulo "[5] DISPOSITIVOS PNP CON ERROR"
try {
    $errores = Get-PnpDevice | Where-Object { $_.Status -ne "OK" -and $_.Status -ne "Unknown" }
    if (-not $errores) {
        Write-Host "OK: Windows no informa dispositivos PnP con error."
    }
    else {
        $errores | Format-Table Status, Class, FriendlyName, InstanceId -AutoSize
    }
}
catch {
    Write-Host "ERROR revisando dispositivos:"
    Write-Host $_
}

Titulo "[6] DRIVERS USB / SERIAL / CAMARA"
try {
    $drivers = Get-CimInstance Win32_PnPSignedDriver | Where-Object {
        $_.DeviceName -match "OpenMV|USB|Serial|Camera|STM|COM"
    } | Select-Object DeviceName, Manufacturer, DriverProviderName, DriverVersion, DriverDate, InfName

    if (-not $drivers) {
        Write-Host "No se encontraron drivers candidatos."
    }
    else {
        $drivers | Sort-Object DeviceName | Format-Table -AutoSize
    }
}
catch {
    Write-Host "ERROR leyendo drivers:"
    Write-Host $_
}

Titulo "[7] CONTROLADORES USB"
try {
    Get-CimInstance Win32_USBController | Select-Object Name, Manufacturer, Status, DeviceID | Format-Table -AutoSize
}
catch {
    Write-Host "ERROR leyendo controladores USB:"
    Write-Host $_
}

Titulo "[8] HUBS USB"
try {
    Get-CimInstance Win32_USBHub | Select-Object Name, Status, PNPDeviceID | Format-Table -AutoSize
}
catch {
    Write-Host "ERROR leyendo hubs USB:"
    Write-Host $_
}

Titulo "[9] EVENTOS RECIENTES USB / PNP"
$inicioEventos = (Get-Date).AddHours(-24)
try {
    $eventos = Get-WinEvent -FilterHashtable @{ LogName = "System"; StartTime = $inicioEventos } -ErrorAction SilentlyContinue |
        Where-Object {
            $_.ProviderName -match "Kernel-PnP|USB|DriverFrameworks" -or
            $_.Message -match "USB|OpenMV|device|dispositivo"
        } |
        Select-Object -First 50 TimeCreated, Id, ProviderName, LevelDisplayName, Message

    if (-not $eventos) {
        Write-Host "No se encontraron eventos USB/PnP relevantes en las ultimas 24 h."
    }
    else {
        foreach ($evento in $eventos) {
            Write-Host ""
            Write-Host "Fecha     :" $evento.TimeCreated
            Write-Host "ID        :" $evento.Id
            Write-Host "Proveedor :" $evento.ProviderName
            Write-Host "Nivel     :" $evento.LevelDisplayName
            Write-Host "Mensaje   :" $evento.Message
            Write-Host "----------------------------------------------"
        }
    }
}
catch {
    Write-Host "ERROR leyendo Event Viewer:"
    Write-Host $_
}

Titulo "[10] PLAN Y CONFIGURACION DE ENERGIA USB"
try {
    powercfg /GETACTIVESCHEME
    Write-Host ""
    powercfg /QUERY SCHEME_CURRENT SUB_USB
}
catch {
    Write-Host "No se pudo consultar la configuracion de energia USB."
}

Titulo "[11] POWER MANAGEMENT DE DISPOSITIVOS USB"
try {
    $powerDevices = Get-CimInstance -Namespace root/wmi -ClassName MSPower_DeviceEnable -ErrorAction Stop
    foreach ($dev in $powerDevices) {
        if ($dev.InstanceName -match "USB") {
            Write-Host "Dispositivo:" $dev.InstanceName
            Write-Host "Power management habilitado:" $dev.Enable
            Write-Host ""
        }
    }
}
catch {
    Write-Host "WARNING: no se pudo consultar MSPower_DeviceEnable."
    Write-Host "Puede requerir ejecutar PowerShell como Administrador."
}

Titulo "[12] RESUMEN DE QUE MIRAR"
Write-Host "1. Si OpenMV aparece entre los dispositivos USB."
Write-Host "2. Si desaparece durante el fallo."
Write-Host "3. Si Windows informa Status distinto de OK."
Write-Host "4. Si cambia o desaparece el puerto COM."
Write-Host "5. Si aparecen eventos Kernel-PnP en el momento del cuelgue."
Write-Host "6. Si hay administracion de energia USB activa."
Write-Host "7. DriverVersion y DriverDate de dispositivos candidatos."

Write-Host ""
Write-Host "=============================================="
Write-Host " FIN DEL DIAGNOSTICO"
Write-Host "=============================================="
