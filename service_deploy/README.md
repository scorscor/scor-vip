# scor.vip Deployment

This directory contains the deployment command for the current server.

Run from the repository root:

```powershell
.\deploy.bat
```

The script connects with `ssh/tencentmain_ssh/config`, pulls:

```text
ghcr.io/scorscor/scor-vip:main
```

and restarts Docker Compose under:

```text
/opt/scor-vip
```

If the GHCR package is private, set `GHCR_TOKEN` locally before deployment:

```powershell
$env:GHCR_TOKEN = "your_github_pat"
.\deploy.bat
```

The remote container binds to `127.0.0.1:5003` and stores SQLite data in the
Docker volume `scor-vip-data`.

The current server Docker daemon uses the local proxy
`http://127.0.0.1:10809`, backed by the LA VLESS Reality server, to speed up
GHCR image pulls.
