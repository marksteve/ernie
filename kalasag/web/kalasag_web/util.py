import binascii
import os

def rand_str(n):
  return binascii.hexlify(os.urandom(n))
