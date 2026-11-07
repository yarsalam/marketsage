# Portable worker runtime and sandbox policy gate

**Status:** policy/contract prototype only. No process executor or OS sandbox is implemented by this PR.

## Trust boundaries

- Controller: validates immutable task identity, manifest, owner confirmation, reviewed default-branch commit and sandbox capability evidence.
- Worker: receives one approved launch plan, a read-only checkout, bounded isolated temp space and a fresh minimal environment. It receives no controller credentials, trading credentials, raw market datasets or arbitrary host files.
- Source forge: GitHub is only a source-of-code provider. A PR head is untrusted input and is not eligible for local/self-hosted execution merely because its checks pass.

## Runtime profile

A runtime profile pins a SHA-256 image digest and declares platform/architecture, non-root UID, memory, CPU, wall-clock, process-count, temp-storage and output-byte ceilings. Floating image tags and out-of-bounds limits are rejected.

## Mandatory sandbox attestation

Before a launch plan can be produced, the executor must attest to read-only root and checkout, no network, no new privileges, non-root execution, dropped capabilities, seccomp, user/mount/PID namespaces, no host PID/network/mounts, isolated temporary storage, and actual resource limits no larger than the immutable task profile.

This module does not enforce those properties. A concrete runtime (for example an appropriately configured OCI/container or OS-level sandbox) must enforce and independently test them. Plain subprocess, a Python virtual environment, or a container with a shared privileged host daemon is not sufficient proof of isolation.

## Filesystem and environment policy

Paths must be normalized relative paths; absolute paths, parent traversal, drive/scheme syntax and symlink components are rejected. The helper is only a preflight check; a real executor must use directory-FD/openat-style no-follow operations to prevent time-of-check/time-of-use races.

The process environment is constructed from a small allowlist and is never inherited from the controller. PATH, HOME, proxy variables, credentials, cloud metadata and arbitrary host variables must be supplied only by the fixed executor profile or omitted.

Output bytes are bounded. Only sanitized summaries and test reports are allowed. Raw logs, secret values, local paths and market data are prohibited.

## Validation

Tests cover immutable runtime digest, non-root UID, resource bounds, missing sandbox controls, digest mismatch, path traversal, symlink rejection, environment/secret leakage, output caps, manifest policy, and untrusted task rejection.

## Not yet proven

No concrete sandbox engine, image build, reproducible lock file, kernel/namespace compatibility, cgroup enforcement, egress filter, process termination, cross-runtime conformance or two-real-harness execution is included. Do not claim that this PR creates a runnable or 24/7 worker. The next implementation must select a zero-cost executor available on the target host, validate its actual OS controls, then run the same harmless contract in two independently configured local/fake backends.