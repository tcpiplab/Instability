# SRD: Exchange point and WHOIS checks that report standing failures

Status: implemented 2026-11-23
Companion: phonebot's `docs/SRD_infrastructure_checks.md`, which holds the
measurements and the reason another program now reads these two reports.

## 1. Problem

`monitor_ixp_connectivity` and `check_whois_servers` each reported failures on
every run that were not outages. Phonebot is about to speak both results over a
telephone, where a failure that is always present trains the listener to ignore
the one that matters. Measured on 2026-11-23:

| Tool | Reported | Cause |
|---|---|---|
| `monitor_ixp_connectivity` | 5 of 6, in 10.3 s | The Equinix status page answers `HTTP 403` to non-browser clients. The tool counted only 200 as success and spent 7 s retrying. |
| `check_whois_servers` | 29 of 35, in 35.7 s | Six server names have no address in DNS. They are retired. |

Three further defects were found in the same reading.

- `check_whois_servers` passed its report through a language model
  (`ollama_shorten_output`) before returning it. A model could therefore rewrite
  the counts and names that the check had measured, and the model call was part
  of the 35.7 s.
- `monitor_ixp_connectivity` returned a dictionary with no `success` key, so
  manual mode printed `Error: Unknown error` after a run that had worked.
- Both tools tested their targets one after another. One dead exchange website
  could hold the IXP check for 67 s under its defaults.

## 2. Requirements

### 2.1 `monitor_ixp_connectivity`

1. A site has answered when it returns any HTTP status below 500. An answer is
   never retried. A connection failure, a timeout or a 5xx status is retried.
2. The sites are tested concurrently. The defaults are a 10-second timeout and
   one retry, which bounds the whole check near 21 s.
3. The tool returns a standardized success result whenever it ran, including
   when no site answered. `stdout` holds a plain-text report. The four keys the
   tool used to return are kept at the top level and in `parsed_data`.
4. The report says that the check requests each exchange's public website and
   does not test traffic crossing the exchange.
5. The `error` field of a failed site is a short fixed category. The exception
   text is kept apart in `error_detail`.

### 2.2 `check_whois_servers`

1. The six retired servers are removed from `WHOIS_SERVERS_DICT`.
2. The servers are tested concurrently with a 5-second connection timeout, and
   the failures are retried once after one second. The worst case is 11 s.
3. The report is built by `format_whois_report` and returned whole. No language
   model touches it, and it is never truncated, because it lists failures last
   and a cut report would look like an all-clear.
4. A failure is described by one of four fixed phrases. No text from the remote
   server or from the operating system's error message enters the report.

### 2.3 Report formats

Other programs parse both reports, so these lines are fixed.

```
IXP websites answering: 5/6
IXP Websites That Answered (5):
- DE-CIX Frankfurt (HTTP 200, 257 ms)
IXP Websites That Did Not Answer (1):
- LINX London: Connection timeout
All IXP websites answered.
```

```
Checked 29 WHOIS servers on port 43.
Reachable WHOIS Servers (29):
- whois.arin.net
Unreachable WHOIS Servers (1):
- whois.nic.io: timed out
All WHOIS servers were reachable.
```

The last line of each block appears only when nothing failed.

## 3. Result

After the change, on the same machine and the same day,
`monitor_ixp_connectivity` reported 6 of 6 in 1.2 s and `check_whois_servers`
reported 29 of 29 in 1.8 s.

## 4. Testing

`tests/test_infrastructure_checks.py` runs offline with every network call
stubbed. It includes the negative controls: a 503, a timeout and a TLS failure
are still reported as failures, and the WHOIS check can report every server
unreachable with every failure listed.

## 5. Known limitations

- The WHOIS check connects by name, so a DNS failure on this host reports every
  server as `name did not resolve`. The report distinguishes that from a
  timeout, and a reader should treat 29 such lines as a DNS fault.
- Port 43 WHOIS is being retired by registries of generic top-level domains.
  More servers will leave DNS, and each one will again show as a standing
  failure until it is removed from the list.
- An exchange's website can be hosted far from the exchange. The check is a
  sample of distant websites and is worded as one.
