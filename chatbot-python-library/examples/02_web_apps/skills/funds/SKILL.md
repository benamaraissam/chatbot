---
name: funds
description: Orchestrate the bnpp_fund_search tool to answer questions about BNP Paribas AM funds (lists, filtering, performance summaries, pagination).
when_to_use: The user asks anything about funds, ISINs, fund performance, share classes, asset classes, or the BNP Paribas catalog.
triggers: [fund, funds, isin, nav, asset class, share class, bnpp, bnp paribas]
version: "1.0"
tags: [finance, bnp]
---

# BNP Paribas AM fund search

You have a `bnpp_fund_search` tool wired to BNP Paribas AM's public fund-search
API. This skill explains how to use it well.

## Tool signature

```
bnpp_fund_search(profile: str = "PV_LU-FSE", language: str = "ENG", offset: int = 0, limit: int = 25)
```

- `profile` controls which country/platform catalog is queried. `PV_LU-FSE`
  covers the Luxembourg professional retail set. Other typical values include
  `PV_FR-RET`, `PV_BE-RET`. If the user doesn't specify, leave the default.
- `language` is a 3-letter language code. Default `ENG`. Set to `FRA` for
  French descriptions if the user prefers.
- `offset` / `limit` are auto-injected — the tool returns an envelope with
  `{total, offset, limit, returned, has_more, items}`. The maximum supported
  limit is 500.

## How to handle common requests

### "List all funds" / "How many funds are there?"
Call once with `limit=500` — that covers the typical catalog in a single
request. The envelope's `total` field is the count.

### "Show me the top performers" / "Filter by asset class"
The tool itself doesn't filter — call once with `limit=500` to get the slim
projection, then filter, sort, or aggregate the `items` list yourself in your
reasoning before answering. Each item carries the fields needed for ranking:
`ytd`, `perf_1y`, `perf_3y`, `nav`, `asset_class`, `currency`.

### "Find a specific fund by ISIN"
Same call (`limit=500`), then look up the ISIN in `items`. If not found, tell
the user the catalog doesn't include it; suggest trying a different `profile`.

### "Paginate slowly"
Only paginate (small `limit`, walking `offset`) if the user explicitly asks for
a few funds at a time. For "give me everything", one big call is faster and
cheaper.

## Answer style

- Always cite the ISIN alongside the fund name.
- Report performance numbers exactly as returned (they're already in percent
  units in this API; don't multiply by 100).
- If the user asks "is this fund good?", report the data but make clear you
  cannot make investment recommendations.
