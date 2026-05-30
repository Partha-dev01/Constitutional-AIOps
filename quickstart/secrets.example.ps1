# Copy this file to  secrets.local.ps1  (which is gitignored) and fill in real
# values. NEVER commit real credentials — this repo is public.
#
#   Copy-Item secrets.example.ps1 secrets.local.ps1   # then edit

$AppUser    = "admin"                 # APP basic-auth (Caddy) username
$AppPass    = "REPLACE_ME"            # APP basic-auth password
$IngestUser = "edge"                  # /ingest/* machine username (for edge monitoring)
$IngestPass = "REPLACE_ME"            # /ingest/* machine password

# The live values are stored on the VM in /mnt/aiops-repo/.env.production
# (APP_BASIC_AUTH_*, INGEST_BASIC_AUTH_*). Grafana/Neo4j passwords are there too.
