Release Instructions
====================

Versions should take the form "v<major>.<minor>.patch". For example, "v0.3.0" is a valid
version, while "v1" is not and "0.3.0" is not.

1. Make sure all PRs are merged and tests pass.

2. Prepare a release branch with `git checkout -b release/<version>`.

3. Update the HISTORY.md, replacing the "latest" version heading with the new version.

4. Commit your changes so far to the release branch.

5. In the project root, run `bumpversion <major/minor/patch>`. This will create a new commit.

6. `git push -u origin release/<version>` and create a new pull request in Github.

7. When the pull request is merged to master, `git checkout master` and `git pull`,
   followed by `git tag <version>`.

8. Run `git push origin --tags` to push all local tags to Github.
