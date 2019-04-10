from __future__ import print_function
import platform
from pyeclib.ec_iface import ECDriver
import sys

# libisal2 is not available for non-amd64 architectures
arch = platform.machine()
if sys.argv[1].startswith('isa_') and arch != 'x86_64':
    print("Skipping {} test for {} architecture".format(sys.argv[1], arch))
else:
    input = b'test'

    # Init
    print("init:", end=" ")
    ec = ECDriver(k=3, m=3, hd=3, ec_type=sys.argv[1])
    print("OK")

    # Encode
    print("encode:", end=" ")
    fragments = ec.encode(input)
    print("OK")

    # Decode
    print("decode:", end=" ")
    assert ec.decode(fragments[0:ec.k]) == input
    print("OK")
