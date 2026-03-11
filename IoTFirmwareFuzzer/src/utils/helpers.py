"""通用工具函数"""
import os
import hashlib
import struct
import random
import time
from typing import List, Tuple

def encode_varint(value: int) -> bytes:
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value > 0:
            byte |= 0x80
        result.append(byte)
        if value == 0:
            break
    return bytes(result)

def decode_varint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    multiplier = 1
    value = 0
    pos = offset
    while True:
        if pos >= len(data):
            raise ValueError("varint 数据不完整")
        byte = data[pos]
        pos += 1
        value += (byte & 0x7F) * multiplier
        multiplier <<= 7
        if (byte & 0x80) == 0:
            break
        if multiplier > 128 * 128 * 128:
            raise ValueError("varint 值超出范围")
    return value, pos - offset

def encode_utf8_string(s: str) -> bytes:
    encoded = s.encode("utf-8")
    return struct.pack(">H", len(encoded)) + encoded

def sha256_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def timestamp_ms() -> int:
    return int(time.time() * 1000)

def safe_mkdir(path: str):
    os.makedirs(path, exist_ok=True)

def format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def interesting_uint8() -> List[int]:
    return [0, 1, 16, 32, 64, 100, 127, 128, 200, 254, 255]

def interesting_uint16() -> List[int]:
    return [0, 1, 256, 512, 1000, 32767, 32768, 65534, 65535]

def interesting_uint32() -> List[int]:
    return [0, 1, 256, 65535, 65536, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
