# Authentication and Security Reference

**Date**: October 15, 2025
**Purpose**: Security patterns for AI Co-Scientist CLI and MCP

## Executive Summary

This document provides comprehensive authentication and security guidance for both CLI and MCP interfaces, following OAuth 2.1, PKCE, and modern security best practices.

## OAuth 2.1 Overview

### Key Changes from OAuth 2.0

OAuth 2.1 consolidates best practices from OAuth 2.0 and related RFCs:

1. **PKCE Mandatory**: All authorization code flows require PKCE
2. **Implicit Flow Removed**: Only authorization code flow supported
3. **Resource Owner Password Flow Removed**: Security risk eliminated
4. **Refresh Token Rotation**: Mandatory for public clients
5. **Redirect URI Exact Matching**: No wildcards allowed

### References

- **RFC 6749**: OAuth 2.0 Framework (base)
- **RFC 7636**: PKCE (Proof Key for Code Exchange)
- **RFC 8707**: Resource Indicators for fine-grained access
- **RFC 9728**: Protected Resource Metadata for server discovery
- **OAuth 2.1**: Draft consolidating best practices (2025)

## PKCE (Proof Key for Code Exchange)

### Why PKCE?

PKCE prevents authorization code interception attacks by:
1. Binding authorization request to token request
2. Eliminating need for client secrets (public clients)
3. Protecting against malicious apps

### PKCE Flow

```
┌─────────┐                                  ┌────────────┐
│ Client  │                                  │   Auth     │
│         │                                  │  Server    │
└────┬────┘                                  └─────┬──────┘
     │                                             │
     │ 1. Generate code_verifier (random)         │
     │    code_challenge = SHA256(code_verifier)  │
     │                                             │
     │ 2. Authorization Request                   │
     │    + code_challenge                         │
     │    + code_challenge_method=S256            │
     ├────────────────────────────────────────────>│
     │                                             │
     │ 3. Authorization Code                      │
     │<────────────────────────────────────────────┤
     │                                             │
     │ 4. Token Request                           │
     │    + code                                  │
     │    + code_verifier                         │
     ├────────────────────────────────────────────>│
     │                                             │
     │    Server verifies:                        │
     │    SHA256(code_verifier) == code_challenge │
     │                                             │
     │ 5. Access Token                            │
     │<────────────────────────────────────────────┤
     │                                             │
```

### Implementation

```python
import secrets
import hashlib
import base64

def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code verifier and challenge.

    Returns:
        tuple: (code_verifier, code_challenge)
    """
    # Generate code_verifier (43-128 characters, URL-safe)
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').rstrip('=')

    # Generate code_challenge (SHA256 hash of verifier)
    code_challenge = hashlib.sha256(
        code_verifier.encode('utf-8')
    ).digest()
    code_challenge = base64.urlsafe_b64encode(
        code_challenge
    ).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge


# Example usage
code_verifier, code_challenge = generate_pkce_pair()

# Step 1: Authorization request
auth_params = {
    "client_id": "co-scientist-cli",
    "redirect_uri": "http://localhost:8080/callback",
    "response_type": "code",
    "scope": "research:read research:write",
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
    "state": secrets.token_urlsafe(32)
}

auth_url = f"https://auth.co-scientist.ai/authorize?{urlencode(auth_params)}"

# Step 2: User authorizes in browser
# Receives authorization code

# Step 3: Token request
token_params = {
    "grant_type": "authorization_code",
    "code": authorization_code,
    "redirect_uri": "http://localhost:8080/callback",
    "client_id": "co-scientist-cli",
    "code_verifier": code_verifier  # Proves we initiated the flow
}

token_response = requests.post(
    "https://auth.co-scientist.ai/token",
    data=token_params
)
```

## CLI Authentication

### Local-Only Mode (Default)

For single-user local development:

