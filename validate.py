import re
import binascii
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import util

def byte_size(limit, target):
    if limit < len(target):
        raise Exception('Length is not less than %s bytes' % limit)


def field_is_sha256(sha, field_name=None):
    """Verifies a string is a possible SHA256 hash.

    Args:
        sha (str): Hash to verify.
    """
    if not re.match(r'^[A-Fa-f0-9]{64}$', sha):
        raise Exception('Field is not a hash' if field_name is None else 'Field %s is not a hash' % field_name)


def rsa(public_key, signature, message):
    """Verifies an RSA signature.
    Args:
        public_key (str): Public key with BEGIN and END sections.
        signature (str): Hex value of the signature with its leading 0x stripped.
        message (str): Message that was signed, unhashed.
    """
    try:
        public_rsa = load_pem_public_key(bytes(public_key), backend=default_backend())
        hashed = util.sha256(message)
        public_rsa.verify(
            binascii.unhexlify(signature),
            hashed,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except InvalidSignature:
        raise Exception('Invalid signature')


def sha256(sha, message, name=None):
    """Verifies the hash matches the SHA256'd message.

    Args:
        sha (str): A SHA256 hash result.
        message (str): Message to hash and compare to.
    """
    if not sha == util.sha256(message):
        raise Exception('SHA256 does not match message' if name is None else 'SHA256 of %s does not match hash' % name)
