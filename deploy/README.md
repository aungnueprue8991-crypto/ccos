# NEXUS x CCOS Production Deploy

See SETUP_PLAN.md and scripts/setup_and_run.sh for host install.

## Docker
```bash
export NEXUS_HOME=$HOME/.nexus
mkdir -p "$NEXUS_HOME"
cp deploy/docker/.env.example "$NEXUS_HOME/.env" && chmod 600 "$NEXUS_HOME/.env"
docker compose -f deploy/docker/docker-compose.yml up -d --build
```

## Helm
```bash
helm upgrade --install nexus ./deploy/k8s -n nexus --create-namespace
```

## systemd
```bash
sudo cp deploy/systemd/nexus-supervisor.service /etc/systemd/system/
sudo systemctl enable --now nexus-supervisor
```
