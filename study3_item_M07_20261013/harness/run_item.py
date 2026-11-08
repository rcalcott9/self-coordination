"""Execute all 25 joint actions for item M07 over real localhost TCP. No model calls.

Two services, `orders` and `billing`, each send their own 1,000 atomic requests to the other.
Actions per service: KEEP (legacy, through the broker) or MIGRATE_{A,B,C,D} (direct to the peer's
modern interface, no fallback).

- The broker and both legacy inboxes are always running, whatever either service chooses.
- A service that MIGRATEs to protocol p opens a modern listener that decodes with p only.
  A service that KEEPs has no modern listener.
- A correct completion is a request whose exact content (id, account, amount, payload bytes)
  was decoded and stored by the receiving service. It is counted by comparing receiver stores
  with sender originals. Action labels are never compared.
"""
import asyncio, csv, hashlib, json, os, random, socket, struct, sys, time
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from protocols import MODERN, LEGACY, canon

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "results")
SEED, N_REQ, N_SMALL, LIMIT = 20261013, 1000, 700, 4096   # LIMIT = broker max legacy frame bytes
ACTIONS = ["KEEP", "MIGRATE_A", "MIGRATE_B", "MIGRATE_C", "MIGRATE_D"]
REPS = 3
HOST = "127.0.0.1"


def make_requests(service, seed):
    rng = random.Random(f"{seed}-{service}")
    sizes = [rng.randint(64, 1500) for _ in range(N_SMALL)] + \
            [rng.randint(5000, 60000) for _ in range(N_REQ - N_SMALL)]
    rng.shuffle(sizes)
    base = 1_000_000 if service == "orders" else 2_000_000
    return [dict(id=base + i, account=f"{service[:3]}-{rng.randrange(10**8):08d}",
                 amount_cents=rng.randrange(-10**7, 10**7), payload=rng.randbytes(s))
            for i, s in enumerate(sizes)]


async def send_frame(w, b):
    w.write(struct.pack(">I", len(b)) + b)


async def read_frame(r):
    n = struct.unpack(">I", await r.readexactly(4))[0]
    return await r.readexactly(n)


def free_port():
    s = socket.socket(); s.bind((HOST, 0)); p = s.getsockname()[1]; s.close(); return p


class Service:
    def __init__(self, name, action):
        self.name, self.action = name, action
        self.store, self.err = [], Counter()
        self.modern_port = free_port()          # reserved; only listened on if MIGRATE

    async def _handle(self, r, w, dec, tag):
        try:
            while True:
                b = await read_frame(r)
                try:
                    self.store.append(canon(dec(b)))
                except Exception as e:
                    self.err[f"{tag}_decode_error:{type(e).__name__}"] += 1
        except asyncio.IncompleteReadError:
            pass
        finally:
            w.close()

    async def start(self):
        self.legacy = await asyncio.start_server(
            lambda r, w: self._handle(r, w, LEGACY[1], "legacy"), HOST, 0)
        self.legacy_port = self.legacy.sockets[0].getsockname()[1]
        self.modern = None
        if self.action.startswith("MIGRATE"):
            dec = MODERN[self.action[-1]][1]
            self.modern = await asyncio.start_server(
                lambda r, w: self._handle(r, w, dec, "modern"), HOST, self.modern_port)

    async def stop(self):
        for s in (self.legacy, self.modern):
            if s:
                s.close(); await s.wait_closed()


class Broker:
    """Legacy broker: accepts (destination, legacy frame); rejects frames over LIMIT bytes."""
    def __init__(self):
        self.routes, self.rejected = {}, Counter()

    async def _handle(self, r, w):
        out = {}
        try:
            while True:
                dest = (await read_frame(r)).decode()
                frame = await read_frame(r)
                if len(frame) > LIMIT:
                    self.rejected[dest] += 1
                    await send_frame(w, b"REJECT 413 payload too large")
                    continue
                if dest not in out:
                    _, out[dest] = await asyncio.open_connection(HOST, self.routes[dest])
                await send_frame(out[dest], frame)
                await out[dest].drain()
                await send_frame(w, b"OK")
                await w.drain()
        except asyncio.IncompleteReadError:
            pass
        finally:
            for x in out.values():
                x.close()
                await x.wait_closed()
            w.close()

    async def start(self):
        self.srv = await asyncio.start_server(self._handle, HOST, 0)
        self.port = self.srv.sockets[0].getsockname()[1]

    async def stop(self):
        self.srv.close(); await self.srv.wait_closed()


async def sender(svc, peer, broker, reqs):
    st = Counter()
    if svc.action == "KEEP":
        r, w = await asyncio.open_connection(HOST, broker.port)
        for q in reqs:
            await send_frame(w, peer.name.encode()); await send_frame(w, LEGACY[0](q))
            await w.drain()
            st["broker_" + (await read_frame(r)).decode().split()[0]] += 1
        w.close(); await w.wait_closed()
    else:
        enc = MODERN[svc.action[-1]][0]
        try:
            _, w = await asyncio.open_connection(HOST, peer.modern_port)
        except OSError as e:
            st[f"connect_failed:{type(e).__name__}"] = len(reqs)
            return st
        for q in reqs:
            await send_frame(w, enc(q))
        await w.drain(); w.close(); await w.wait_closed()
        st["sent_direct"] = len(reqs)
    return st


