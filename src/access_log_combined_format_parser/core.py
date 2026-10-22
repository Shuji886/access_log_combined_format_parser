from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class LogEntry:
    """Typed representation of one Apache/Nginx combined access log line.

    Fields map to the combined log format in field order. `ident` is kept
    even though modern servers almost always log a literal hyphen for it;
    dropping the field would silently change the layout this library
    claims to parse.
    """
    remote_host: str
    ident: str
    remote_user: str
    timestamp: str
    method: str
    path: str
    protocol: str
    status: int
    size: Optional[int]
    referer: str
    user_agent: str

    @property
    def datetime(self) -> str:
        """The date/time portion of the timestamp, without brackets.

        Kept as a string rather than parsed to a `datetime` because the
        log value carries an explicit timezone offset that callers may want
        to preserve verbatim. Parsing is left to the caller.
        """
        return self.timestamp


# Sample line, for reference when reading the regex below:
# 1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] "GET /path HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
_PATTERN = re.compile(
    r'^'
    r'(?P<remote_host>\S+)'
    r'\s+'
    r'(?P<ident>\S+)'
    r'\s+'
    r'(?P<remote_user>\S+)'
    r'\s+'
    r'\[(?P<timestamp>[^\]]+)\]'
    r'\s+'
    r'"(?P<request>[^"]*)"'
    r'\s+'
    r'(?P<status>\d{3})'
    r'\s+'
    r'(?P<size>\S+)'
    r'\s+'
    r'"(?P<referer>[^"]*)"'
    r'\s+'
    r'"(?P<user_agent>[^"]*)"'
    r'\s*$'
)


class ParseError(ValueError):
    """Raised when a line does not match the combined log format.

    Subclassing `ValueError` keeps the error familiar to callers who use
    `except ValueError` for malformed input while still allowing this
    library to be singled out.
    """


def _split_request(request: str) -> List[str]:
    """Split the request line into method, path, protocol.

    A single space splits each token, matching what servers actually write.
    Any other count is treated as malformed: we return an empty list so the
    caller can raise a clear error rather than guessing which token is missing.
    """
    if not request:
        return []
    parts = request.split(' ')
    if len(parts) != 3:
        return []
    return parts


def _parse_size(raw: str) -> Optional[int]:
    """Convert the size field, tolerating the literal hyphen for 0-byte responses.

    Apache writes `-` when no body is sent; Nginx writes `0`. We normalise the
    hyphen to `None` rather than `0` so callers can tell the two cases apart
    if they need to. A genuinely numeric value is never mapped to `None`.
    """
    if raw == '-':
        return None
    return int(raw)


def parse_log_line(line: str) -> LogEntry:
    """Parse a single Apache/Nginx combined access log line.

    The combined format is:
        host ident user [time] "request" status size "referer" "agent"

    `line` must be a single complete log entry with its trailing newline
    already stripped. Leading or trailing whitespace beyond a single optional
    newline is not trimmed: real log lines are space-delimited, not
    arbitrary-whitespace-delimited, and silently trimming would hide the kind
    of corruption callers usually want to see.

    Raises `ParseError` if the line does not match.
    """
    match = _PATTERN.match(line)
    if match is None:
        raise ParseError(f"line does not match combined log format: {line!r}")

    request = match.group('request')
    parts = _split_request(request)
    if not parts:
        raise ParseError(f"malformed request field: {request!r}")
    method, path, protocol = parts

    status = int(match.group('status'))
    size = _parse_size(match.group('size'))

    return LogEntry(
        remote_host=match.group('remote_host'),
        ident=match.group('ident'),
        remote_user=match.group('remote_user'),
        timestamp=match.group('timestamp'),
        method=method,
        path=path,
        protocol=protocol,
        status=status,
        size=size,
        referer=match.group('referer'),
        user_agent=match.group('user_agent'),
    )
