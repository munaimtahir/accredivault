#!/usr/bin/env bash
set -euo pipefail

PROJECT="accredivault"
docker ps --filter "label=com.docker.compose.project=$PROJECT"