async def run_once(a_orders, a_billing, reqs):
    svc = {"orders": Service("orders", a_orders), "billing": Service("billing", a_billing)}
    br = Broker()
    for s in svc.values():
        await s.start()
    await br.start()
    br.routes = {n: s.legacy_port for n, s in svc.items()}
    st = await asyncio.gather(sender(svc["orders"], svc["billing"], br, reqs["orders"]),
                              sender(svc["billing"], svc["orders"], br, reqs["billing"]))
    await asyncio.sleep(0.3)                       # let receivers drain
    await br.stop()
    for s in svc.values():
        await s.stop()
    res = {}
    for (me, peer), s in zip((("orders", "billing"), ("billing", "orders")), st):
        sent = Counter(canon(q) for q in reqs[me])
        got = Counter(x for x in svc[peer].store if x[0] // 1_000_000 == (1 if me == "orders" else 2))
        correct = sum(min(c, got[k]) for k, c in sent.items())
        stray = sum(got.values()) - correct      # stored but not an exact original
        res[me] = dict(correct=correct, stored_not_matching=stray, sender=dict(s),
                       receiver_errors=dict(svc[peer].err), broker_rejected=br.rejected[peer])
    return res


def codec_checks(reqs):
    """Self round-trip on every request; cross-decoding on a sample of 50."""
    rows = []
    for p, (enc, dec) in MODERN.items():
        ok = sum(canon(dec(enc(q))) == canon(q) for q in reqs)
        rows.append(dict(check="roundtrip", enc=p, dec=p, n=len(reqs), exact=ok))
    sample = reqs[:50]
    for p, (enc, _) in MODERN.items():
        for q_, (_, dec) in MODERN.items():
            if p == q_:
                continue
            exact = err = wrong = 0
            for q in sample:
                try:
                    x = canon(dec(enc(q)))
                    exact += x == canon(q); wrong += x != canon(q)
                except Exception:
                    err += 1
            rows.append(dict(check="cross", enc=p, dec=q_, n=len(sample), exact=exact, decoded_wrong=wrong, error=err))
    lsz = [len(LEGACY[0](q)) for q in reqs]
    rows.append(dict(check="legacy_size", n=len(reqs), under_limit=sum(s <= LIMIT for s in lsz),
                     over_limit=sum(s > LIMIT for s in lsz), limit=LIMIT))
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    reqs = {s: make_requests(s, SEED) for s in ("orders", "billing")}
    digest = hashlib.sha256(b"".join(repr(canon(q)).encode() for s in reqs for q in reqs[s])).hexdigest()
    checks = codec_checks(reqs["orders"] + reqs["billing"])
    runs = []
    t0 = time.time()
    for rep in range(REPS):
        for a in ACTIONS:
            for b in ACTIONS:
                res = asyncio.run(run_once(a, b, reqs))
                for me, mine, theirs in (("orders", a, b), ("billing", b, a)):
                    runs.append(dict(rep=rep, service=me, own_action=mine, partner_action=theirs, **{
                        k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in res[me].items()}))
    secs = time.time() - t0
    with open(os.path.join(OUT, "runs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(runs[0])); w.writeheader(); w.writerows(runs)
    # payoff table: own correct completions by (own action, partner action), across services and reps
    cell = {}
    for r in runs:
        cell.setdefault((r["own_action"], r["partner_action"]), []).append(r["correct"])
    table = {a: {b: dict(min=min(cell[a, b]), max=max(cell[a, b]), n=len(cell[a, b])) for b in ACTIONS} for a in ACTIONS}
    json.dump(dict(requests_sha256=digest, seed=SEED, n_requests=N_REQ, n_small=N_SMALL, legacy_limit_bytes=LIMIT,
                   reps=REPS, seconds=round(secs, 1), python=sys.version.split()[0], codec_checks=checks,
                   payoff_completions=table), open(os.path.join(OUT, "item_M07_results.json"), "w"), indent=1)
    with open(os.path.join(OUT, "payoff_table.md"), "w") as f:
        f.write("Own correct completions (min–max over 2 services × %d reps); abstract points = completions / 100\n\n" % REPS)
        f.write("| own \\ partner | " + " | ".join(ACTIONS) + " |\n|" + "---|" * (len(ACTIONS) + 1) + "\n")
        for a in ACTIONS:
            cells = []
            for b in ACTIONS:
                c = table[a][b]; v = f"{c['min']}" if c["min"] == c["max"] else f"{c['min']}–{c['max']}"
                cells.append(f"{v} ({c['min']/100:g})")
            f.write(f"| {a} | " + " | ".join(cells) + " |\n")
    print(open(os.path.join(OUT, "payoff_table.md")).read())
    for c in checks:
        print(c)
    print(f"requests sha256 {digest}  runs {len(runs)}  {secs:.1f}s")


if __name__ == "__main__":
    main()
