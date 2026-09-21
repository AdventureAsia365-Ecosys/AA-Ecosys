#!/usr/bin/env bash
# Open an SSM port-forwarding tunnel from a bastion EC2 (in the RDS VPC) to the
# RDS endpoint, mapping it to localhost:5432 for local SQL clients (SQLTools).
#
# Prereqs:
#   - AWS CLI v2 + session-manager-plugin installed
#   - MFA creds loaded into env (see docs/db-access-ssm-tunnel.md §2)
#   - A bastion EC2 online in SSM (docs/db-access-ssm-tunnel.md §4)
#
# Usage:
#   ./docs/db-tunnel.sh <bastion-instance-id> <rds-host> [local-port]
#
# Example:
#   ./docs/db-tunnel.sh i-0abc123 aa-cis-dev-db.xxxx.us-west-1.rds.amazonaws.com
#
# Keep this terminal open while you query. Ctrl+C closes the tunnel.
set -euo pipefail

REGION="us-west-1"
REMOTE_PORT="5432"

BASTION_ID="${1:-}"
RDS_HOST="${2:-}"
LOCAL_PORT="${3:-5432}"

if [[ -z "$BASTION_ID" || -z "$RDS_HOST" ]]; then
  echo "Usage: $0 <bastion-instance-id> <rds-host> [local-port]" >&2
  exit 1
fi

echo "Tunnel: localhost:${LOCAL_PORT} -> ${RDS_HOST}:${REMOTE_PORT} via ${BASTION_ID} (${REGION})"
echo "Keep this open. Ctrl+C to close."

exec aws ssm start-session \
  --region "$REGION" \
  --target "$BASTION_ID" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"${RDS_HOST}\"],\"portNumber\":[\"${REMOTE_PORT}\"],\"localPortNumber\":[\"${LOCAL_PORT}\"]}"
