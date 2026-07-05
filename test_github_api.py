import os
from dotenv import load_dotenv
from extractor.github_api import GitHubAPIClient

load_dotenv()

owner = os.getenv("GITHUB_OWNER")
repo = os.getenv("GITHUB_REPOSITORY")

client = GitHubAPIClient()

repository = client.get(f"/repos/{owner}/{repo}")

print("Connected to GitHub successfully!")
print("Repository name:", repository["name"])
print("Owner:", repository["owner"]["login"])
print("Default branch:", repository["default_branch"])