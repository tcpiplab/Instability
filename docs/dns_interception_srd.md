# SRD: DNS Checks That Cannot Fail

## 1. Purpose

Three tools report success unconditionally on any host running a macOS DNS
proxy network extension. `check_internet_connection` will report "Connected"
with the WAN cable unplugged. `check_dns_root_servers` and `check_dns_resolvers`
will report every server reachable when none of them is.

This document records what was measured, fixes the two tools that can be fixed,
and makes the third report honestly that it cannot run rather than passing.

## 2. Background

### 2.1 How it was found

A consumer of this toolkit (a voice assistant that speaks tool results aloud)
removed a language model from its narration path, cutting a network-check turn
from roughly 22 seconds to under one. The operator noticed that a check of
thirteen root servers across the internet was answering in under a second,
including a subprocess spawn, and asked why. Nothing in this repository changed.

### 2.2 What is intercepted

Measured 2026-08-29 on macOS 25.6.0. Every row has a negative control: an
address that must not be able to answer. `240.0.0.1` is in reserved space and is
not routable; `192.0.2.1`, `198.51.100.1` and `203.0.113.1` are RFC 5737
documentation ranges.

| Signal | Real host | Negative control | Verdict |
| --- | --- | --- | --- |
| UDP/53 | answers | **answers** | intercepted |
| TCP/53 | answers | **answers** | intercepted |
| UDP/53, `IP_BOUND_IF` to en0 | `ENXIO` | `ENXIO` | no bypass |
| UDP/53, source bound to en0 | answers | **answers** | no bypass |
| TCP/443 | connects | times out | clean |
| TCP/853 (DoT) | connects | times out | clean |
| ICMP echo | replies 2.6-65.9 ms | times out | clean |

The answers returned are *correct* — they match Cloudflare DoH byte for byte,
and a nonexistent name correctly yields NXDOMAIN — so this is a real resolver
answering on behalf of every destination, not a wildcard hijacker.

### 2.3 What is doing it

Nothing is listening on port 53 (`lsof -nP -iUDP:53 -iTCP:53` is empty) and the
routing table is ordinary (default via `en0` to the LAN gateway, for the root
server addresses and for `240.0.0.1` alike). The host runs Tailscale, whose
`io.tailscale.ipn.macsys.network-extension` is loaded, with `scutil --dns`
reporting nameserver `100.100.100.100` and a `.ts.net` search domain.

That is a **`NEDNSProxyProvider`**: a macOS DNS proxy network extension, which
captures DNS flows system-wide at the flow level rather than by binding a port
or installing a route. This is why no socket option reaches it. It is not a
misconfiguration and it is working as designed; the defect is that these tools
cannot tell.

**Do not treat this as Tailscale-specific.** Any DNS proxy extension, corporate
VPN client, or captive portal produces the same result. The fix must detect the
*condition*, not the vendor.

### 2.4 The consequence, stated plainly

A check that cannot fail is worse than no check. It converts "I do not know"
into "everything is fine", and it does so at exactly the moment a user is asking
because they suspect it is not.

## 3. Scope

In scope:

- `check_internet_connection`: move off port 53 entirely.
- `check_dns_resolvers`: query over DoT, which is not intercepted.
- `check_dns_root_servers`: detect interception and refuse to pass; report ICMP
  reachability as a clearly-labelled weaker signal.
- A shared `dns_interception_detected()` helper.
- A third result state, "could not be checked", distinct from reachable and
  unreachable.

Out of scope:

- Defeating the extension. Section 5.1 records that it cannot be done from an
  unprivileged process, with the measurements behind that.
- Changing anyone's Tailscale configuration.
- IPv6. The tables here are IPv4 and the probes were IPv4.
- The other DNS tools in the registry (`dns_diagnostics.py`, reverse lookups),
  which resolve names rather than test specific servers and are not making a
  reachability claim.

## 4. Goals

1. No tool reports a server reachable on the strength of a query that never left
   the machine.
2. Every reachability claim is backed by a signal with a passing negative
   control.
3. "Could not be checked" is a distinct outcome and never renders as success.
4. The detection works for any DNS proxy, not just Tailscale.
5. Tools that can be genuinely fixed are genuinely fixed, not merely annotated.

## 5. Architecture

### 5.1 There is no bypass, and this is measured rather than assumed

Two approaches were tried and both are recorded so they are not re-proposed:

