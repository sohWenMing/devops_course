#!/usr/bin/env python3
"""
FlowForge Health Check

Verifies that all FlowForge services are running and healthy.
Checks: api-service HTTP endpoint, PostgreSQL connectivity.

Usage:
    python healthcheck.py

Environment Variables:
    DATABASE_URL  - PostgreSQL connection string
    API_URL       - api-service base URL (default: http://localhost:8080)

Exit Codes:
    0 - All services healthy
    1 - One or more services unhealthy
"""

# TODO (Lab 04, Exercise 4b): Implement this script
#
# Requirements:
# 1. Check api-service health:
#    - HTTP GET to {API_URL}/health
#    - Expect 200 status code
#    - Use a reasonable timeout (e.g., 5 seconds)
#    - Report: "api-service: UP" or "api-service: DOWN (reason)"
#
# 2. Check PostgreSQL health:
#    - Connect to DATABASE_URL
#    - Execute a simple query (e.g., SELECT 1)
#    - Report: "postgresql: UP" or "postgresql: DOWN (reason)"
#
# 3. Print a summary:
#    - List each service and its status
#    - Overall: "All services healthy" or "X of Y services unhealthy"
#
# 4. Exit code:
#    - 0 if ALL services are healthy
#    - 1 if ANY service is unhealthy
#
# 5. Handle errors gracefully:
#    - Connection refused → report DOWN, don't crash
#    - Timeout → report DOWN with timeout info
#    - Missing env vars → report error and exit 1
#
# Hints:
# - Use requests library for HTTP checks (pip install requests)
# - Use psycopg2 for PostgreSQL checks
# - Use os.environ for configuration
# - Set timeouts on all network calls

import sys


def main():
    print("healthcheck.py: Not yet implemented -- complete Lab 04, Exercise 4b")
    sys.exit(1)


if __name__ == "__main__":
    main()
