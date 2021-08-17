def parse_address(address):
    s = address.split(':', 1)
    host = s[0].strip() or 'localhost'
    if len(s) == 1:
        return (host, None)
    return (host, int(s[1] or 0))
