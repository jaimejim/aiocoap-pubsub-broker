# Development Rules

## First Message

If the user did not give a concrete task, read `README.md` to understand the project, then ask what to work on.

## Project Structure

```
broker.py       # CoAP pubsub broker (aiocoap resources)
client.py       # CLI client for all pubsub operations
codec.py        # CBOR/JSON encoding helpers, key maps, content formats
test_broker.py  # pytest-asyncio tests covering draft-19 operations
```

Single-package project, no monorepo. All source lives at the repo root.

## Spec Reference

This project implements [draft-ietf-core-coap-pubsub-19](https://datatracker.ietf.org/doc/draft-ietf-core-coap-pubsub/). The full draft text is in `draft-ietf-core-coap-pubsub.md`. Consult it when unsure about protocol behavior.

## Code Quality

- Python 3.12+ required
- Type hints on all new functions
- CBOR encoding uses numeric keys (see `TOPIC_KEYS` in `codec.py`), never string keys on the wire
- Content format constant: `CT_PUBSUB_CBOR = 606` lives in `codec.py`
- JSON is accepted as input fallback only; output is always `application/core-pubsub+cbor` (CT 606)
- Always ask before removing functionality or code that appears intentional

## aiocoap Pitfalls

These are easy to get wrong and waste debugging time:

- `aiocoap.Context.create_client_context()` is a coroutine, must be `await`ed. It does **not** support `async with` directly; wrap with `asynccontextmanager` if needed.
- iPATCH code: `aiocoap.numbers.codes.Code.iPATCH` (lowercase `i`). The handler method is named `render_ipatch`.
- Do **not** install `aiocoap[all]`; it pulls `lakers-python` (Rust/maturin) which has build issues. Use bare `aiocoap` from git.
- aiocoap git HEAD has iPATCH support; the stable PyPI release (0.4.7) does not. The project pins to git HEAD in `pyproject.toml`.

## Commands

- **Install deps**: `uv sync`
- **Run broker**: `uv run pubsub-broker`
- **Run client**: `uv run pubsub-client --help`
- **Run tests**: `uv run pytest test_broker.py -v`
- **Run single test**: `uv run pytest test_broker.py -v -k "test_name"`
- **Interactive demo**: `uv run pubsub-client demo coap://localhost` (requires running broker)

After code changes, run `uv run pytest test_broker.py -v` and fix all failures before committing.

NEVER run the broker as a background process during tests; the test suite starts its own server on port 15684.

## Testing

- Tests use `pytest-asyncio` with a per-test CoAP server on `localhost:15684`
- Test file: `test_broker.py`
- When writing tests, run them, identify issues, and iterate until fixed
- Do not modify or remove existing tests unless explicitly asked

## Git Rules

- NEVER commit unless the user asks
- Always use `git add <specific-files>`, never `git add -A` or `git add .`
- Before committing, run `git status` and verify only intended files are staged
- Never use `git reset --hard`, `git checkout .`, `git clean -fd`, or `git stash`

## Protocol Concepts

Key concepts an agent must understand:

| Concept | Description |
|---------|-------------|
| Topic collection | `/ps` - holds all topic configs |
| Topic config | `/ps/<id>` - CBOR resource with topic properties (rt=`core.ps.conf`) |
| Topic data | `/ps/data/<id>` - the actual published payload (rt=`core.ps.data`) |
| HALF CREATED | Config exists but no data published yet (GET on data returns 4.04) |
| FULLY CREATED | Data has been published at least once |
| `initialize` | Property on creation that pre-populates topic-data immediately |
| `max-subscribers` | Enforced limit; excess subscribers get response without Observe option |
| `conf-filter` | iPATCH with CBOR key 10; selects which properties to return in config reads |

## Client Subcommands

`client.py` exposes these via `pubsub-client`: `create`, `read`, `update`, `delete`, `subscribe`, `publish`, `demo`. Each maps to the corresponding draft-19 operation.

## Style

- Keep answers short and concise
- No fluff or filler text
- Technical prose, be direct
- No em dashes in prose; use comma, colon, or rephrase
