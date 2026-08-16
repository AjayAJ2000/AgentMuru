$ErrorActionPreference = "Stop"
Write-Error "The deterministic Go helper process in supervisor_test.go is the executable fixture. This file documents that production supervision does not invoke an unverified script."
exit 2
