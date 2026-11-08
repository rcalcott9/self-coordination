"""Wire codecs for item M07. Stdlib only.

A request is a dict: id (int), account (str), amount_cents (int), payload (bytes).
Four modern protocols (A-D) encode every request, whatever its size. The legacy
codec is used only through the broker, which enforces a payload-size limit.
Decoders raise on malformed input; they are never told which codec produced a frame.
"""
import base64, json, struct, zlib
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, parse_qs


def _canon(r):
    return (int(r["id"]), str(r["account"]), int(r["amount_cents"]), bytes(r["payload"]))


# A: JSON object, payload base64
def enc_A(r):
    return json.dumps({"id": r["id"], "account": r["account"], "amount_cents": r["amount_cents"],
                       "payload": base64.b64encode(r["payload"]).decode()}).encode()


def dec_A(b):
    o = json.loads(b.decode("utf-8"))
    return dict(id=int(o["id"]), account=str(o["account"]), amount_cents=int(o["amount_cents"]),
                payload=base64.b64decode(o["payload"], validate=True))


# B: XML document, payload hex
def enc_B(r):
    e = ET.Element("request", id=str(r["id"]), account=r["account"], amount_cents=str(r["amount_cents"]))
    e.text = r["payload"].hex()
    return ET.tostring(e)


def dec_B(b):
    e = ET.fromstring(b)
    if e.tag != "request":
        raise ValueError("not a request element")
    return dict(id=int(e.get("id")), account=e.get("account"), amount_cents=int(e.get("amount_cents")),
                payload=bytes.fromhex(e.text or ""))


# C: fixed binary layout: uint64 id, 16-byte account, int64 amount, uint32 length, raw payload
_HC = struct.Struct(">Q16sqI")


def enc_C(r):
    return _HC.pack(r["id"], r["account"].encode().ljust(16, b"\0"), r["amount_cents"], len(r["payload"])) + r["payload"]


def dec_C(b):
    i, acc, amt, n = _HC.unpack_from(b, 0)
    body = b[_HC.size:]
    if len(body) != n:
        raise ValueError("length field does not match frame")
    return dict(id=i, account=acc.rstrip(b"\0").decode("ascii"), amount_cents=amt, payload=body)


# D: zlib-compressed URL-encoded form, payload base85
def enc_D(r):
    return zlib.compress(urlencode({"id": r["id"], "account": r["account"], "amount_cents": r["amount_cents"],
                                    "payload": base64.b85encode(r["payload"]).decode()}).encode())


def dec_D(b):
    q = parse_qs(zlib.decompress(b).decode("ascii"), strict_parsing=True)
    return dict(id=int(q["id"][0]), account=q["account"][0], amount_cents=int(q["amount_cents"][0]),
                payload=base64.b85decode(q["payload"][0]))


# Legacy: one text line, fields separated by '|', payload base64. Used only via the broker.
def enc_L(r):
    return f'{r["id"]}|{r["account"]}|{r["amount_cents"]}|{base64.b64encode(r["payload"]).decode()}'.encode()


def dec_L(b):
    i, acc, amt, p = b.decode("ascii").split("|")
    return dict(id=int(i), account=acc, amount_cents=int(amt), payload=base64.b64decode(p, validate=True))


MODERN = {"A": (enc_A, dec_A), "B": (enc_B, dec_B), "C": (enc_C, dec_C), "D": (enc_D, dec_D)}
LEGACY = (enc_L, dec_L)
canon = _canon
