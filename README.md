# vk-shared-gcp

Shared Google Cloud primitives for vkscraper8 Python services.

The package targets Python `>=3.14,<3.15` and keeps service policy out of the library: no settings imports, no environment fallback chains, no service SQL, and no telemetry coupling.

Downstream install line after `v0.1.0` is published:

```toml
"vk-shared-gcp @ git+https://github.com/Defmon3/vk_shared_gcp.git@v0.1.0"
```
