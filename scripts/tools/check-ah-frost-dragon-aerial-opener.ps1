param(
    [string] $Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$componentPath = Join-Path $Root "Server/NPC/Roles/Creature/Mythic/Components/Component_AH_Instruction_Dragon_Frost_Tamed_Combat.json"
$failures = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path -LiteralPath $componentPath)) {
    $failures.Add("missing Frost Dragon tamed-combat component: $componentPath")
}

if ($failures.Count -eq 0) {
    $component = Get-Content -LiteralPath $componentPath -Raw | ConvertFrom-Json
    $entry = @($component.Content.Instructions | Where-Object {
        $sensorJson = $_.Sensor | ConvertTo-Json -Depth 100 -Compress
        $actionJson = $_.Actions | ConvertTo-Json -Depth 100 -Compress
        $sensorJson -match '"State":"\.Default"' -and
            $sensorJson -match '"State":"\.GroundCombat"' -and
            $actionJson -match '"State":"\.AirRanged"'
    })

    if ($entry.Count -ne 1) {
        $failures.Add("expected exactly one ground-to-aerial combat entry transition")
    } else {
        $timerStates = @{}
        $enteredAirRanged = $false
        foreach ($action in @($entry[0].Actions)) {
            if ($action.Type -eq "TimerStart") {
                $timerStates[$action.Name] = "Stopped"
            } elseif ($action.Type -eq "TimerRestart") {
                $timerStates[$action.Name] = "Running"
            } elseif ($action.Type -eq "State" -and $action.State -eq ".AirRanged") {
                $enteredAirRanged = $true
                break
            }
        }

        if (-not $enteredAirRanged) {
            $failures.Add("aerial combat entry never reaches .AirRanged")
        }
        foreach ($timerName in @("AH_Dragon_Frost_Air_Volley", "AH_Dragon_Frost_Air_Breath")) {
            if ($timerStates[$timerName] -ne "Running") {
                $failures.Add("$timerName must be running before .AirRanged so target acquisition opens with a ranged Frost Bolt")
            }
        }
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { [Console]::Error.WriteLine($_) }
    exit 1
}

Write-Host "Frost Dragon aerial opener contract checks passed."
