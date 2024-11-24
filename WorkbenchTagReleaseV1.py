import requests
from requests.auth import HTTPBasicAuth

# Read the organization name and version number from the configuration file
def read_config(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            name, value = line.strip().split('=')
            config[name] = value
    return config

# Read config values from config.txt
config = read_config('config.txt')
#ORGANIZATION = config.get('organization')
user = config.get('organization')
NEW_TAG = 'v' + config.get('version')
COMMIT_MESSAGE = 'Tagging version ' + NEW_TAG

# Your GitHub username and personal access token (PAT) read from config.txt
GITHUB_USERNAME = config.get('GITHUB_USERNAME')
GITHUB_PAT = config.get('GITHUB_PAT')

# Authenticate with GitHub
auth = HTTPBasicAuth(GITHUB_USERNAME, GITHUB_PAT)

# Headers for GitHub API
headers = {
    'Accept': 'application/vnd.github.v3+json'
}

def get_repositories(org):
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

# url = f'https://api.github.com/repos/{repo_full_name}/git/tags'
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
        print(response.json())  # Debug: show response content
        response.raise_for_status()
        return response.json()['sha']
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} for url: {url}")
        print(f"Response content: {response.content.decode()}")
        return None
    except Exception as err:
        print(f"Other error occurred: {err}")
        return None

def create_tag_ref(repo_full_name, tag):
    url = f'https://api.github.com/repos/{repo_full_name}/git/refs'
    data = {
            'ref': f'refs/tags/{tag}',
            'sha': get_latest_commit_sha(repo_full_name)
        }
    try:
            response = requests.post(url, json=data, headers=headers, auth=auth)
            response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} for url: {url}")
            print(f"Response content: {response.content.decode()}")
    except Exception as err:
            print(f"Other error occurred: {err}")

def tag_repositories(org, new_tag, commit_message):
    repos = get_repositories(org)
    for repo in repos:
        repo_full_name = repo['full_name']
        sha = get_latest_commit_sha(repo_full_name)
        print(f"Tagging repository: {repo_full_name} sha value: {sha} rep fullname= {repo_full_name}")
        if sha:
            create_tag_object(repo_full_name, new_tag, sha, commit_message)
            create_tag_ref(repo_full_name, new_tag)
            print(f"Tagged {repo_full_name} with {new_tag}")
        else:
            print(f"Skipping {repo_full_name}: No commits found")

# Run the script
tag_repositories(user, NEW_TAG, COMMIT_MESSAGE)
