# PowerShell script to run Salesforce Schema Pipeline with progress monitoring

Write-Host "🚀 Starting Salesforce Schema Pipeline with Enhanced Progress Monitoring" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "⏰ Start Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Cyan

Write-Host "📋 Pipeline Configuration:" -ForegroundColor Green
Write-Host "  • Org Alias: DEVNEW" -ForegroundColor White
Write-Host "  • Output Directory: ./output" -ForegroundColor White
Write-Host "  • Features: Stats, Automation, Metadata, JSONL, Pinecone" -ForegroundColor White
Write-Host "  • Throttle: 100ms between API calls" -ForegroundColor White
Write-Host "  • Retries: 3 per object" -ForegroundColor White
Write-Host "=" * 80 -ForegroundColor Cyan

# Start the pipeline with real-time output
$startTime = Get-Date
$lastProgressTime = $startTime

try {
    # Run the pipeline command
    $process = Start-Process -FilePath "python" -ArgumentList @(
        "-u",
        "src/pipeline/build_schema_library_end_to_end.py",
        "--org-alias", "DEVNEW",
        "--output", "./output",
        "--with-stats",
        "--with-automation",
        "--with-metadata",
        "--emit-jsonl",
        "--push-to-pinecone",
        "--clean-output",
        "--throttle-ms", "100",
        "--retries", "3"
    ) -NoNewWindow -PassThru -RedirectStandardOutput "pipeline_output.log" -RedirectStandardError "pipeline_error.log"

    Write-Host "🔄 Pipeline is running..." -ForegroundColor Yellow
    Write-Host "📝 Output is being logged to pipeline_output.log" -ForegroundColor Cyan
    Write-Host "⚠️  Errors are being logged to pipeline_error.log" -ForegroundColor Cyan
    
    # Monitor the process
    while (-not $process.HasExited) {
        Start-Sleep -Seconds 30  # Check every 30 seconds
        
        $currentTime = Get-Date
        $elapsed = $currentTime - $startTime
        $minutes = [math]::Floor($elapsed.TotalMinutes)
        $seconds = [math]::Floor($elapsed.TotalSeconds) % 60
        
        Write-Host "⏱️  Time elapsed: ${minutes}m ${seconds}s" -ForegroundColor Yellow
        
        # Show last few lines of output
        if (Test-Path "pipeline_output.log") {
            $lastLines = Get-Content "pipeline_output.log" -Tail 3
            if ($lastLines) {
                Write-Host "📊 Recent output:" -ForegroundColor Gray
                $lastLines | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            }
        }
        
        Write-Host "---" -ForegroundColor DarkGray
    }
    
    # Show final results
    $endTime = Get-Date
    $totalTime = $endTime - $startTime
    $minutes = [math]::Floor($totalTime.TotalMinutes)
    $seconds = [math]::Floor($totalTime.TotalSeconds) % 60
    
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "✅ Pipeline completed!" -ForegroundColor Green
    Write-Host "⏰ End Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
    Write-Host "⏱️  Total Time: ${minutes}m ${seconds}s" -ForegroundColor Yellow
    Write-Host "🔢 Exit Code: $($process.ExitCode)" -ForegroundColor Yellow
    Write-Host "=" * 80 -ForegroundColor Cyan
    
    if ($process.ExitCode -eq 0) {
        Write-Host "🎉 Success! Your Salesforce schema has been processed and uploaded to Pinecone." -ForegroundColor Green
        Write-Host "📁 Check the ./output directory for generated files." -ForegroundColor Cyan
        Write-Host "🤖 You can now run the Streamlit chatbot to test the RAG system!" -ForegroundColor Cyan
        
        # Show final output
        if (Test-Path "pipeline_output.log") {
            Write-Host "📋 Final Pipeline Output:" -ForegroundColor Green
            Get-Content "pipeline_output.log" -Tail 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
        }
    } else {
        Write-Host "❌ Pipeline failed. Check the logs for errors." -ForegroundColor Red
        if (Test-Path "pipeline_error.log") {
            Write-Host "📋 Error Log:" -ForegroundColor Red
            Get-Content "pipeline_error.log" -Tail 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        }
    }
    
} catch {
    Write-Host "❌ Error running pipeline: $_" -ForegroundColor Red
    exit 1
}
