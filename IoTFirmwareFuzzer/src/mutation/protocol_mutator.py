"""协议感知变异器 - MQTT/CoAP/HTTP"""
import os
import struct
import random
import logging
from typing import List

from .strategies import havoc, ALL_SPECIAL_PAYLOADS
from ..utils import encode_varint, encode_utf8_string

logger = logging.getLogger("IoTFuzzer.ProtocolMutator")

class MQTTMutator:
    def mutate(self, data: bytes, strategy: str = "hybrid") -> bytes:
        if len(data) < 2:
            return self._gen_connect()
        ptype = (data[0] >> 4) & 0x0F
        if strategy == "random" or random.random() < 0.3:
            result = bytearray(havoc(bytearray(data), rounds=8))
            result[0] = (result[0] & 0x0F) | (ptype << 4)
            return bytes(result)
        if ptype == 1: return self._mutate_connect(data)
        if ptype == 3: return self._mutate_publish(data)
        result = bytearray(havoc(bytearray(data), rounds=8))
        result[0] = (result[0] & 0x0F) | (ptype << 4)
        return bytes(result)

    def _mutate_connect(self, data: bytes) -> bytes:
        try:
            _, vlen = self._parse_remaining_length(data, 1)
            offset = 1 + vlen + 2 + 4 + 1 + 1 + 2  # 协议名+级别+flags+keepalive
            cid_len = struct.unpack_from(">H", data, offset)[0]
            cid_end = offset + 2 + cid_len
            result = bytearray(data)
            new_cid = random.choice([os.urandom(cid_len), b"../etc/passwd"[:cid_len], b"%s" * 10][:cid_len])
            result[offset + 2:cid_end] = bytearray(new_cid).ljust(cid_len, b"\x00")[:cid_len]
            return bytes(result)
        except Exception:
            return bytes(havoc(bytearray(data), rounds=4))

    def _mutate_publish(self, data: bytes) -> bytes:
        try:
            _, vlen = self._parse_remaining_length(data, 1)
            offset = 1 + vlen
            topic_len = struct.unpack_from(">H", data, offset)[0]
            topic_end = offset + 2 + topic_len
            result = bytearray(data)
            payload_start = topic_end
            if (data[0] >> 1) & 0x03 > 0: payload_start += 2
            result[payload_start:] = bytearray(havoc(bytearray(result[payload_start:]), rounds=16))
            return bytes(result)
        except Exception:
            return bytes(havoc(bytearray(data), rounds=8))

    def _parse_remaining_length(self, data: bytes, offset: int):
        value, consumed = 0, 0
        multiplier = 1
        while True:
            if offset + consumed >= len(data): raise ValueError("数据不足")
            b = data[offset + consumed]
            consumed += 1
            value += (b & 0x7F) * multiplier
            multiplier <<= 7
            if (b & 0x80) == 0: break
        return value, consumed

    def _gen_connect(self) -> bytes:
        cid = os.urandom(random.randint(1, 23))
        payload = encode_utf8_string(cid.decode("latin-1"))
        var = b"\x00\x04MQTT\x04\x02" + struct.pack(">H", 60)
        return b"\x10" + encode_varint(len(var + payload)) + var + payload

class CoAPMutator:
    def mutate(self, data: bytes) -> bytes:
        if len(data) < 4: return bytes([0x44, 0x01, 0, 0])
        result = bytearray(data)
        result = havoc(result, rounds=8)
        return bytes(result)

class HTTPMutator:
    def mutate(self, data: bytes) -> bytes:
        return bytes(havoc(bytearray(data), rounds=8))

class ProtocolMutator:
    def __init__(self, protocol: str = "mqtt", constraint: bool = True, havoc_rounds: int = 16):
        self.protocol = protocol.lower()
        self.constraint = constraint
        self.havoc_rounds = havoc_rounds
        self._mutators = {"mqtt": MQTTMutator(), "coap": CoAPMutator(), "http": HTTPMutator()}

    def mutate(self, data: bytes, strategy: str = "hybrid", corpus: List[bytes] = None) -> bytes:
        if not data: data = b"\x00"
        if self.constraint and self.protocol in self._mutators:
            try:
                m = self._mutators[self.protocol]
                return m.mutate(data, strategy) if self.protocol == "mqtt" else m.mutate(data)
            except Exception:
                pass
        return bytes(havoc(bytearray(data), rounds=self.havoc_rounds, extra_corpus=corpus or []))
