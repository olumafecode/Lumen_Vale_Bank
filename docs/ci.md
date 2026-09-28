# GitHub Actions checks

The Policy assistant CI workflow runs on every push, every pull request, and manual workflow_dispatch. Open the repository's Actions tab and select the workflow:

https://github.com/olumafecode/Lumen_Vale_Bank/actions

The Python 3.12 / Windows job checks out a fresh copy, installs hashed development dependencies, runs pip check, verifies all canonical policy hashes, imports the app and required parsers, and runs the full pytest suite. The workflow uses the official checkout and setup-python actions.

Windows is intentional: this is the platform on which the existing environment and locks were verified. A Linux job should be added after its dependency installation and tests have been validated, especially before Linux deployment.

No Groq key or other secret is passed to CI. Generation tests use explicit mocks; Chroma storage tests use local fixture embeddings. CI does not run the live held-out benchmark, spend provider quota, download MiniLM, or claim semantic answer quality. Live development/evaluation results remain separately recorded.

## Going forward

For each fix:

1. Run relevant local tests.
2. Commit the implementation, regression tests, and relevant documentation together.
3. Push the branch (or open/update its pull request).
4. Open Actions and confirm the check passed for that exact commit. A local test pass is not a GitHub Actions pass.
5. If it fails, inspect the first failing step, fix the cause, and push again.

The workflow starts only after its file is pushed. Historical commits will not gain retroactive CI evidence.

This implements continuous integration. Automatic deployment is not configured because no deployment target has been selected; the assignment permits a local demo and makes automatic deployment optional. Do not describe this workflow as a successful deployment.

Optional repository governance: require the Python 3.12 / Windows check before merging via a GitHub ruleset. That is a repository setting, separate from committing this workflow.

Official references:
- https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- https://github.com/actions/checkout
- https://github.com/actions/setup-python

## Local preflight

The initial workflow was checked against a fresh source copy without .env, an index, or a model cache: all 78 tests passed using the existing Python 3.12 virtual environment. Dependency compatibility, corpus verification, and app/parser imports also passed. A fresh dependency installation and the hosted Actions result remain to be verified by GitHub. Pytest uses the ignored project-root .pytest_tmp directory so it does not depend on an existing cache folder.

## Corpus checkout line endings

The first hosted run failed corpus verification because the original 12 policy files use CRLF line endings while the default Git attribute checked them out as LF. The manifest hashes original bytes, so identical wording with different line endings correctly fails verification. The corpus-specific `text eol=crlf` attribute restores the original bytes on checkout on every platform. The manifest, policy wording, and hash validator remain unchanged.

The earlier preflight copied working files and therefore missed Git checkout conversion. Future checkout-sensitive verification must use an actual Git checkout, not a filesystem copy. The CI corpus verification step remains mandatory.

Fix validation: a fresh local Git clone of commit 849e5f0 verified all 12 original manifest hashes and passed all 78 tests using the existing Python 3.12 environment. The hosted rerun remains pending publication.
