#!/usr/bin/env bash
set -euo pipefail

PROJECT="accredivault"
docker compose -p "$PROJECT" restart
