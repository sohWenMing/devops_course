#!/usr/bin/env python3
"""
FlowForge Database Cleanup

Resets the FlowForge database to a clean state by removing all task data.
Requires --confirm flag as a safety measure.

Usage:
    python cleanup.py --confirm        # Delete all tasks
    python cleanup.py                  # Shows warning, does nothing

Environment Variables:
    DATABASE_URL  - PostgreSQL connection string
                    Example: postgres://user:pass@localhost:5432/flowforge

Exit Codes:
    0 - Success (or no action taken without --confirm)
    1 - Failure (connection error, missing config, etc.)
"""

# TODO (Lab 04, Exercise 4b): Implement this script
#
# Requirements:
# 1. Read DATABASE_URL from environment variable
# 2. REQUIRE --confirm flag (safety measure!)
#    - Without --confirm: print a warning and exit 0 (no action)
#    - With --confirm: proceed with cleanup
# 3. Connect to PostgreSQL using psycopg2
# 4. Delete all data from the tasks table (TRUNCATE or DELETE FROM)
# 5. Print what was deleted: "Deleted N tasks from database"
# 6. Handle errors gracefully
# 7. Return exit code 0 on success, 1 on failure
#
# Why the --confirm flag?
# - This script deletes data. Running it by accident in production would be catastrophic.
# - The --confirm flag forces the user to be intentional about data deletion.
# - In CI/CD pipelines, scripts are often run automatically. A safety flag
#   prevents accidental data loss if the script ends up in a pipeline by mistake.
#
# Hints:
# - Use argparse for the --confirm flag
# - Use os.environ to read DATABASE_URL
# - Consider counting rows before deleting to report what was removed
# - Use psycopg2 for database operations

import sys


def main():
    print("cleanup.py: Not yet implemented -- complete Lab 04, Exercise 4b")
    sys.exit(1)


if __name__ == "__main__":
    main()
