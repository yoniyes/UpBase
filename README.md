# UpBase

Automatically rebase your local branches and keep them up-to-date with changes committed to remote branches.

## Setup

1. Place the `.upbase.py` file in your repo's top-level directory

2. `chmod +x .upbase.py`

3. `mkdir .upbase`

4. `touch .upbase/.upbase.yaml`

5. Fill in the yaml as defined further down

### .upbase.yaml

The most minimal configuration:

```yaml
remote_repo: origin
branches:
  - local_branch: my-branch-that-forked-from-main
    remote_branch: main
```

Complete options:

```yaml
remote_repo: origin # MANDATORY. The name of the remote repository
branches:   # MANDATORY. A list of objects describing the UpBase configuration for rebasing the local branch on top of a remote branch.
  - local_branch: test  # MANDATORY. The local branch to rebase
    remote_branch: main # MANDATORY. The remote branch to rebase from
  - local_branch: local_test
    remote_branch: main
    disabled: True  # OPTIONAL. Should this rebase be skipped?
    push_to_remote: # OPTIONAL. An object to configure pushing the local branch to remote after successful rebasing
      allowed_to_push: some@email.com # MANDATORY. If you chose to push to remote, this field must be configured to be the email of the brnach owner to have only one automatic push in a team
      force: True   # OPTIONAL. Should the push be forced?
    post_script:    # OPTIONAL. A list of commands to run after rebasing (and optionally pushing)
      - "echo POST SCRIPT"
      - "echo MORE POST SCRIPT"
      - "python3 ./my-post-script.py"
```

### Schedule UpBase with `cron`

Provided is a `.upbase_cron.sh` script that expects an environment variable called `REPO_PATH` which should be the absolute path to the git repo you want UpBase to run on. Place it in the `.upbase` directory. Then you can add it to your `crontab` and choose whatever schedule you'd like. You can also pipe the stdout and stderr to whatever log file you want if you'd like it.

Important! Make sure your [repo configuration uses ssh and not https](https://gist.github.com/asksven/b37e8d83eca7f77484be9dd7af2b98e6#file-git-with-ssh-instead-of-https).


For example:

```bash
0 6 * * * REPO_PATH="/path/to/your/repo" /path/to/your/repo/.upbase_cron.sh >> /path/to/your/repo/.upbase/upbase_cron.log 2>&1
```

This will run UpBase every day at 6 AM, define an environment variable that is passed to the UpBase cron script and will direct all stdout and stderr to a dedicated log file.
