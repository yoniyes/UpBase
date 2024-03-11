import subprocess
import yaml
import time

def get_current_branch_name():
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip()

def git_fetch():
    subprocess.run(["git", "fetch", "origin"], check=True)

def git_stash():
    current_branch = get_current_branch_name()
    stash_name = f'upbase_{str(time.time())}__{current_branch}'
    try:
        subprocess.run(["git", "stash", "push", "-m" , f'"{stash_name}"'], check=True)
    except subprocess.CalledProcessError:
        print("Error occurred while stashing changes.")
        return None
    return stash_name

def git_stash_pop(stash_name):
    stash_value =  "stash^{/"f"{stash_name}""}"
    try:
        subprocess.run(["git", "stash", "apply", stash_value], check=True)
    except subprocess.CalledProcessError:
        return False
    return True

def git_checkout(branch_name):
    try:
        subprocess.run(["git", "checkout", branch_name], check=True)
    except subprocess.CalledProcessError:
        print(f"Branch '{branch_name}' does not exist.")
        return False
    return True

def git_rebase(branch_name):
    try:
        subprocess.run(["git", "rebase", branch_name], check=True)
    except subprocess.CalledProcessError:
        print(f"Error occurred while rebasing '{get_current_branch_name()}' on top of '{branch_name}'.")
        return False
    return True

def git_rebase_abort(branch_name):
    try:
        subprocess.run(["git", "rebase", "--abort"], check=True)
    except subprocess.CalledProcessError:
        print(f"Error occurred while aborting rebase of '{get_current_branch_name()}' on top of '{branch_name}'.")
        return False
    return True

def git_push(branch_name):
    try:
        subprocess.run(["git", "push", "origin", branch_name, "--force"], check=True)
    except subprocess.CalledProcessError:
        print(f"Error occurred while pushing '{branch_name}' to origin.")
        return False
    return True

def run_post_script(script):
    for command in script:
        try:
            subprocess.run([command], check=True, shell=True)
        except subprocess.CalledProcessError:
            print(f"Error occurred while executing command '{command}' in post-script.")
            return False
    return True

def rebase_local_branches(branch_mapping):
    git_fetch()

    for branch_info in branch_mapping:
        disabled = branch_info.get("disabled")
        if disabled is not None and disabled:
            continue

        local_branch = branch_info.get("local_branch")
        remote_branch = branch_info.get("remote_branch")
        push_to_remote = branch_info.get("push_to_remote")
        post_script = branch_info.get("post_script")

        print(f"Rebasing local branch '{local_branch}' on top of remote branch '{remote_branch}'...")
        if not git_checkout(local_branch):
            continue

        if not git_rebase(remote_branch):
            print(f"Conflicts occurred during rebase of local branch '{local_branch}'. Aborting rebase...")
            if not git_rebase_abort():
                raise Exception(f"Failed aborting rebase of '{local_branch}'")
            continue

        if push_to_remote is not None and push_to_remote:
            print(f"Pushing '{local_branch}' to origin...")
            git_push(local_branch)
        
        if post_script is not None and len(post_script) > 0:
            if not run_post_script(post_script):
                print(f"Failed to execute post-script for {local_branch}, post-script: {post_script}")

if __name__ == "__main__":
    with open(".upbase/.upbase.yaml", "r") as yaml_file:
        # Save the current branch name
        original_branch = get_current_branch_name()

        # Stash changes with a custom name
        stash_name = git_stash()
        if stash_name is None:
            exit(1)  # Exit the script if stashing fails

        try:
            branch_mapping = yaml.safe_load(yaml_file)
            rebase_local_branches(branch_mapping.get("branches", []))

        except Exception as e:
            print(e)
            print(f"******** Stashed your changes in original branch '{original_branch}' under name '{stash_name}' ********")
            exit(1)

        # Switch back to the original branch
        git_checkout(original_branch)

        # Pop the stash
        git_stash_pop(stash_name)
