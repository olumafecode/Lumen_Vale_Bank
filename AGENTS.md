# Project working instructions

The user requires fixes and tests to go through GitHub Actions going forward.

- Preserve the fictional corpus and keep evaluation answers out of ingestion.
- Add focused regression tests when fixing behavioral bugs; run relevant local checks.
- Keep .github/workflows/ci.yml working on pushes and pull requests.
- Commit code, tests, and related documentation coherently so the same version is checked by CI.
- When publishing is authorized, push and check the Actions result for that exact commit if network access permits.
- If pushing or reading Actions is blocked, explain the concrete limitation and give the minimal user command/link. Never claim GitHub CI passed solely because local tests passed.
- Do not add API keys to the repository or routine CI. Keep live Groq checks separate from mocked automated tests.
- Preserve original evaluation attempts and identify benchmark-informed reruns honestly.