```python
class LocalAuth:
    """Local-only authentication (no network)."""

    def __init__(self, config_dir: Path = Path.home() / ".co-scientist"):
        self.config_dir = config_dir
        self.config_file = config_dir / "config.yaml"
        self.token_file = config_dir / ".token"

    def is_authenticated(self) -> bool:
        """Check if user has valid local session."""
        return self.token_file.exists()

    def login(self, username: str, password: str) -> bool:
        """Local authentication (stores hashed credentials)."""
        # In production, this would verify against local keychain
        # or prompt for master password

        # Hash password
        password_hash = hashlib.sha256(
            f"{username}:{password}".encode()
        ).hexdigest()

        # Store token
        token = secrets.token_urlsafe(32)
        self.token_file.write_text(json.dumps({
            "user": username,
            "token": token,
            "created_at": datetime.utcnow().isoformat()
        }))

        return True

    def logout(self):
        """Clear local session."""
        if self.token_file.exists():
            self.token_file.unlink()


# Usage
auth = LocalAuth()

if not auth.is_authenticated():
    username = typer.prompt("Username")
    password = typer.prompt("Password", hide_input=True)
    auth.login(username, password)

# Now proceed with CLI operations
```

### OAuth 2.1 Mode (Multi-User)

For cloud deployments with multiple users:

```python
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback in local server."""

    authorization_code = None
    state = None

    def do_GET(self):
        """Handle authorization callback."""
        query = parse_qs(urlparse(self.path).query)

        OAuthCallbackHandler.authorization_code = query.get('code', [None])[0]
        OAuthCallbackHandler.state = query.get('state', [None])[0]

        # Send success page
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"""
            <html>
            <body>
                <h1>Authentication Successful</h1>
                <p>You can close this window and return to the CLI.</p>
            </body>
            </html>
        """)

    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


class CLIOAuth:
    """OAuth 2.1 authentication for CLI."""

    def __init__(
        self,
        client_id: str,
        auth_url: str,
        token_url: str,
        redirect_port: int = 8080
    ):
        self.client_id = client_id
        self.auth_url = auth_url
        self.token_url = token_url
        self.redirect_port = redirect_port
        self.redirect_uri = f"http://localhost:{redirect_port}/callback"

        self.config_dir = Path.home() / ".co-scientist"
        self.config_dir.mkdir(exist_ok=True)
        self.token_file = self.config_dir / ".oauth_token"

    def login(self, scopes: list[str]) -> dict:
        """Initiate OAuth 2.1 login flow with PKCE.

        Returns:
            dict: Token response with access_token, refresh_token, etc.
        """
        # Generate PKCE parameters
        code_verifier, code_challenge = generate_pkce_pair()
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        auth_params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        auth_url = f"{self.auth_url}?{urlencode(auth_params)}"

        # Start local callback server
        server = HTTPServer(('localhost', self.redirect_port), OAuthCallbackHandler)

        # Open browser for authorization
        typer.echo(f"Opening browser for authentication...")
        typer.echo(f"If browser doesn't open, visit: {auth_url}")
        webbrowser.open(auth_url)

        # Wait for callback (timeout after 5 minutes)
        typer.echo("Waiting for authorization...")
        server.timeout = 300
        server.handle_request()

        # Verify we got authorization code
        if not OAuthCallbackHandler.authorization_code:
            raise RuntimeError("Authorization failed - no code received")

        # Verify state matches (CSRF protection)
        if OAuthCallbackHandler.state != state:
            raise RuntimeError("State mismatch - possible CSRF attack")

        # Exchange code for token
        token_params = {
            "grant_type": "authorization_code",
            "code": OAuthCallbackHandler.authorization_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": code_verifier  # PKCE verification
        }

        response = requests.post(self.token_url, data=token_params)
        response.raise_for_status()

        token_data = response.json()

        # Store tokens securely
        self._store_tokens(token_data)

        typer.echo("✓ Authentication successful")
        return token_data

    def _store_tokens(self, token_data: dict):
        """Store tokens securely in config directory."""
        # In production, use OS keychain (keyring library)
        self.token_file.write_text(json.dumps({
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": (
                datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            ).isoformat(),
            "scope": token_data["scope"]
        }))
        self.token_file.chmod(0o600)  # Read/write for owner only

    def get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary."""
        if not self.token_file.exists():
            raise RuntimeError("Not authenticated - run 'co-scientist login' first")

        token_data = json.loads(self.token_file.read_text())
        expires_at = datetime.fromisoformat(token_data["expires_at"])

        # Check if token needs refresh
        if datetime.utcnow() >= expires_at - timedelta(minutes=5):
            # Refresh token
            token_data = self._refresh_token(token_data["refresh_token"])
            self._store_tokens(token_data)

        return token_data["access_token"]

    def _refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        token_params = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id
        }

        response = requests.post(self.token_url, data=token_params)
        response.raise_for_status()

        return response.json()

    def logout(self):
        """Clear stored tokens."""
        if self.token_file.exists():
            self.token_file.unlink()
        typer.echo("✓ Logged out successfully")


# Usage in CLI
oauth = CLIOAuth(
    client_id="co-scientist-cli",
    auth_url="https://auth.co-scientist.ai/authorize",
    token_url="https://auth.co-scientist.ai/token"
)

@app.command()
def login():
    """Authenticate with AI Co-Scientist."""
    oauth.login(scopes=[
        "research:read",
        "research:write",
        "hypotheses:generate"
    ])

@app.command()
def logout():
    """Clear authentication."""
    oauth.logout()

@app.command()
def research_start(goal: str):
    """Start research (requires authentication)."""
    # Get access token
    access_token = oauth.get_access_token()

    # Make authenticated API call
    response = requests.post(
        "https://api.co-scientist.ai/research",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"goal": goal}
    )

    # Handle response
    ...
```

