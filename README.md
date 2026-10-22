# access_log_combined_format_parser

Parses Apache/Nginx combined access log lines into typed fields. Standard library only, no dependencies.

```python
from access_log_combined_format_parser import parse_log_line

entry = parse_log_line(
    '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
    '"GET /apache_pb.gif HTTP/1.0" 200 2326 '
    '"http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
)
print(entry.method, entry.path, entry.status, entry.size)
# GET /apache_pb.gif 200 2326
```

## Why this exists

The combined log format is common enough that many ad-hoc parsers are copy-pasted between projects, and they tend to fall over on the same edges: the size field is a hyphen for zero-byte responses, the request line can contain spaces, and the referer and user-agent fields are quoted strings that may themselves contain quotes-adjacent garbage. This library exists to parse that format correctly once, with no dependencies, so that callers get typed fields and a clear error when a line is malformed.

The trade-off: this library parses the combined format and only the combined format. If you need the common log format (no referer/user-agent), or a custom `LogFormat` string, this is not the right tool — wrapping it to handle multiple formats would mean guessing what the caller intended, and that guesswork is what makes most log parsers unreliable.

## Edge cases you will hit

- **Size field is `-`.** Apache writes `-` when no response body is sent; Nginx writes `0`. This library normalises the hyphen to `None` (not `0`) so you can tell the two cases apart. `0` stays `0`.
- **Trailing newline.** A single trailing newline is accepted; everything else in the line must match the format exactly. Leading whitespace is not trimmed, because real log lines are space-delimited and a stray leading space is usually a sign of corruption you want to see, not hide.
- **Malformed request line.** The request field must contain exactly three space-separated tokens (method, path, protocol). Anything else raises `ParseError`.
- **Timestamp is a string.** The timestamp is returned as-is (without brackets). Parsing it to a `datetime` is left to you, because the timezone offset in the log is worth preserving verbatim and different callers want different handling.

## Exports

- `parse_log_line(line: str) -> LogEntry` — parse one line; raises `ParseError` (subclass of `ValueError`) on failure.
- `LogEntry` — frozen dataclass with fields: `remote_host`, `ident`, `remote_user`, `timestamp`, `method`, `path`, `protocol`, `status` (int), `size` (int or None), `referer`, `user_agent`. Also exposes `datetime` as a property alias of `timestamp`.
- `ParseError` — raised on malformed input.

## Running the tests

```
PYTHONPATH=src python -m unittest discover -s tests
```
