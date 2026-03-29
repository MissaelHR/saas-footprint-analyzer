# Security Policy

## Reporting

Do not open public issues for security-sensitive problems. Report vulnerabilities privately to the maintainers.

## Secrets handling

`saas-footprint-analyzer` is designed so credentials come from environment variables rather than plain-text YAML. Do not commit real Datadog credentials, output artifacts with sensitive metadata, or shell history containing secrets.

## Datadog permissions

The tool requires Datadog API and application keys with enough permission to validate credentials, list tag inventory used for discovery, and query metrics. If a token lacks permission, the CLI surfaces the failure instead of silently degrading behavior.