## MCP Authentication

### OAuth 2.1 with FastMCP

```python
from fastmcp import FastMCP, Context
from fastmcp.auth import OAuth21Config

# Configure MCP server with OAuth 2.1
mcp = FastMCP("AI Co-Scientist")

mcp.configure_auth(
    OAuth21Config(
        # Authorization server endpoints
        auth_url="https://auth.co-scientist.ai/authorize",
        token_url="https://auth.co-scientist.ai/token",
        jwks_url="https://auth.co-scientist.ai/.well-known/jwks.json",

        # Client configuration
        client_id="co-scientist-mcp",

        # Token validation
        audience="https://api.co-scientist.ai",
        issuer="https://auth.co-scientist.ai",

        # Scopes
        scopes={
            "research:read": "Read research projects and hypotheses",
            "research:write": "Create and modify research projects",
            "hypotheses:generate": "Generate new hypotheses",
            "hypotheses:evolve": "Evolve existing hypotheses",
            "reviews:read": "Read hypothesis reviews",
            "reviews:write": "Create hypothesis reviews",
            "admin": "Full system access"
        },

        # Security
        pkce_required=True,
        refresh_token_rotation=True
    )
)


# Tools automatically enforce authentication
@mcp.tool(scopes=["research:write"])
async def start_research(goal: str, context: Context) -> dict:
    """Start research (requires research:write scope)."""

    # Context provides authentication info
    user_id = context.user.id
    user_scopes = context.user.scopes

    # Verify scope (done automatically by decorator)
    if not context.has_scope("research:write"):
        raise PermissionError("research:write scope required")

    # Log for audit trail
    await context.log_action("start_research", {"goal": goal})

    # Proceed with research
    ...
```

### JWT Token Validation

