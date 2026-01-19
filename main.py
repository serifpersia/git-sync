import os
import json
import requests
import argparse
from dulwich import porcelain, repo
from dulwich.client import get_transport_and_path
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime, timezone

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def get_repos_from_github(username, include_forks=False):
    repos_info = {}
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            for repo_data in data:
                if not include_forks and repo_data['fork']:
                    continue
                repos_info[repo_data['name']] = {
                    'clone_url': repo_data['clone_url'],
                    'pushed_at': repo_data['pushed_at']
                }
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repos for {username}: {e}")
            return {}
    return repos_info

def clone_repo(repo_url, target_path, depth=0):
    print(f"Cloning {repo_url}...")
    try:
        porcelain.clone(repo_url, target_path, depth=depth if depth > 0 else None)
        print(f"Successfully cloned {repo_url}")
        return True
    except Exception as e:
        print(f"Error cloning {repo_url}: {e}")
        return False

def update_repo(repo_path, remote_url=None):
    try:
        r = repo.Repo(repo_path)
    except repo.NotGitRepository:
        print(f"Skipping {repo_path}: not a git repository.")
        return False
    
    status = porcelain.status(r)
    if any(status.staged.values()) or status.unstaged:
        print(f"Discarding uncommitted changes in {repo_path} to prioritize remote state...")
        porcelain.reset(r, 'hard')

    print(f"Checking for updates in {repo_path}...")
    try:
        if remote_url is None:
            config = r.get_config()
            try:
                remote_url = config[(b'remote "origin"', b'url')].decode('utf-8')
            except KeyError:
                print(f"Warning: No remote 'origin' URL found for {repo_path}. Skipping update.")
                return False

        client, relative_path = get_transport_and_path(remote_url)
        remote_refs = client.fetch(relative_path, r)
        
        has_changes = False
        for key, value in remote_refs.refs.items():
            if key.startswith(b'refs/heads/'):
                try:
                    old_sha = r.refs[key]
                    if old_sha != value:
                        has_changes = True
                        r.refs.set_if_equals(key, old_sha, value)
                except KeyError:
                    has_changes = True
                    r.refs[key] = value
        
        if has_changes:
            print(f"Successfully updated {repo_path}")
        else:
            print(f"{repo_path} is up to date.")
        return True

    except Exception as e:
        print(f"Error updating {repo_path}: {e}")
        return False

def save_config(config, path):
    with open(path, 'w') as f:
        json.dump(config, f, indent=4)

def prompt_for_username(config):
    while True:
        username = input("Please enter your GitHub username to sync repositories: ")
        if username:
            config['github_usernames'] = [username]
            return config
        print("Username cannot be empty.")

def main():
    parser = argparse.ArgumentParser(description="A tool to back up your git repositories.")
    parser.add_argument('-b', '--backup-dir', dest='backup_dir_opt', nargs='+', help="Directory where repositories will be backed up. Handles paths with spaces.")
    args = parser.parse_args()

    backup_dir = ' '.join(args.backup_dir_opt) if args.backup_dir_opt else './repos'
    
    if not os.path.exists(backup_dir):
        print(f"Backup directory '{backup_dir}' not found. Creating it...")
        os.makedirs(backup_dir)

    config_path = os.path.join(backup_dir, 'config.json')
    
    config = {
        "github_usernames": [],
        "include_forks": False,
        "clone_depth": 0,
        "repositories": {}
    }

    try:
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)
            config.update(loaded_config)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No valid config.json found in the backup directory. Let's create one.")

    if not config.get('github_usernames') or "YOUR_GITHUB_USERNAME" in config.get('github_usernames', []):
        config = prompt_for_username(config)

    usernames = config.get('github_usernames', [])
    include_forks = config.get('include_forks', False)
    clone_depth = config.get('clone_depth', 0)
    
    processed_repos = set()

    if usernames:
        for username in usernames:
            print(f"Fetching repository list for {username}...")
            remote_repos = get_repos_from_github(username, include_forks)
            
            for name, info in remote_repos.items():
                processed_repos.add(name)
                repo_config = config['repositories'].get(name, {})
                last_sync = repo_config.get('last_synced_at', '1970-01-01T00:00:00Z')
                
                if info['pushed_at'] > last_sync:
                    print(f"Remote repo '{name}' has new changes (pushed at {info['pushed_at']}).")
                    target_path = os.path.join(backup_dir, name)
                    success = False
                    if not os.path.exists(target_path):
                        success = clone_repo(info['clone_url'], target_path, clone_depth)
                    else:
                        success = update_repo(target_path, info['clone_url'])
                    
                    if success:
                        config['repositories'][name] = {
                            'pushed_at': info['pushed_at'],
                            'last_synced_at': datetime.now(timezone.utc).isoformat()
                        }
                else:
                    print(f"Remote repo '{name}' has no new changes since last sync.")

    print("\n--- Checking for local-only repositories to sync ---")
    for item in os.listdir(backup_dir):
        item_path = os.path.join(backup_dir, item)
        if item not in processed_repos and os.path.isdir(item_path):
            update_repo(item_path)

    save_config(config, config_path)
    print("\nSync process finished. Configuration updated.")

if __name__ == "__main__":
    main()
