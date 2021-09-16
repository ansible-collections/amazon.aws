#!/usr/bin/env python
"""
Reads an OpenSSH Public key and spits out the 'AWS' MD5 sum
The equivalent of

ssh-keygen -f id_rsa.pub -e -m PKCS8 | openssl pkey -pubin -outform DER | openssl md5 -c | cut -f 2 -d ' '

(but without needing the OpenSSL CLI)
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import hashlib
import sys
from Crypto.PublicKey import RSA

if len(sys.argv) == 0:
    ssh_public_key = "id_rsa.pub"
else:
    ssh_public_key = sys.argv[1]

with open(ssh_public_key, 'r') as key_fh:
    data = key_fh.read()

# Convert from SSH format to DER format
public_key = RSA.importKey(data).exportKey('DER')
md5digest = hashlib.md5(public_key).hexdigest()
# Format the md5sum into the normal format
pairs = zip(md5digest[::2], md5digest[1::2])
md5string = ":".join(["".join(pair) for pair in pairs])

print(md5string)
