# Architecture

```mermaid
flowchart LR
    A[JSONL batch] --> B[S3 raw/]
    B -->|ObjectCreated| C[Lambda validator]
    C --> D[S3 processed/]
    C --> E[S3 quarantine/]
    C --> F[CloudWatch Logs]
    C -->|Errors metric| G[CloudWatch Alarm]
    G --> H[SNS email]
    D --> I[Athena validated table]
    E --> J[Athena quarantine table]
    I --> K[Quality and business views]
    J --> K
```

## Governance controls

- Private S3 bucket with public access blocked, ACLs disabled, versioning, and SSE-S3.
- Event filter restricted to `raw/*.jsonl` to prevent recursive invocation.
- Lambda role limited to reading `raw/` and writing `processed/` and `quarantine/`.
- Unexpected fields are rejected to expose schema drift and possible sensitive-data leakage.
- CloudWatch logs retain operational summaries rather than record payloads.
- Alarm threshold is one or more Lambda errors in five minutes; missing data is healthy.

