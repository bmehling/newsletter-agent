#!/bin/bash
# Newsletter Agent Cron Wrapper

# Navigate to the project directory so relative paths (token.json, .env) work
cd /Users/ben/.gemini/antigravity/scratch/agent_project

# Log start time
echo "Starting Newsletter Agent at $(date)" >> cron.log

# Run the agent using the specific python executable
# Redirect stdout and stderr to cron.log for debugging
/Users/ben/.pyenv/shims/python main.py >> cron.log 2>&1

echo "Finished at $(date)" >> cron.log
echo "----------------------------------------" >> cron.log
