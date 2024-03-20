import subprocess
import yaml
import time
import logging
from colorama import Fore, Style

def get_current_branch_name():
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip()

def get_git_config_user_email():
    result = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True)
    return result.stdout.strip()

def git_fetch():
    subprocess.run(["git", "fetch", "origin"], check=True)

def git_stash():
    current_branch = get_current_branch_name()
    stash_name = f'upbase_{str(time.time())}__{current_branch}'
    try:
        subprocess.run(["git", "stash", "push", "-m" , f'"{stash_name}"'], check=True)
    except subprocess.CalledProcessError:
        msg = "Error occurred while stashing changes."
        print(Fore.RED + msg + Style.RESET_ALL)
        logging.error(msg)

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
        msg = f"Branch '{branch_name}' does not exist."
        print(Fore.RED + msg + Style.RESET_ALL)
        logging.error(msg)

        return False
    return True

def git_rebase(branch_name):
    try:
        subprocess.run(["git", "rebase", branch_name], check=True)
    except subprocess.CalledProcessError:
        msg = f"Error occurred while rebasing '{get_current_branch_name()}' on top of '{branch_name}'."
        print(Fore.RED + msg + Style.RESET_ALL)
        logging.error(msg)

        return False
    return True

def git_rebase_abort(branch_name):
    try:
        subprocess.run(["git", "rebase", "--abort"], check=True)
    except subprocess.CalledProcessError:
        msg = f"Error occurred while aborting rebase of '{get_current_branch_name()}' on top of '{branch_name}'."
        print(Fore.RED + msg + Style.RESET_ALL)
        logging.error(msg)

        return False
    return True

def git_push(branch_name, force=False):
    try:
        subprocess.run(["git", "push", "origin", branch_name, "--force" if force else ""], check=True)
    except subprocess.CalledProcessError:
        msg = f"Error occurred while pushing '{branch_name}' to origin."
        print(Fore.RED + msg + Style.RESET_ALL)
        logging.error(msg)

        return False
    return True

def is_allowed_to_push(local_branch, push_to_remote):
    allowed_to_push = push_to_remote.get("allowed_to_push")
    user_email = get_git_config_user_email()
    if allowed_to_push is None:
        msg = f"Can't push '{local_branch}' to origin: in .upbase.yaml, field `branch->push_to_remote->allowed_to_push` must be set to the allowed user email"
        print(Fore.YELLOW + msg + Style.RESET_ALL)
        logging.warn(msg)
        return False
    elif allowed_to_push != user_email:
        msg = f"Can't push '{local_branch}' to origin: you are user '{user_email}' and only user '{allowed_to_push}' is allowed to push"
        print(Fore.YELLOW + msg + Style.RESET_ALL)
        logging.warn(msg)
        return False
    return True

def run_post_script(script):
    for command in script:
        try:
            subprocess.run([command], check=True, shell=True)
        except subprocess.CalledProcessError:
            msg = f"Error occurred while executing command '{command}' in post-script."
            print(Fore.RED + msg + Style.RESET_ALL)
            logging.error(msg)

            return False
    return True

def rebase_local_branches(branch_mapping, remote_repo="origin"):
    git_fetch()

    for branch_info in branch_mapping:
        disabled = branch_info.get("disabled")
        if disabled is not None and disabled:
            continue

        local_branch = branch_info.get("local_branch")
        remote_branch = '/'.join([remote_repo, branch_info.get("remote_branch")])
        push_to_remote = branch_info.get("push_to_remote")
        post_script = branch_info.get("post_script")

        msg = f"Rebasing local branch '{local_branch}' on top of remote branch '{remote_branch}'..."
        print(Fore.GREEN + msg + Style.RESET_ALL)
        logging.info(msg)

        if not git_checkout(local_branch):
            continue

        if not git_rebase(remote_branch):
            msg = f"Conflicts occurred during rebase of local branch '{local_branch}'. Aborting rebase..."
            print(Fore.YELLOW + msg + Style.RESET_ALL)
            logging.warn(msg)

            if not git_rebase_abort():
                raise Exception(f"Failed aborting rebase of '{local_branch}'")
            continue

        if push_to_remote is not None:
            msg = f"Pushing '{local_branch}' to origin..."
            print(Fore.GREEN + msg + Style.RESET_ALL)
            logging.info(msg)

            if is_allowed_to_push(local_branch, push_to_remote):
                git_fetch()
                remote_local_branch = '/'.join([remote_repo, local_branch])
                if not git_rebase(remote_local_branch):
                    msg = f"Conflicts occurred during rebase of local branch '{local_branch}' before pushing it to remote. Aborting rebase..."
                    print(Fore.YELLOW + msg + Style.RESET_ALL)
                    logging.warn(msg)

                    if not git_rebase_abort():
                        raise Exception(f"Failed aborting rebase of '{local_branch}'")
                    continue

                git_push(local_branch, force=push_to_remote.get("force", False))
        
        if post_script is not None and len(post_script) > 0:
            msg = f"Running post-script for '{local_branch}'..."
            print(Fore.GREEN + msg + Style.RESET_ALL)
            logging.info(msg)

            if not run_post_script(post_script):
                msg = f"Failed to execute post-script for '{local_branch}', post-script: {post_script}"
                print(Fore.RED + msg + Style.RESET_ALL)
                logging.error(msg)
        
        msg = f"Successfully rebased local branch '{local_branch}' on top of remote branch '{remote_branch}'"
        print(Fore.GREEN + msg + Style.RESET_ALL)
        logging.info(msg)



if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG,
                        filename='.upbase/upbase.log',
                        encoding='utf-8')

    with open(".upbase/.upbase.yaml", "r") as yaml_file:
        # Save the current branch name
        original_branch = get_current_branch_name()

        # Stash changes with a custom name
        stash_name = git_stash()
        if stash_name is None:
            exit(1)  # Exit the script if stashing fails

        try:
            branch_mapping = yaml.safe_load(yaml_file)
            remote_repo = branch_mapping.get("remote_repo", "origin")
            rebase_local_branches(branch_mapping.get("branches", []), remote_repo=remote_repo)

        except Exception as e:
            msg = f"******** Stashed your changes in original branch '{original_branch}' under name '{stash_name}' ********"
            print(e)
            logging.exception('Exception!', exc_info=e)
            print(Fore.YELLOW + msg + Style.RESET_ALL)
            logging.warn(msg)
            exit(1)

        # Switch back to the original branch
        git_checkout(original_branch)

        # Pop the stash
        git_stash_pop(stash_name)
