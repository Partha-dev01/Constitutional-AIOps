# Non-secret deployment config shared by the quickstart scripts. Safe to commit.
# (These identify AWS resources but are NOT credentials — useless without your AWS keys.)

$AiopsRegion     = "us-east-1"
$AiopsInstanceId = "i-0123456789abcdef0"        # the GPU VM (g6.xlarge L4)
$AiopsDomain     = "https://aiops.imaginaerium.in"

# Secrets (app/grafana/ingest passwords) live in secrets.local.ps1 (gitignored).
# Copy secrets.example.ps1 -> secrets.local.ps1 and fill it in. Scripts load it
# automatically when present.