- **`IP_BOUND_IF`** (`setsockopt(IPPROTO_IP, 25, if_index)` on `en0`) failed with
  `OSError: [Errno 6] Device not configured` for every destination including a
  real root server, so it did not even reach the question.
- **Source-address binding** (`bind(("192.168.1.244", 0))`) succeeded in sending,
  and the negative control still answered. The flow is captured regardless of
  which interface address it leaves from.

This follows from what a `NEDNSProxyProvider` is: the system hands matching
flows to the extension before they reach the network stack's routing decision.
An unprivileged process cannot opt out. Do not spend time here again.

### 5.2 Detection: a negative control at runtime

```
dns_interception_detected() -> bool
```

Sends one A query for a fixed name to `240.0.0.1` — reserved space, not
routable, guaranteed to have nothing behind it — with a short timeout. **Any
response at all means DNS is being intercepted**, because a response is
impossible otherwise.

Three properties matter:

- It is cheap in the case that matters. When interception is present the reply
  arrives in under 10 ms, so the tools that need to know pay almost nothing.
  When it is absent the probe costs its timeout, so the timeout is short
  (`DNS_INTERCEPTION_PROBE_TIMEOUT`, 1.5 s) and the result is cached for the
  process lifetime.
- It tests the condition, not the vendor. A corporate VPN or captive portal that
  answers for every destination is caught by the same probe.
- It fails toward *reporting a problem*, not toward silence. If the probe itself
  errors, the answer is "unknown", which the callers treat as "cannot verify" —
  the same direction as detecting interception, never as an all-clear.

### 5.3 `check_internet_connection`: move off port 53

Currently `socket.create_connection((DNS_TEST_SERVERS[0], 53), timeout=3)`. The
port is incidental — nothing about this check needs DNS, it needs one TCP
handshake with a host on the internet.

Port 443 is not intercepted (measured: `1.1.1.1:443` connects, both
documentation addresses time out at 4 s), so the fix is to connect on 443 and to
try more than one host before concluding the internet is down. This tool is
fully repaired: it will report Disconnected when the WAN is down, which it
cannot do today.

### 5.4 `check_dns_resolvers`: query over DoT

DoT (TCP/853) is not intercepted and reaches the real resolver. Measured against
all ten entries in `DEFAULT_DNS_RESOLVERS`:

| Resolver | TCP/853 | DoT query |
| --- | --- | --- |
| Google primary and secondary | open | answered |
| Cloudflare primary and secondary | open | answered |
| OpenDNS primary and secondary | open | answered |
| Quad9 primary and secondary | open | answered |
| **Comodo primary and secondary** | **timeout** | **not available** |
| negative controls | timeout | timed out |

Eight of ten are genuinely checkable. **Comodo Secure DNS offers no DoT**, and
its port 53 answer is the interceptor's, so on an intercepted host it cannot be
checked at all. It is reported as `UNKNOWN`, not as reachable and not as
unreachable — see 5.6.

Each resolver needs its DoT hostname for certificate validation, so
`DEFAULT_DNS_RESOLVERS` gains a per-entry hostname. Where a resolver has none,
that is the marker that it is not DoT-capable.

When `dns_interception_detected()` is false, plain port-53 queries are used as
before: they are faster, they test the actual service on the actual port, and
there is nothing wrong with them on a clean host.

### 5.5 `check_dns_root_servers`: it cannot be fixed, so it must not pass

The root servers are the one case with no repair available.

- They serve DNS on port 53 only, which is captured.
- Encrypted DNS is not a uniform escape route. Measured across five roots: B
  accepts TCP/853 but presents a certificate that does not verify, F accepts
  TCP/443, A and K time out on both, M refuses on 443. There is no path that
  works for all thirteen.

So under interception this tool reports that the check **could not be performed**
and why. It never reports the roots reachable on the strength of a query that
did not leave the machine.

ICMP is offered alongside, explicitly labelled as a weaker claim — it shows a
host answers a ping, not that it serves DNS. Two caveats, both measured, and
both of which must reach the output rather than being smoothed over:

- **G-root (192.112.36.4) and L-root (199.7.83.42) do not answer ICMP**, across
  repeated attempts with retries. Eleven of thirteen reply, in 2.6 to 65.9 ms.
  Reporting 11/13 as "two root servers are down" would be a false negative, so
  non-response to ICMP is reported as "did not answer a ping", never as down.
