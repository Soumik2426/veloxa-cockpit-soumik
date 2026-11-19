
# ==================================================
# VELOXA CXO COCKPIT - PRECISION AGENT EVALUATION
# EVALUATION SET 2
# ==================================================


$tests = @(
    @{
        Id = "TC-01"
        Question = "What is Siddharth Mehta's last working day, and is there any additional information about his resignation?"
    },
    @{
        Id = "TC-02"
        Question = "Who does Rahul Verma report to, and when did he join the company?"
    },
    @{
        Id = "TC-03"
        Question = "Where are Divya Reddy, Arjun Das, and Rohan Banerjee based, and what are their work arrangements?"
    },
    @{
        Id = "TC-04"
        Question = "Which requisitions have been on hold since 12 August, and what is the candidate pipeline for each? Include any relevant cancelled interview details."
    },
    @{
        Id = "TC-05"
        Question = "Compare the April-June quarter with the July-September quarter in terms of ARR, customers, team size, monthly burn, and runway. State both values and the change for each metric."
    },
    @{
        Id = "TC-06"
        Question = "What is the total amount and IGST charged in invoice PIS-114, and who issued the invoice? Also explain the subtotal and tax calculation."
    },
    @{
        Id = "TC-07"
        Question = "What was the original Atlas GA release date, what is the revised release date, and who changed it? Include the date on which the change was made."
    },
    @{
        Id = "TC-08"
        Question = "How many story points have been completed, how many are still open, and what is the total? Show the calculation using the relevant Jira statuses."
    },
    @{
        Id = "TC-09"
        Question = "What is the status of the ATLAS-5 epic, and how many open story points does it have? If its status is unavailable, explicitly explain why."
    },
    @{
        Id = "TC-10"
        Question = "What was the total gross payroll for January, February, and March 2026? Provide the monthly gross payroll and the overall Q1 total."
    },
    @{
        Id = "TC-11"
        Question = "How many employees are present in the HR master, and how are they distributed across departments? Provide the total employee count and the count for each department."
    },
    @{
        Id = "TC-12"
        Question = "Which job requisitions are currently open? For each requisition, provide its requisition ID, job title, opening date, and the number of candidates currently in its pipeline."
    },
    @{
        Id = "TC-13"
        Question = "According to the July-September 2026 board update, what are the company's ARR, total customer count, monthly burn, team size, and runway?"
    },
    @{
        Id = "TC-14"
        Question = "How many Jira issues are there in total, and how are they distributed across Done, In Progress, and To Do statuses? Provide the status-wise counts and verify that they add up to the total."
    },
    @{
        Id = "TC-15"
        Question = "Show the number of open story points assigned to each employee. Include the assignee identifiers and their corresponding names, and provide the total open story points across all assignees listed."
    },
    @{
        Id = "TC-16"
        Question = "Which service has the highest number of incidents between August and October 2026? Provide the incident count for each service, identify the incident IDs associated with the service having the highest count, and state the overall incident total."
    },
    @{
        Id = "TC-17"
        Question = "How many incidents occurred in each month from August to October 2026? Provide the monthly incident counts and the overall total."
    },
    @{
        Id = "TC-18"
        Question = "When did the SEV1 incidents occur, and who handled each of them? Include the incident IDs, dates, affected service, and responder."
    },
    @{
        Id = "TC-19"
        Question = "Which incident lasted the longest, and how long did it run? Provide the incident ID, start timestamp, end timestamp, and total duration."
    },
    @{
        Id = "TC-20"
        Question = "What was the total general ledger spend for each cost centre between April and September 2026? Provide the cost centre-wise amounts and the overall total."
    },
    @{
        Id = "TC-21"
        Question = "How many commits did Priya make in total? Check whether she appears under multiple author email addresses and combine the commits belonging to her across those identities."
    },
    @{
        Id = "TC-22"
        Question = "What was the total amount spent on the September summit? Identify the individual vendor transactions, reconcile different spellings of the same vendor, and exclude expenses unrelated to the summit."
    }
)

# ==================================================
# CONFIGURATION
# ==================================================

$uri = "http://localhost:8080/api/v1/agent/ask"

$outputDirectory = ".\agent_evaluation"

if (-not (Test-Path $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$results = [System.Collections.Generic.List[object]]::new()

$total = $tests.Count
$counter = 0

# ==================================================
# EXECUTE TEST CASES
# ==================================================

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
        Write-Host "Level: $($response.confidence.level)"
        Write-Host "Reason: $($response.confidence.rationale)"

        Write-Host "`nEVIDENCE COUNT:" -ForegroundColor Cyan
        Write-Host @($response.evidence).Count

        Write-Host "`nLIMITATIONS:" -ForegroundColor Cyan

        if (@($response.limitations).Count -eq 0) {
            Write-Host "None"
        }
        else {
            $response.limitations | ForEach-Object {
                Write-Host "- $_"
            }
        }

        $result = [PSCustomObject]@{
            TestCase    = $test.Id
            Question    = $test.Question
            ApiStatus   = "SUCCESS"
            Sources     = $response.retrieval_sources
            Answer      = $response.answer
            Evidence    = $response.evidence
            Confidence  = $response.confidence
            Limitations = $response.limitations
            HttpStatus  = 200
            Error       = $null
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
            TestCase    = $test.Id
            Question    = $test.Question
            ApiStatus   = "FAILED"
            Sources     = @()
            Answer      = $null
            Evidence    = @()
            Confidence  = $null
            Limitations = @()
            HttpStatus  = $httpStatus
            Error       = $errorMessage
        }
    }

    $results.Add($result)

    Write-Host "`nCompleted $counter of $total tests." -ForegroundColor Gray

    Start-Sleep -Seconds 1
}

# ==================================================
# FINAL SUMMARY
# ==================================================

$passed = @(
    $results | Where-Object { $_.ApiStatus -eq "SUCCESS" }
).Count

$failed = @(
    $results | Where-Object { $_.ApiStatus -eq "FAILED" }
).Count

Write-Host "`n==================================================" -ForegroundColor Magenta
Write-Host "          PRECISION EVALUATION SUMMARY" -ForegroundColor Magenta
Write-Host "==================================================" -ForegroundColor Magenta

$results |
    Select-Object TestCase, ApiStatus, HttpStatus,
        @{Name = "Confidence"; Expression = {
            if ($_.Confidence) { $_.Confidence.level }
            else { "N/A" }
        }} |
    Format-Table -AutoSize -Wrap

Write-Host "`nTotal Questions : $total"
Write-Host "API Success     : $passed" -ForegroundColor Green
Write-Host "API Failed      : $failed" -ForegroundColor Red

# ==================================================
# SAVE COMPLETE RESULTS
# ==================================================

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$outputFile = Join-Path $outputDirectory "precision_evaluation_$timestamp.json"

$results |
    ConvertTo-Json -Depth 30 |
    Set-Content -Path $outputFile -Encoding UTF8

Write-Host "`nFull evaluation saved to:" -ForegroundColor Yellow
Write-Host (Resolve-Path $outputFile)

Write-Host "`nAll evaluation requests completed." -ForegroundColor Green
