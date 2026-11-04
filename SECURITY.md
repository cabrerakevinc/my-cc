# Security

The command center stores local ticket details, decision logs, and reference material. Keep company confidential information in authorized local workspaces only, not this public plugin repository.

Do not commit credentials, AWS logs, private Jira issue contents, or confidential repository code. State and context folders are ignored by default, but review `git status` before publication.

No data is sent by the Python CLI to third-party services. External CLIs and Claude Code have separate behavior and must be configured under company policy. Push, merge, deploy, and Jira closure require human authorization.

For security concerns, use a private report to the repository maintainer rather than publishing secrets in a GitHub issue.
