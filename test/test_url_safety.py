import unittest

from url_safety import is_public_address

PUBLIC = [
    "93.184.216.34",
    "8.8.8.8",
    "2606:2800:220:1:248:1893:25c8:1946",
    "::ffff:8.8.8.8",
    "64:ff9b::808:808",
]

NON_PUBLIC = [
    "127.0.0.1",
    "127.1.2.3",
    "10.0.0.1",
    "172.16.0.1",
    "192.168.1.1",
    "169.254.169.254",
    "100.100.100.200",
    "100.64.0.1",
    "0.0.0.0",
    "255.255.255.255",
    "224.0.0.1",
    "239.255.255.250",
    "240.0.0.1",
    "198.18.0.1",
    "192.0.2.1",
    "::1",
    "::",
    "fe80::1",
    "fe80::1%en0",
    "fc00::1",
    "fd00:ec2::254",
    "ff02::1",
    "::ffff:127.0.0.1",
    "::ffff:169.254.169.254",
    "64:ff9b::7f00:1",
    "64:ff9b::a9fe:a9fe",
    "2002:7f00:1::",
    "2002:a9fe:a9fe::",
    "2001:0:4136:e378:8000:63bf:80ff:fffe",
]

MALFORMED = [
    "",
    "localhost",
    "example.com",
    "999.1.1.1",
    "1.2.3",
    "::g",
    "127.0.0.1:80",
    " 8.8.8.8",
]


class TestIsPublicAddress(unittest.TestCase):
    def test_public_addresses_are_allowed(self) -> None:
        for address in PUBLIC:
            with self.subTest(address=address):
                self.assertTrue(is_public_address(address))

    def test_non_public_addresses_are_rejected(self) -> None:
        for address in NON_PUBLIC:
            with self.subTest(address=address):
                self.assertFalse(is_public_address(address))

    def test_malformed_input_is_rejected(self) -> None:
        for address in MALFORMED:
            with self.subTest(address=address):
                self.assertFalse(is_public_address(address))


if __name__ == "__main__":
    unittest.main()
