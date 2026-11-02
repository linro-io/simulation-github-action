# Changelog

## v2.0.0 (unreleased)

The CLI is downloaded from your Linro install, not anonymously from the
marketplace (ENG-1730). The marketplace is going to require a key for
downloads, and a customer's CI has no marketplace key; it has a Linro PAT.

- The action downloads `linro-simulator` from
  `<server>/api/simulator/download/<version>/<os>-<arch>.tar.gz` with `token`
  as `Authorization: Bearer`. The install fetches it from the marketplace with
  its own key and checks the marketplace's sha256; the action checks the file
  again against the install's `X-Linro-Sha256` header.
- **Breaking:** `server` and `token` are required on every run, dry runs
  included.
- **Breaking:** the `marketplace-url` input is removed.
- `server` must be `https://`, or plain `http://` to a loopback install, so the
  token never crosses the network in clear.
- A refused token (401), a token without `SCOPE_SIMULATIONS` (403), an
  unknown version (404) and an unreachable install are reported separately.

Needs an install that serves the simulator download. `@v1` keeps downloading
anonymously from the marketplace until the marketplace requires a key for
downloads.

## v1.1.1 and earlier

See the [releases](https://github.com/linro-io/simulation-github-action/releases).
