# Jan-SahayakAI Security Notes

## Secrets

- Keep `.env`, `.env.local`, and `.streamlit/secrets.toml` out of Git.
- Never hard-code AWS access keys, bearer tokens, passwords, or Knowledge Base credentials.
- Do not paste credentials into chat, source files, screenshots, or issue trackers.
- The previously exposed AWS/Bedrock credential must be revoked and replaced by the account owner. Do not reuse it.

## AWS permissions

Use a dedicated development identity with only the permissions required by this project:

- Bedrock model invocation for the configured model.
- Bedrock Knowledge Base retrieval for the configured Knowledge Base.
- No S3 write, IAM administration, account administration, or unrelated service permissions unless separately required by the AWS owner.

Prefer short-lived AWS CLI or SSO credentials over long-lived access keys. Never commit credential files.

## Application behavior

- Complaint records are stored in a local in-memory mock database.
- `READY_FOR_SUBMISSION` is not proof of a real government submission.
- Eligibility responses are preliminary and require official verification.
- RAG responses must use retrieved content and returned source information. The application must say when official documents are unavailable or insufficient.
- UI error messages are generic; logs record only exception types and must not contain user prompts or credentials.