"""Personal keys for the Siri Shortcut.

A key looks like "h4e_" + 40 random characters. Only its SHA-256 hash is
stored, so a database leak can't be used to log food for anyone; the key is
shown once when it is created. A key can only log food by voice: it is not a
sign-in token and can't read or change anything else.
"""

import hashlib
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import abort, g, request

from database import db
from models import ApiToken

PREFIX = "h4e_"
MAX_KEYS_PER_USER = 5


def _hash(key):
    return hashlib.sha256(key.encode()).hexdigest()


def create_token(user_id, name, zone_name):
    if db.session.query(ApiToken).filter_by(user_id=user_id).count() >= MAX_KEYS_PER_USER:
        raise ValueError(f"You can have up to {MAX_KEYS_PER_USER} Siri keys. Delete one first.")
    key = PREFIX + secrets.token_urlsafe(30)
    token = ApiToken(user_id=user_id, token_hash=_hash(key), name=name, timezone=zone_name)
    db.session.add(token)
    db.session.commit()
    return token, key


def serialize_token(token):
    def iso(value):
        return value.replace(tzinfo=value.tzinfo or timezone.utc).isoformat() if value else None
    return dict(id=token.id, name=token.name, timezone=token.timezone,
                created_at=iso(token.created_at), last_used_at=iso(token.last_used_at))


def api_token_required(view):
    """Accept "Authorization: Bearer h4e_..." and set g.api_token."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        key = header[7:].strip() if header.lower().startswith("bearer ") else ""
        if not key.startswith(PREFIX):
            abort(401, description="Add your health4everyone Siri key to the Shortcut.")
        token = db.session.query(ApiToken).filter_by(token_hash=_hash(key)).first()
        if token is None:
            abort(401, description="This Siri key was deleted. Make a new one in Settings.")
        token.last_used_at = datetime.now(timezone.utc)
        g.api_token = token
        return view(*args, **kwargs)
    return wrapper