```python
import jwt
from jwt import PyJWKClient
from datetime import datetime

class JWTValidator:
    """Validate JWT access tokens."""

    def __init__(
        self,
        jwks_url: str,
        audience: str,
        issuer: str
    ):
        self.jwks_client = PyJWKClient(jwks_url)
        self.audience = audience
        self.issuer = issuer

    def validate(self, access_token: str) -> dict:
        """Validate JWT and return decoded payload.

        Raises:
            jwt.InvalidTokenError: Token is invalid or expired
        """
        # Get signing key from JWKS endpoint
        signing_key = self.jwks_client.get_signing_key_from_jwt(access_token)

        # Decode and validate
        payload = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
                "require_exp": True,
                "require_iat": True
            }
        )

        return payload


# Usage
validator = JWTValidator(
    jwks_url="https://auth.co-scientist.ai/.well-known/jwks.json",
    audience="https://api.co-scientist.ai",
    issuer="https://auth.co-scientist.ai"
)

try:
    payload = validator.validate(access_token)
    user_id = payload["sub"]
    scopes = payload["scope"].split()
    email = payload["email"]

    # Proceed with authorized request
    ...

except jwt.ExpiredSignatureError:
    # Token expired - need to refresh
    ...

except jwt.InvalidAudienceError:
    # Token not intended for this API
    ...

except jwt.InvalidTokenError as e:
    # Invalid token
    ...
```

## Scope Design

### Hierarchical Scopes

```python
# Scope hierarchy for AI Co-Scientist
SCOPES = {
    # Read-only scopes
    "research:read": {
        "description": "Read research projects and status",
        "implies": []
    },
    "hypotheses:read": {
        "description": "Read hypotheses and their details",
        "implies": []
    },
    "reviews:read": {
        "description": "Read hypothesis reviews and scores",
        "implies": []
    },

    # Write scopes
    "research:write": {
        "description": "Create and modify research projects",
        "implies": ["research:read"]
    },
    "hypotheses:generate": {
        "description": "Generate new hypotheses",
        "implies": ["research:read", "hypotheses:read"]
    },
    "hypotheses:evolve": {
        "description": "Evolve existing hypotheses",
        "implies": ["hypotheses:read"]
    },
    "reviews:write": {
        "description": "Create and modify reviews",
        "implies": ["reviews:read", "hypotheses:read"]
    },

    # Administrative scopes
    "admin": {
        "description": "Full system access",
        "implies": [
            "research:read", "research:write",
            "hypotheses:read", "hypotheses:generate", "hypotheses:evolve",
            "reviews:read", "reviews:write"
        ]
    }
}


def has_scope(user_scopes: list[str], required_scope: str) -> bool:
    """Check if user has required scope (including implied scopes)."""

    # Direct match
    if required_scope in user_scopes:
        return True

    # Check implied scopes
    for user_scope in user_scopes:
        if user_scope in SCOPES:
            implied = SCOPES[user_scope].get("implies", [])
            if required_scope in implied:
                return True

    return False


# Example usage
user_scopes = ["research:write", "hypotheses:generate"]

has_scope(user_scopes, "research:read")  # True (implied by research:write)
has_scope(user_scopes, "research:write")  # True (direct)
has_scope(user_scopes, "hypotheses:evolve")  # False
```

### RFC 8707: Resource Indicators

Fine-grained access control with resource-specific tokens:

```python
# Request token for specific research project
token_params = {
    "grant_type": "authorization_code",
    "code": auth_code,
    "resource": "https://api.co-scientist.ai/research/res_abc123",  # RFC 8707
    "scope": "research:read hypotheses:read"
}

# Token will be restricted to res_abc123 only
access_token = get_token(token_params)

# Using the token
@mcp.tool()
async def get_hypotheses(research_id: str, context: Context):
    """Get hypotheses for research project."""

    # Verify token resource indicator
    allowed_resource = context.token_resource
    if allowed_resource:
        # Token is restricted to specific resource
        expected = f"https://api.co-scientist.ai/research/{research_id}"
        if allowed_resource != expected:
            raise PermissionError(f"Token not valid for {research_id}")

    # Proceed with request
    ...
```

## Rate Limiting

### Token Bucket Algorithm

