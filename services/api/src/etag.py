"""ETag utility for HTTP caching support.

This module provides ETag generation and validation for API responses,
enabling efficient caching via HTTP 304 Not Modified responses.

Based on Session 12 requirements for tool-friendly APIs.
"""
import hashlib
import json
from typing import Any, Dict
from fastapi import Request, Response
from fastapi.responses import JSONResponse


def compute_etag(body: Dict[str, Any]) -> str:
    """Compute an ETag hash for a response payload.

    The ETag is a weak validator (prefixed with W/) computed from the
    SHA-256 hash of the JSON-serialized response body with sorted keys.

    Args:
        body: The response payload dictionary to hash

    Returns:
        str: ETag string in format W/"<hash>" (e.g., W/"a3f5b2c8...")

    Example:
        >>> compute_etag({"page": 1, "items": [{"id": 1}]})
        'W/"a3f5b2c8d4e1f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"'
    """
    # Serialize with sorted keys for deterministic hashing
    json_str = json.dumps(body, sort_keys=True)
    digest = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    return f'W/"{digest}"'


def maybe_return_not_modified(
    request: Request,
    response: Response,
    payload: Dict[str, Any]
) -> Response:
    """Check If-None-Match header and return 304 if ETag matches.

    This function implements HTTP conditional request handling:
    1. Computes the ETag for the current payload
    2. Checks if client sent If-None-Match header with matching ETag
    3. Returns 304 Not Modified if match (no body, saves bandwidth)
    4. Returns the original response with ETag header if no match

    Args:
        request: FastAPI request object (to read If-None-Match header)
        response: The response to potentially return
        payload: The response payload dictionary

    Returns:
        Response: Either a 304 Not Modified response or the original response
                  with ETag header added

    Example:
        First request:
            Client: GET /exercises?page=1
            Server: 200 OK, ETag: W/"abc123", [data]

        Second request (data unchanged):
            Client: GET /exercises?page=1, If-None-Match: W/"abc123"
            Server: 304 Not Modified, ETag: W/"abc123", [no body]
    """
    # Compute ETag for current payload
    etag = compute_etag(payload)

    # Check if client sent If-None-Match header
    if_none_match = request.headers.get("if-none-match")

    # If ETags match, return 304 Not Modified (no body)
    if if_none_match == etag:
        not_modified = Response(status_code=304)
        not_modified.headers["ETag"] = etag
        # Optionally preserve other headers from original response
        if hasattr(response, 'headers'):
            for key in ["X-Total-Count", "X-Request-Id", "X-Response-Time"]:
                if key in response.headers:
                    not_modified.headers[key] = response.headers[key]
        return not_modified

    # No match - return original response with ETag header
    response.headers["ETag"] = etag
    return response


def add_etag_header(response: JSONResponse, payload: Dict[str, Any]) -> JSONResponse:
    """Add ETag header to a JSONResponse.

    Convenience function for adding ETag without If-None-Match checking.
    Useful for responses where 304 is not desired (e.g., POST/PATCH).

    Args:
        response: JSONResponse to add ETag to
        payload: The response payload dictionary

    Returns:
        JSONResponse: The same response with ETag header added
    """
    etag = compute_etag(payload)
    response.headers["ETag"] = etag
    return response