- **Reply validation is load-bearing.** A first version of the probe counted any
  received ICMP packet as a reply, and a router's destination-unreachable for
  `240.0.0.1` read as a 2310 ms success. A reply counts only if it is an echo
  reply (type 0) carrying our own payload and coming from the address queried.
  The negative controls exist to catch exactly this, and did.

Unprivileged ICMP works on macOS via `SOCK_DGRAM` with `IPPROTO_ICMP`, so no
elevation is needed. On a platform where that raises `PermissionError`, ICMP is
skipped and only the interception verdict is reported.

### 5.6 A third result state

Both DNS tools return three states per server rather than two:

| State | Meaning |
| --- | --- |
| `REACHABLE` | A signal with a passing negative control confirmed it |
| `UNREACHABLE` | Such a signal was attempted and failed |
| `UNKNOWN` | No trustworthy signal was available from this host |

`UNKNOWN` is the whole point of this document. It covers Comodo on any host, and
every root server on an intercepted one. Summary lines must never fold `UNKNOWN`
into either of the others, and the count of `UNKNOWN` servers is always stated.

### 5.7 A predicted defect, deliberately not asserted

Root servers are not recursive: queried for `example.com A` they return a
*referral* to the `.com` nameservers, with an empty answer section.
`dns.resolver.Resolver.resolve()` raises `NoAnswer` on an empty answer section.
If both hold, `check_dns_server` has always reported every root server
unreachable on a clean host, and only the interception has been masking it.

**This is a prediction, not a measurement.** It could not be verified here: the
interception prevents seeing a real root response, and the one root accepting
DoT presents an unverifiable certificate. It is recorded rather than acted on.

The redesign sidesteps the question regardless by querying `.` `NS`, which the
roots answer authoritatively from the zone they actually serve. That is the
correct query for "is this root server serving" whether or not the prediction
holds. Confirm it on a host with no DNS proxy before closing this section.

## 6. Configuration

New constants in `config.py`:

| Constant | Value | Meaning |
| --- | --- | --- |
| `DNS_INTERCEPTION_PROBE_ADDRESS` | `240.0.0.1` | Reserved; nothing may answer |
| `DNS_INTERCEPTION_PROBE_TIMEOUT` | `1.5` | Short: the clean case pays this |
| `DOT_PORT` | `853` | DNS over TLS |
| `INTERNET_CHECK_PORT` | `443` | Was 53, which is intercepted |
| `INTERNET_CHECK_HOSTS` | 3 addresses | More than one before declaring down |
| `ICMP_PROBE_TIMEOUT` | `3` | Per attempt |

## 7. Failure modes

| Failure | Behaviour |
| --- | --- |
| DNS intercepted | Root check reports UNKNOWN with the reason; resolvers use DoT |
| Interception probe errors | Treated as "cannot verify", never as clean |
| DoT unavailable for a resolver | That resolver is UNKNOWN, others unaffected |
| ICMP needs root on this platform | ICMP skipped; interception verdict still reported |
| A root does not answer ICMP | "did not answer a ping", never "down" |
| Everything clean | Plain port-53 queries, as today, but for `.` NS |

No row produces a false pass. That is the one property this document exists to
guarantee.

## 8. Testing

- `dns_interception_detected()` against a stub that answers the reserved address
  (must report intercepted) and one that times out (must report clean).
- The ICMP reply validator against an echo reply, a destination-unreachable, a
  reply from a different address, and a truncated packet. Only the first counts.
- Three-state reporting: a summary containing an `UNKNOWN` must not claim all
  servers reachable, asserted for every summary-line generator.
- `check_internet_connection` against an unreachable host list must return
  Disconnected — the case that is impossible to produce today.

## 9. Known limitations

1. **The root server check cannot be repaired on an intercepted host.** It can
   only be honest. Turning off the DNS proxy's "override local DNS" setting is
   the only way to restore it, and that is the operator's decision, not this
   tool's.
2. **DoT tests the resolver's DoT service**, which is not byte-for-byte the same
   service as its port 53. A resolver could in principle serve one and not the
   other. This is a far smaller gap than the one it replaces.
3. **Comodo cannot be checked from an intercepted host at all.**
4. Section 5.7's prediction is unverified.
5. Measured on one host, one OS version, one VPN client. The negative-control
   discipline is what makes the result portable, not the specific numbers.
