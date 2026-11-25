# Loop reproduzivel de medicao e correcao do desempenho do Canvas.
# Execute a partir da raiz: npm --prefix jogo run perf:loop
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$jogo = Join-Path $raiz 'jogo'
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$profile = Join-Path $env:TEMP ('brasalume-perf-loop-' + [guid]::NewGuid().ToString('N'))
$medidas = Join-Path $raiz 'arquivo\medidas-loop.txt'

Push-Location $jogo
try {
  npm run build
} finally {
  Pop-Location
}

$server = Start-Process -FilePath 'python.exe' -ArgumentList '-I', (Join-Path $raiz 'ferramentas\servidor_teste.py'), (Join-Path $jogo 'dist'), '8774' -PassThru -WindowStyle Hidden
$browser = Start-Process -FilePath $edge -ArgumentList '--headless=new', '--remote-debugging-port=9333', "--user-data-dir=$profile", 'about:blank' -PassThru

try {
  Start-Sleep -Seconds 2
  $pronto = $false
  for ($n = 0; $n -lt 40 -and !$pronto; $n++) {
    try { Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8774/__perf.html?z=4&s=12' -TimeoutSec 1 | Out-Null; $pronto = $true } catch { Start-Sleep -Milliseconds 250 }
  }
  if (!$pronto) { throw 'Servidor de desempenho não iniciou.' }
  $prontoNavegador = $false
  for ($n = 0; $n -lt 40 -and !$prontoNavegador; $n++) {
    try { Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:9333/json' -TimeoutSec 1 | Out-Null; $prontoNavegador = $true } catch { Start-Sleep -Milliseconds 250 }
  }
  if (!$prontoNavegador) { throw 'Edge de desempenho não iniciou.' }
  New-Item -ItemType File -Path $medidas -Force | Out-Null
  '' | Set-Content -Path $medidas -Encoding utf8

  $cenarios = @(
    @{ nome = 'zona4'; url = 'http://127.0.0.1:8774/__perf.html?z=4&cls=guerreiro&path=baluarte&lv=40&s=12&zoom=1' },
    @{ nome = 'zona8'; url = 'http://127.0.0.1:8774/__perf.html?z=8&cls=guerreiro&path=baluarte&lv=40&s=12&zoom=1' }
  )

  foreach ($c in $cenarios) {
    for ($i = 1; $i -le 3; $i++) {
      $linha = "[$($c.nome) $i] "
      $out = node (Join-Path $raiz 'ferramentas\medir.js') $c.url 12 9333 2>&1
      $texto = ($out | Out-String)
      $fpsMatch = [regex]::Match($texto, 'intervalo medio[^`r`n]*|intervalo médio[^`r`n]*')
      $worldMatch = [regex]::Match($texto, 'drawWorld medio[^`r`n]*|drawWorld médio[^`r`n]*')
      $fps = if ($fpsMatch.Success) { $fpsMatch.Value } else { $null }
      $world = if ($worldMatch.Success) { $worldMatch.Value } else { $null }
      $text = if ($fps -and $world) { "$linha$fps | $world" } else { "$linha`n$texto" }
      $text | Tee-Object -FilePath $medidas -Append
    }
  }
} finally {
  if ($browser -and !$browser.HasExited) { Stop-Process -Id $browser.Id -Force }
  if ($server -and !$server.HasExited) { Stop-Process -Id $server.Id -Force }
}
