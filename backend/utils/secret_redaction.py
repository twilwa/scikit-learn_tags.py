import re
from typing import Set, List, Tuple

class SecretRedactor:
    def __init__(self):
        self.patterns = [
            (r'sk-[a-zA-Z0-9]{20,}', 'OPENAI_API_KEY'),
            (r'sk-ant-[a-zA-Z0-9\-_]{20,}', 'ANTHROPIC_API_KEY'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GITHUB_TOKEN'),
            (r'gho_[a-zA-Z0-9]{36}', 'GITHUB_OAUTH_TOKEN'),
            (r'(?i)Bearer\s+[a-zA-Z0-9\-_\.]{20,}', 'BEARER_TOKEN'),
            (r'(?i)token["\s:=]+[a-zA-Z0-9\-_\.]{20,}', 'API_TOKEN'),
            (r'(?i)api[_-]?key["\s:=]+[a-zA-Z0-9\-_\.]{20,}', 'API_KEY'),
            (r'(?i)secret["\s:=]+[a-zA-Z0-9\-_\.]{20,}', 'SECRET'),
            (r'(?i)password["\s:=]+[^\s"\']{8,}', 'PASSWORD'),
            (r'-----BEGIN (RSA |DSA )?PRIVATE KEY-----[\s\S]*?-----END (RSA |DSA )?PRIVATE KEY-----', 'PRIVATE_KEY'),
            (r'ssh-rsa\s+[A-Za-z0-9+/]{200,}[=]{0,3}', 'SSH_PUBLIC_KEY'),
            (r'ey[A-Za-z0-9\-_]+\.ey[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+', 'JWT_TOKEN'),
            (r'(?i)postgres://[^\s]+:[^\s]+@[^\s]+', 'DATABASE_URL'),
            (r'(?i)mysql://[^\s]+:[^\s]+@[^\s]+', 'DATABASE_URL'),
            (r'mongodb(\+srv)?://[^\s]+:[^\s]+@[^\s]+', 'DATABASE_URL'),
            (r'AKIA[0-9A-Z]{16}', 'AWS_ACCESS_KEY_ID'),
            (r'(?i)aws_secret_access_key[\s=:]+[a-zA-Z0-9/+]{40}', 'AWS_SECRET_ACCESS_KEY'),
            (r'AIza[0-9A-Za-z\-_]{35}', 'GOOGLE_API_KEY'),
            (r'ya29\.[0-9A-Za-z\-_]+', 'GOOGLE_OAUTH_TOKEN'),
            (r'projects/[^/]+/secrets/[^/]+', 'GCP_SECRET_PATH'),
            (r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'UUID_TOKEN'),
            (r'xox[pboa]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}', 'SLACK_TOKEN'),
            (r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8,}/B[a-zA-Z0-9_]{8,}/[a-zA-Z0-9_]{24}', 'SLACK_WEBHOOK'),
        ]

        self.compiled_patterns = [(re.compile(pattern), name) for pattern, name in self.patterns]

    def redact(self, text: str) -> Tuple[str, List[str]]:
        redacted_text = text
        found_secrets = []

        for pattern, secret_name in self.compiled_patterns:
            matches = pattern.finditer(redacted_text)
            for match in matches:
                found_secrets.append(f"{secret_name} at position {match.start()}")
                redacted_text = redacted_text[:match.start()] + f"[REDACTED_{secret_name}]" + redacted_text[match.end():]

        return redacted_text, list(set(found_secrets))

    def redact_env_vars(self, text: str) -> str:
        env_pattern = re.compile(r'(?i)(export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*["\']?([^"\'\s]+)["\']?')

        def replace_env(match):
            var_name = match.group(2)
            value = match.group(3)

            sensitive_keywords = ['KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'AUTH', 'CREDENTIAL']
            if any(keyword in var_name.upper() for keyword in sensitive_keywords):
                return f"{match.group(1) or ''}{var_name}=[REDACTED_{var_name}]"
            return match.group(0)

        return env_pattern.sub(replace_env, text)

    def full_redaction(self, text: str) -> Tuple[str, List[str]]:
        redacted, secrets = self.redact(text)
        redacted = self.redact_env_vars(redacted)
        return redacted, secrets

def redact_secrets(text: str) -> Tuple[str, List[str]]:
    redactor = SecretRedactor()
    return redactor.full_redaction(text)
