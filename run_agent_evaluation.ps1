
$tests = @(
    @{
        Id = "TC-01"
        Question = "How many employees are there in the employee master, and what is the department-wise employee count?"
    },
    @{
        Id = "TC-02"
        Question = "What is Siddharth Mehta's last working day, and is there any additional information about his resignation?"
    },
    @{
        Id = "TC-03"
        Question = "Who does Rahul Verma report to, and when did he join the company?"
    },
    @{
        Id = "TC-04"
        Question = "Where are Divya Reddy, Arjun Das, and Rohan Banerjee based, and what are their work arrangements?"
    },
    @{
        Id = "TC-05"
        Question = "Which requisitions have been on hold since 12 August, and what is the candidate pipeline for them?"
    },
    @{
        Id = "TC-06"
        Question = "Which requisitions are currently open?"
    },
    @{
        Id = "TC-07"
        Question = "What are the key business metrics for the July-September quarter, including ARR, customers, monthly burn, and runway?"
    },
    @{
        Id = "TC-08"
        Question = "Compare the April-June quarter with the July-September quarter in terms of ARR, customers, team size, monthly burn, and runway."
    },
    @{
        Id = "TC-09"
        Question = "What is the total amount and IGST charged in invoice PIS-114, and who issued the invoice?"
    },
    @{
        Id = "TC-10"
        Question = "What was the original Atlas GA release date, what is the revised date, and who changed it?"
    },
    @{
        Id = "TC-11"
        Question = "How many Jira issues are Done, In Progress, and To Do?"
    },
    @{
        Id = "TC-12"
        Question = "How many story points have been completed, how many are still open, and what is the total?"
    },
    @{
        Id = "TC-13"
        Question = "Show the number of open story points assigned to each person."
    },
    @{
        Id = "TC-14"
        Question = "What is the status of the ATLAS-5 epic, and how many open story points does it have?"
    },
    @{
        Id = "TC-15"
        Question = "Which service has recorded the highest number of incidents, and how many incidents were recorded for each service?"
    },
    @{
        Id = "TC-16"
        Question = "What was the total gross payroll for January, February, and March 2026?"
    }
)

$uri = "http://localhost:8080/api/v1/agent/ask"

$results = [System.Collections.Generic.List[object]]::new()

$total = $tests.Count
$counter = 0

foreach ($test in $tests) {

    $counter++

    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "[$counter/$total] $($test.Id)" -ForegroundColor Yellow
    Write-Host $test.Question
    Write-Host "==================================================" -ForegroundColor Cyan

    $result = $null

    try {

        $body = @{
            question = $test.Question
        } | ConvertTo-Json -Depth 10

        $response = Invoke-RestMethod `
            -Uri $uri `
            -Method POST `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec 300

        Write-Host "`nANSWER:" -ForegroundColor Green
        Write-Host $response.answer

        Write-Host "`nSOURCES:" -ForegroundColor Cyan
        Write-Host ($response.retrieval_sources -join ", ")

        Write-Host "`nCONFIDENCE:" -ForegroundColor Cyan
        Write-Host $response.confidence.level

        Write-Host "`nEVIDENCE COUNT:" -ForegroundColor Cyan
        Write-Host $response.evidence.Count

        $result = [PSCustomObject]@{
            TestCase        = $test.Id
            Question        = $test.Question
            ApiStatus       = "SUCCESS"
            Sources         = $response.retrieval_sources
            Answer          = $response.answer
            Evidence        = $response.evidence
            Confidence      = $response.confidence
            Limitations     = $response.limitations
            HttpStatus      = 200
            Error           = $null
        }

    }
    catch {

        $errorMessage = $_.Exception.Message
        $httpStatus = $null

        if ($_.Exception.Response) {
            try {
                $httpStatus = [int]$_.Exception.Response.StatusCode
            }
            catch {
                $httpStatus = $null
            }
        }

        Write-Host "`nREQUEST FAILED:" -ForegroundColor Red
        Write-Host $errorMessage

        $result = [PSCustomObject]@{
            TestCase        = $test.Id
            Question        = $test.Question
            ApiStatus       = "FAILED"
            Sources         = @()
            Answer          = $null
            Evidence        = @()
            Confidence      = $null
            Limitations     = @()
            HttpStatus      = $httpStatus
            Error           = $errorMessage
        }
    }

    $results.Add($result)

    Write-Host "`nCompleted $counter of $total tests." -ForegroundColor Gray

    # Small pause between requests
    Start-Sleep -Seconds 1
}

# --------------------------------------------------
# FINAL SUMMARY
# --------------------------------------------------

$passed = @($results | Where-Object {
    $_.ApiStatus -eq "SUCCESS"
}).Count

$failed = @($results | Where-Object {
    $_.ApiStatus -eq "FAILED"
}).Count

Write-Host "`n==================================================" -ForegroundColor Magenta
Write-Host "               FINAL TEST SUMMARY" -ForegroundColor Magenta
Write-Host "==================================================" -ForegroundColor Magenta

$results |
    Select-Object TestCase, ApiStatus, HttpStatus, Confidence |
    Format-Table -AutoSize -Wrap

Write-Host "`nTotal Questions : $total"
Write-Host "API Success     : $passed" -ForegroundColor Green
Write-Host "API Failed      : $failed" -ForegroundColor Red

# --------------------------------------------------
# SAVE COMPLETE RESULTS
# --------------------------------------------------

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$outputFile = ".\agent_evaluation_$timestamp.json"

$results |
    ConvertTo-Json -Depth 30 |
    Set-Content -Path $outputFile -Encoding UTF8

Write-Host "`nFull evaluation saved to:" -ForegroundColor Yellow
Write-Host (Resolve-Path $outputFile)

Write-Host "`nAll API requests completed." -ForegroundColor Green
