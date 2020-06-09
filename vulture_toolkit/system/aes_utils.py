#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file is part of Vulture 3.

Vulture 3 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture 3 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture 3.  If not, see http://www.gnu.org/licenses/.
"""
__author__ = "Jérémie Jourdin"
__credits__ = [""]
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'System Utils SSL Toolkit'

import base64
import hashlib

from Crypto import Random
from Crypto.Cipher import AES


class AESCipher(object):

    def __init__(self, key):
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        try:
            raw = self._pad(raw)
            iv = Random.new().read(AES.block_size)
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
        except:
            return None
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        try:
            enc = base64.b64decode(enc)
            iv = enc[:AES.block_size]
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
        except:
            return None
        try:
            data = self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')
        except:
            return None
        return data

    def _pad(self, s):
        # Warning : special caracters in str count 1 while they count 2 in bytes
        len_s = len(bytes(s, 'utf8'))
        return s + (self.bs - len_s % self.bs) * chr(self.bs - len_s % self.bs)

    @staticmethod
    def _unpad(s):
        if ord(s[len(s)-1:]) > len(s):
            return None
        return s[:-ord(s[len(s)-1:])]