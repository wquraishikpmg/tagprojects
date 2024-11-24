import requests
from requests.auth import HTTPBasicAuth
import json

# Function to read the configuration values from a file and handle comments
def read_config(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                name, value = line.split('=', 1)
                config[name.strip()] = value.strip()
    return config

# Read config values from config.txt
config = read_config('config.txt')
USER = config.get('organization')  # Since it's a user, we'll use the 'organization' key to hold the username
NEW_TAG = 'v' + config.get('version')
COMMIT_MESSAGE = 'Tagging version ' + NEW_TAG
RELEASE_NAME = 'Release ' + config.get('version')
RELEASE_BODY = 'This is the release description for version ' + config.get('version')
GITHUB_USERNAME = config.get('GITHUB_USERNAME')
GITHUB_PAT = config.get('GITHUB_PAT')

# Authenticate with GitHub
auth = HTTPBasicAuth(GITHUB_USERNAME, GITHUB_PAT)

# Headers for GitHub API
headers = {
    'Accept': 'application/vnd.github.v3+json'
}

def get_repositories(user):
    url = f'https://api.github.com/users/{user}/repos'
    try:
        response = requests.get(url, headers=headers, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Print the error
        return []
    except Exception as err:
        print(f"Other error occurred: {err}")  # Print any other error
        return []

def get_latest_commit_sha(repo_full_name):
    url = f'https://api.github.com/repos/{repo_full_name}/commits'
    response = requests.get(url, headers=headers, auth=auth)
    response.raise_for_status()
    commits = response.json()
    if commits:
        return commits[0]['sha']
    return None

def tag_exists(repo_full_name, tag):
    url = f'https://api.github.com/repos/{repo_full_name}/git/refs/tags/{tag}'
    response = requests.get(url, headers=headers, auth=auth)
    return response.status_code == 200

def create_tag_object(repo_full_name, tag, sha, message):
    url = f'https://api.github.com/repos/{repo_full_name}/git/tags'
    data = {
        'tag': tag,
        'message': message,
        'object': sha,
        'type': 'commit',
        'tagger': {
            'name': GITHUB_USERNAME,
            'email': f"{GITHUB_USERNAME}@users.noreply.github.com",
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers, auth=auth)
        response.raise_for_status()
        return response.json()['sha']
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} for url: {url}")
        print(f"Response content: {response.content.decode()}")
        return None
    except Exception as err:
        print(f"Other error occurred: {err}")
        return None

def create_tag_ref(repo_full_name, tag, tag_sha):
    url = f'https://api.github.com/repos/{repo_full_name}/git/refs'
    data = {
        'ref': f'refs/tags/{tag}',
        'sha': tag_sha
    }
    try:
        response = requests.post(url, json=data, headers=headers, auth=auth)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} for url: {url}")
        print(f"Response content: {response.content.decode()}")
    except Exception as err:
        print(f"Other error occurred: {err}")

def create_release(repo_full_name, tag, release_name, release_body):
    url = f'https://api.github.com/repos/{repo_full_name}/releases'
    data = {
        'tag_name': tag,
        'name': release_name,
        'body': release_body,
        'draft': False,
        'prerelease': False
    }
    try:
        response = requests.post(url, json=data, headers=headers, auth=auth)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} for url: {url}")
        print(f"Response content: {response.content.decode()}")
    except Exception as err:
        print(f"Other error occurred: {err}")

def tag_repositories(user, new_tag, commit_message, release_name, release_body):
    repos = get_repositories(user)
    if not repos:
        print("No repositories found or error accessing the user.")
        return

    for repo in repos:
        repo_full_name = repo['full_name']
        print(f"Tagging repository: {repo_full_name}")
        
        # Check if the tag already exists
        if tag_exists(repo_full_name, new_tag):
            print(f"Tag {new_tag} already exists for repository {repo_full_name}. Skipping tagging.")
            continue
        
        sha = get_latest_commit_sha(repo_full_name)
        if sha:
            print(f"Tagging repository: {repo_full_name} sha value: {sha} rep fullname= {repo_full_name}")
            tag_sha = create_tag_object(repo_full_name, new_tag, sha, commit_message)
            if tag_sha:
                create_tag_ref(repo_full_name, new_tag, tag_sha)
                create_release(repo_full_name, new_tag, release_name, release_body)
                print(f"Tagged {repo_full_name} with {new_tag}")
            else:
                print(f"Failed to create tag object for {repo_full_name}")
        else:
            print(f"Skipping {repo_full_name}: No commits found")

# Run the script
tag_repositories(USER, NEW_TAG, COMMIT_MESSAGE, RELEASE_NAME, RELEASE_BODY)
