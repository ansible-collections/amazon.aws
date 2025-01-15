#!/usr/bin/env python
"""
Reads an OpenSSH Public key and spits out the 'AWS' MD5 sum
The equivalent of

ssh-keygen -f id_rsa.pub -e -m PKCS8 | openssl pkey -pubin -outform DER | openssl md5 -c | cut -f 2 -d ' '

(but without needing the OpenSSL CLI)
"""

import hashlib
import sys

from cryptography.hazmat.primitives import serialization

if len(sys.argv) == 0:
    ssh_public_key = "id_rsa.pub"
else:
    ssh_public_key = sys.argv[1]

with open(ssh_public_key, "rb") as key_file:
    public_key = serialization.load_ssh_public_key(
        key_file.read(),
    )
pub_der = public_key.public_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
md5digest = hashlib.md5(pub_der).hexdigest()
# Format the md5sum into the normal format
pairs = zip(md5digest[::2], md5digest[1::2])
md5string = ":".join(["".join(pair) for pair in pairs])

print(md5string)
