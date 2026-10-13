#!/bin/bash
# One-time setup: lets GitHub Actions deploy this repo to Cloud Run without a key.
#
#     CLOUDSDK_PYTHON=/opt/homebrew/opt/python@3.12/bin/python3.12 scripts/setup_github_deploy.sh
#
# GitHub proves to Google which repo and branch a workflow runs on (Workload
# Identity Federation). Only pushes to main of Prod-Discovery/agent-design-guidelines
# are accepted. There is no secret to store in GitHub. Safe to run again.
set -e

PROJECT_ID="prod-vpepf-cm"
REPO="Prod-Discovery/agent-design-guidelines"
POOL="github"
PROVIDER="agent-design-guidelines"
DEPLOYER="github-deployer"
RUNTIME_SA="assess-agent@${PROJECT_ID}.iam.gserviceaccount.com"   # the site runs as this; it may call Vertex AI
DEPLOYER_SA="${DEPLOYER}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$PROJECT_ID"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
gcloud services enable iamcredentials.googleapis.com sts.googleapis.com run.googleapis.com \
    cloudbuild.googleapis.com artifactregistry.googleapis.com

gcloud iam workload-identity-pools describe "$POOL" --location=global >/dev/null 2>&1 || \
    gcloud iam workload-identity-pools create "$POOL" --location=global --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers describe "$PROVIDER" --location=global \
    --workload-identity-pool="$POOL" >/dev/null 2>&1 || \
    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" --location=global \
        --workload-identity-pool="$POOL" --display-name="agent-design-guidelines (main)" \
        --issuer-uri="https://token.actions.githubusercontent.com" \
        --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
        --attribute-condition="assertion.repository=='${REPO}' && assertion.ref=='refs/heads/main'"

# The deployer can deploy from source and nothing else.
gcloud iam service-accounts describe "$DEPLOYER_SA" >/dev/null 2>&1 || \
    gcloud iam service-accounts create "$DEPLOYER" --display-name="GitHub Actions deployer (agent-design-guidelines)"
for role in roles/run.sourceDeveloper roles/serviceusage.serviceUsageConsumer; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$DEPLOYER_SA" \
        --role="$role" --condition=None >/dev/null
done
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
    --member="serviceAccount:$DEPLOYER_SA" --role=roles/iam.serviceAccountUser >/dev/null
gcloud iam service-accounts add-iam-policy-binding "$DEPLOYER_SA" \
    --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${REPO}" \
    --role=roles/iam.workloadIdentityUser >/dev/null

echo ""
echo "Done. These go in .github/workflows/deploy.yml:"
echo "  workload_identity_provider: projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"
echo "  service_account: ${DEPLOYER_SA}"
