import unittest

from access_log_combined_format_parser import parse_log_line, LogEntry, ParseError


class TestParseLogLine(unittest.TestCase):
    def test_typical_line(self):
        line = (
            '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] '
            '"GET /apache_pb.gif HTTP/1.0" 200 2326 '
            '"http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"'
        )
        entry = parse_log_line(line)
        self.assertIsInstance(entry, LogEntry)
        self.assertEqual(entry.remote_host, '127.0.0.1')
        self.assertEqual(entry.ident, '-')
        self.assertEqual(entry.remote_user, 'frank')
        self.assertEqual(entry.timestamp, '10/Oct/2000:13:55:36 -0700')
        self.assertEqual(entry.datetime, '10/Oct/2000:13:55:36 -0700')
        self.assertEqual(entry.method, 'GET')
        self.assertEqual(entry.path, '/apache_pb.gif')
        self.assertEqual(entry.protocol, 'HTTP/1.0')
        self.assertEqual(entry.status, 200)
        self.assertEqual(entry.size, 2326)
        self.assertEqual(entry.referer, 'http://www.example.com/start.html')
        self.assertEqual(entry.user_agent, 'Mozilla/4.08 [en] (Win98; I ;Nav)')

    def test_size_hyphen_becomes_none(self):
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET / HTTP/1.1" 304 - "-" "Mozilla/5.0"'
        )
        entry = parse_log_line(line)
        self.assertIsNone(entry.size)
        self.assertEqual(entry.status, 304)

    def test_size_zero_is_int_zero_not_none(self):
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET / HTTP/1.1" 200 0 "-" "Mozilla/5.0"'
        )
        entry = parse_log_line(line)
        self.assertEqual(entry.size, 0)
        self.assertIsNotNone(entry.size)

    def test_trailing_newline_accepted(self):
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET / HTTP/1.1" 200 1234 "-" "Mozilla/5.0"\n'
        )
        entry = parse_log_line(line)
        self.assertEqual(entry.remote_host, '1.2.3.4')
        self.assertEqual(entry.size, 1234)

    def test_referer_and_user_agent_hyphens(self):
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET / HTTP/1.1" 200 1234 "-" "-"'
        )
        entry = parse_log_line(line)
        self.assertEqual(entry.referer, '-')
        self.assertEqual(entry.user_agent, '-')

    def test_path_with_query_string(self):
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET /search?q=cats&sort=asc HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'
        )
        entry = parse_log_line(line)
        self.assertEqual(entry.path, '/search?q=cats&sort=asc')

    def test_path_with_encoded_space(self):
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET /some%20path HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'
        )
        entry = parse_log_line(line)
        self.assertEqual(entry.path, '/some%20path')

    def test_missing_trailing_fields_raises(self):
        line = '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] "GET / HTTP/1.1" 200 1234'
        with self.assertRaises(ParseError):
            parse_log_line(line)

    def test_garbage_raises(self):
        with self.assertRaises(ParseError):
            parse_log_line('not a log line')

    def test_empty_line_raises(self):
        with self.assertRaises(ParseError):
            parse_log_line('')

    def test_malformed_request_field_raises(self):
        # request is "GET /" (two tokens, not three)
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET /" 200 1234 "-" "Mozilla/5.0"'
        )
        with self.assertRaises(ParseError):
            parse_log_line(line)

    def test_protocol_with_spaces_in_request_handled(self):
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET /path HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'
        )
        entry = parse_log_line(line)
        self.assertEqual(entry.method, 'GET')
        self.assertEqual(entry.path, '/path')
        self.assertEqual(entry.protocol, 'HTTP/1.1')

    def test_negative_status_format_rejected(self):
        # status must be exactly 3 digits
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET / HTTP/1.1" abc 1234 "-" "Mozilla/5.0"'
        )
        with self.assertRaises(ParseError):
            parse_log_line(line)

    def test_remote_user_hyphen(self):
        line = (
            '1.2.3.4 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET / HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'
        )
        entry = parse_log_line(line)
        self.assertEqual(entry.remote_user, '-')

    def test_ipv6_remote_host(self):
        line = (
            '2001:db8::1 - - [01/Jan/2023:12:00:00 +0000] '
            '"GET / HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'
        )
        entry = parse_log_line(line)
        self.assertEqual(entry.remote_host, '2001:db8::1')


if __name__ == '__main__':
    unittest.main()