```python
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        self.rate = requests_per_minute / 60.0  # requests per second
        self.burst_size = burst_size

        # User buckets: {user_id: (tokens, last_update)}
        self.buckets: dict[str, tuple[float, datetime]] = defaultdict(
            lambda: (burst_size, datetime.utcnow())
        )

        self.lock = asyncio.Lock()

    async def check_limit(self, user_id: str) -> tuple[bool, int]:
        """Check if request is allowed.

        Returns:
            tuple: (allowed, retry_after_seconds)
        """
        async with self.lock:
            now = datetime.utcnow()
            tokens, last_update = self.buckets[user_id]

            # Refill tokens based on time elapsed
            elapsed = (now - last_update).total_seconds()
            tokens = min(self.burst_size, tokens + elapsed * self.rate)

            if tokens >= 1.0:
                # Allow request
                tokens -= 1.0
                self.buckets[user_id] = (tokens, now)
                return True, 0
            else:
                # Rate limited
                retry_after = int((1.0 - tokens) / self.rate)
                return False, retry_after


# Usage with MCP
rate_limiter = RateLimiter(requests_per_minute=60, burst_size=10)

@mcp.before_tool
async def check_rate_limit(context: Context):
    """Check rate limit before executing tool."""
    user_id = context.user.id

    allowed, retry_after = await rate_limiter.check_limit(user_id)

    if not allowed:
        raise RateLimitExceededError(retry_after)


# Usage with CLI
@app.command()
def research_start(goal: str):
    """Start research."""
    try:
        # Make API call
        response = api.start_research(goal)
        ...
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            # Rate limited
            retry_after = e.response.headers.get("Retry-After", 60)
            typer.echo(f"Rate limit exceeded. Retry after {retry_after}s")
        else:
            raise
```

## Audit Logging

### Comprehensive Audit Trail

```python
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class AuditLogEntry:
    """Audit log entry."""
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    parameters: dict
    result: str  # success, failure, error
    ip_address: str
    user_agent: str

    def to_json(self) -> str:
        return json.dumps({
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "parameters": self.parameters,
            "result": self.result,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        })


class AuditLogger:
    """Audit logger for security events."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    async def log(self, entry: AuditLogEntry):
        """Write audit log entry."""
        with open(self.log_file, 'a') as f:
            f.write(entry.to_json() + '\n')

    async def log_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        parameters: dict,
        result: str,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log a user action."""
        entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource=resource,
            parameters=parameters,
            result=result,
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown"
        )
        await self.log(entry)


# Usage with MCP
audit_logger = AuditLogger(Path("/var/log/co-scientist/audit.log"))

@mcp.before_tool
async def log_tool_call(context: Context, tool_name: str, parameters: dict):
    """Log all tool calls."""
    await audit_logger.log_action(
        user_id=context.user.id,
        action=f"tool:{tool_name}",
        resource=f"mcp://tools/{tool_name}",
        parameters=parameters,
        result="started",
        ip_address=context.request.client_ip,
        user_agent=context.request.user_agent
    )

@mcp.after_tool
async def log_tool_result(
    context: Context,
    tool_name: str,
    parameters: dict,
    result: any,
    error: Exception = None
):
    """Log tool results."""
    await audit_logger.log_action(
        user_id=context.user.id,
        action=f"tool:{tool_name}",
        resource=f"mcp://tools/{tool_name}",
        parameters=parameters,
        result="error" if error else "success",
        ip_address=context.request.client_ip,
        user_agent=context.request.user_agent
    )
```

## Security Best Practices

### 1. Token Storage

```python
# ❌ BAD: Plain text storage
with open("~/.token", "w") as f:
    f.write(access_token)

# ✅ GOOD: OS keychain (macOS/Linux/Windows)
import keyring

keyring.set_password("co-scientist", "access_token", access_token)

# Later:
access_token = keyring.get_password("co-scientist", "access_token")
```

### 2. HTTPS Only

```python
# ❌ BAD: Allow HTTP
API_BASE_URL = "http://api.co-scientist.ai"

# ✅ GOOD: HTTPS only with certificate verification
API_BASE_URL = "https://api.co-scientist.ai"

response = requests.get(API_BASE_URL, verify=True)  # Verify SSL cert
```

### 3. Input Validation

