"""变异策略 - AFL 风格算子"""
import os
import random
import struct
from typing import List

def bit_flip(data: bytearray, width: int = 1) -> bytearray:
    if not data: return data
    result = bytearray(data)
    pos = random.randint(0, len(data) * 8 - width)
    for i in range(width):
        byte_pos, bit_off = (pos + i) // 8, (pos + i) % 8
        result[byte_pos] ^= (1 << bit_off)
    return result

def byte_flip(data: bytearray, width: int = 1) -> bytearray:
    if len(data) < width: return data
    result = bytearray(data)
    pos = random.randint(0, len(data) - width)
    for i in range(width): result[pos + i] ^= 0xFF
    return result

def arith_add(data: bytearray) -> bytearray:
    if not data: return data
    result = bytearray(data)
    pos = random.randint(0, len(data) - 1)
    result[pos] = (result[pos] + random.randint(1, 35)) & 0xFF
    return result

def set_interesting_byte(data: bytearray) -> bytearray:
    if not data: return data
    result = bytearray(data)
    result[random.randint(0, len(data) - 1)] = random.choice([0, 1, 127, 128, 255])
    return result

def havoc(data: bytearray, rounds: int = 16, extra_corpus: List[bytes] = None) -> bytearray:
    ops = [bit_flip, byte_flip, arith_add, set_interesting_byte]
    result = bytearray(data)
    for _ in range(rounds):
        result = random.choice(ops)(result)
    return result

FORMAT_STRING_PAYLOADS = [b"%s", b"%x", b"%n", b"%s%s%s%s"]
OVERFLOW_PAYLOADS = [b"A" * 256, b"A" * 1024, b"\x00" * 256]
ALL_SPECIAL_PAYLOADS = FORMAT_STRING_PAYLOADS + OVERFLOW_PAYLOADS
