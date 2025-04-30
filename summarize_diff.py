# import subprocess
# import openai
# import os

# # Load your OpenAI API key
# openai.api_key = os.getenv("OPENAI_API_KEY")  # Set this in your environment or shell

# # Define your main and current branch
# main_branch = "main"
# # current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
# current_branch = "test_branch"  # Replace with your current branch name

# # Check if the current branch is clean
# status = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
# if status:
#     print("Your working directory is not clean. Please commit or stash your changes.")
#     exit(1)
# # Check if the current branch is up to date with origin/main
# try:
#     subprocess.check_output(["git", "merge-base", current_branch, f"origin/{main_branch}"])
# except subprocess.CalledProcessError:
#     print(f"Your branch {current_branch} is not up to date with origin/{main_branch}. Please pull the latest changes.")
#     exit(1)
# # Check if the current branch is ahead of origin/main
# try:
#     subprocess.check_output(["git", "rev-list", "--left-only", "--count", f"origin/{main_branch}...{current_branch}"])
# except subprocess.CalledProcessError:
#     print(f"Your branch {current_branch} is ahead of origin/{main_branch}. Please push your changes.")
#     exit(1)
# # Check if the current branch is behind origin/main
# try:
#     subprocess.check_output(["git", "rev-list", "--right-only", "--count", f"{current_branch}...origin/{main_branch}"])
# except subprocess.CalledProcessError:
#     print(f"Your branch {current_branch} is behind origin/{main_branch}. Please pull the latest changes.")
#     exit(1)

# # Fetch latest changes to ensure we have origin/main
# subprocess.run(["git", "fetch", "origin", main_branch], check=True)

# # Find common ancestor (merge base)
# base_commit = subprocess.check_output(["git", "merge-base", current_branch, f"origin/{main_branch}"]).decode().strip()

# # Get the diff for just server.py
# diff = subprocess.check_output(["git", "diff", base_commit, "HEAD", "--", "server.py"]).decode("utf-8")

# if not diff.strip():
#     print("No changes detected in server.py.")
#     exit(0)

# # Truncate if too long
# MAX_INPUT = 12000
# if len(diff) > MAX_INPUT:
#     diff = diff[:MAX_INPUT] + "\n\n[Diff truncated due to length...]"

# # Use OpenAI to summarize
# response = openai.ChatCompletion.create(
#     model="gpt-4",  # Or gpt-3.5-turbo
#     messages=[
#         {"role": "system", "content": "You are an assistant that summarizes code diffs for developers."},
#         {"role": "user", "content": f"Summarize this code diff of server.py:\n\n{diff}"}
#     ],
#     temperature=0.3,
#     max_tokens=300
# )

# summary = response['choices'][0]['message']['content']
# print("\n🔍 Summary of changes in server.py:\n")
# print(summary)






import subprocess
from dotenv import load_dotenv
import os
import requests

# Load environment variables from .env file
load_dotenv()

# Load your DeepSeek API key
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# Ensure the DeepSeek API key is loaded
if not deepseek_api_key:
    print("Error: DEEPSEEK_API_KEY not found in environment variables.")
    exit(1)

# Print API key to verify it's loaded correctly
print(f"DeepSeek API Key: {deepseek_api_key}")

# Define your main and current branch
main_branch = "main"
current_branch = "test_repo_change_summary_test"  # Replace with your current branch name

# Check if the current branch is clean
try:
    status = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
    if status:
        print("Your working directory is not clean. Please commit or stash your changes.")
        exit(1)
except subprocess.CalledProcessError as e:
    print("Error: Unable to check git status.")
    print(e)
    exit(1)

# Check if the current branch is up to date with origin/main
try:
    subprocess.check_output(["git", "merge-base", current_branch, f"origin/{main_branch}"])
except subprocess.CalledProcessError:
    print(f"Your branch {current_branch} is not up to date with origin/{main_branch}. Please pull the latest changes.")
    exit(1)

# Check if the current branch is ahead of origin/main
try:
    subprocess.check_output(["git", "rev-list", "--left-only", "--count", f"origin/{main_branch}...{current_branch}"])
except subprocess.CalledProcessError:
    print(f"Your branch {current_branch} is ahead of origin/{main_branch}. Please push your changes.")
    exit(1)

# Check if the current branch is behind origin/main
try:
    subprocess.check_output(["git", "rev-list", "--right-only", "--count", f"{current_branch}...origin/{main_branch}"])
except subprocess.CalledProcessError:
    print(f"Your branch {current_branch} is behind origin/{main_branch}. Please pull the latest changes.")
    exit(1)

# Fetch latest changes to ensure we have origin/main
try:
    subprocess.run(["git", "fetch", "origin", main_branch], check=True)
except subprocess.CalledProcessError as e:
    print("Error: Unable to fetch from origin/main.")
    print(e)
    exit(1)

# Find common ancestor (merge base)
try:
    base_commit = subprocess.check_output(["git", "merge-base", current_branch, f"origin/{main_branch}"]).decode().strip()
except subprocess.CalledProcessError as e:
    print("Error: Unable to find common ancestor.")
    print(e)
    exit(1)

# Get the diff for just server.py
try:
    diff = subprocess.check_output(["git", "diff", base_commit, "HEAD", "--", "server.py"]).decode("utf-8")
    if not diff.strip():
        print("No changes detected in server.py.")
        exit(0)
except subprocess.CalledProcessError as e:
    print("Error: Unable to get diff for server.py.")
    print(e)
    exit(1)

# Truncate if too long
MAX_INPUT = 12000
if len(diff) > MAX_INPUT:
    diff = diff[:MAX_INPUT] + "\n\n[Diff truncated due to length...]"

# Print diff length and a preview
print(f"Diff Length: {len(diff)}")
print(f"Diff Preview (first 500 characters): {diff[:500]}")

# DeepSeek API request to summarize the diff
url = "https://api.deepseek.com/v1/summarize"  # Verify this endpoint with DeepSeek API documentation
headers = {
    "Authorization": f"Bearer {deepseek_api_key}",
    "Content-Type": "application/json"
}
payload = {
    "text": f"Summarize this code diff of server.py:\n\n{diff}"
}

# Make the request to DeepSeek
try:
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        summary = response.json().get("summary", "No summary available.")
        print("\n🔍 Summary of changes in server.py:\n")
        print(summary)
    else:
        print(f"Error: {response.status_code}. Could not summarize the diff.")
        print(response.text)
except requests.exceptions.RequestException as e:
    print("Error: Unable to make request to DeepSeek API.")
    print(e)
    exit(1)