```python
# Validate all inputs before processing
def validate_research_goal(goal: str) -> str:
    """Validate and sanitize research goal."""

    # Length check
    if len(goal) < 10:
        raise ValueError("Research goal too short (min 10 characters)")
    if len(goal) > 500:
        raise ValueError("Research goal too long (max 500 characters)")

    # No malicious content
    dangerous_patterns = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers
        r"\$\{.*\}",  # Template injection
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, goal, re.IGNORECASE):
            raise ValueError("Invalid characters in research goal")

    # Strip whitespace
    return goal.strip()
```

### 4. Secrets Management

```python
# ❌ BAD: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"

# ✅ GOOD: Environment variables
import os

API_KEY = os.environ.get("CO_SCIENTIST_API_KEY")
if not API_KEY:
    raise RuntimeError("CO_SCIENTIST_API_KEY environment variable required")

# ✅ BETTER: Secret manager (production)
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
secret_name = "projects/PROJECT_ID/secrets/co-scientist-api-key/versions/latest"
response = client.access_secret_version(request={"name": secret_name})
API_KEY = response.payload.data.decode("UTF-8")
```

### 5. Timeout Configuration

```python
# Configure reasonable timeouts
TIMEOUT_CONFIG = {
    "connect": 5.0,  # Connection timeout
    "read": 120.0,   # Read timeout (LLM can be slow)
}

response = requests.post(
    API_URL,
    json=payload,
    timeout=(TIMEOUT_CONFIG["connect"], TIMEOUT_CONFIG["read"])
)
```

### 6. Error Handling (No Info Leakage)

```python
# ❌ BAD: Expose internal details
@app.exception_handler(Exception)
async def handle_error(request, exc):
    return JSONResponse({
        "error": str(exc),  # Could leak internal paths, SQL, etc.
        "traceback": traceback.format_exc()
    })

# ✅ GOOD: Generic error message
@app.exception_handler(Exception)
async def handle_error(request, exc):
    # Log full error internally
    logger.error(f"Internal error: {exc}", exc_info=True)

    # Return generic message to user
    return JSONResponse({
        "error": "An internal error occurred",
        "request_id": request.state.request_id  # For support lookup
    }, status_code=500)
```

## Multi-Factor Authentication (Optional)

For high-security deployments:

```python
import pyotp

class MFAValidator:
    """TOTP-based multi-factor authentication."""

    def generate_secret(self, user_id: str) -> str:
        """Generate MFA secret for user."""
        secret = pyotp.random_base32()

        # Store in database
        # db.store_mfa_secret(user_id, secret)

        return secret

    def generate_qr_code(self, user_id: str, secret: str) -> str:
        """Generate QR code for authenticator app."""
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user_id,
            issuer_name="AI Co-Scientist"
        )

        # Generate QR code image
        import qrcode
        qr = qrcode.make(uri)

        # Return data URL or save to file
        return uri

    def verify_code(self, user_id: str, code: str) -> bool:
        """Verify TOTP code."""
        # Fetch secret from database
        # secret = db.get_mfa_secret(user_id)
        secret = "stored_secret"

        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 30s window


# Usage during login
mfa = MFAValidator()

@app.command()
def login():
    """Login with MFA."""
    # Step 1: Username/password
    username = typer.prompt("Username")
    password = typer.prompt("Password", hide_input=True)

    # Verify credentials
    if not verify_credentials(username, password):
        typer.echo("Invalid credentials")
        raise typer.Exit(1)

    # Step 2: MFA code
    mfa_code = typer.prompt("MFA Code (from authenticator app)")

    if not mfa.verify_code(username, mfa_code):
        typer.echo("Invalid MFA code")
        raise typer.Exit(1)

    # Issue token
    typer.echo("✓ Login successful")
```

## Conclusion

This authentication and security guide provides:

1. **OAuth 2.1 with PKCE** for secure authorization
2. **JWT validation** for stateless authentication
3. **Scope-based access control** with hierarchical permissions
4. **Rate limiting** to prevent abuse
5. **Comprehensive audit logging** for compliance
6. **Security best practices** for production deployment
7. **Optional MFA** for high-security environments

Both CLI and MCP implementations should follow these patterns to ensure security, compliance, and user trust.
