import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"


class GitHubAPIClient:
    def __init__(self):
        if not GITHUB_TOKEN:
            raise ValueError("GitHub token not found. Check your .env file.")

        self.headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get(self, endpoint, params=None):
        url = f"{BASE_URL}{endpoint}"

        response = requests.get(
            url,
            headers=self.headers,
            params=params
        )

        if response.status_code != 200:
            raise Exception(
                f"GitHub API error: {response.status_code} - {response.text}"
            )

        return response.json()

    def get_paginated(self, endpoint, params=None):
        if params is None:
            params = {}

        params["per_page"] = 100

        all_data = []
        page = 1

        while True:
            params["page"] = page

            data = self.get(endpoint, params=params)

            if not data:
                break

            all_data.extend(data)
            page += 1

        return all_data