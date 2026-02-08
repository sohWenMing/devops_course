#!/usr/bin/env python3
"""
FlowForge Database Seeder

Populates the FlowForge PostgreSQL database with test data.
Useful for development and testing.

Usage:
    python seed-database.py                  # Create 20 test tasks (default)
    python seed-database.py --count 50       # Create 50 test tasks
    python seed-database.py --clear          # Clear existing data before seeding
    python seed-database.py --clear --count 100

Environment Variables:
    DATABASE_URL  - PostgreSQL connection string
                    Example: postgres://user:pass@localhost:5432/flowforge

Exit Codes:
    0 - Success
    1 - Failure (connection error, missing config, etc.)
"""

# TODO (Lab 04, Exercise 4b): Implement this script
#
# Requirements:
# 1. Read DATABASE_URL from environment variable
# 2. Connect to PostgreSQL using psycopg2
# 3. Accept --count N argument (default 20)
# 4. Accept --clear flag to truncate tasks table before seeding
# 5. Insert N tasks with varied:
#    - Titles (realistic task names)
#    - Descriptions
#    - Statuses (mix of: pending, processing, completed, failed)
# 6. Print a summary: "Created N tasks (X pending, Y processing, Z completed, W failed)"
# 7. Handle errors gracefully (no stack traces for connection failures)
# 8. Return exit code 0 on success, 1 on failure
#
# Hints:
# - Use argparse for command-line arguments
# - Use os.environ to read DATABASE_URL
# - Use psycopg2 for PostgreSQL (pip install psycopg2-binary)
# - Consider using random or faker for generating test data
#
# Example task data:
#   title: "Process monthly report"
#   description: "Generate and email the monthly sales report"
#   status: "pending"
#   created_at: current timestamp

import sys


def main():
    print("seed-database.py: Not yet implemented -- complete Lab 04, Exercise 4b")
    sys.exit(1)


if __name__ == "__main__":
    main()
