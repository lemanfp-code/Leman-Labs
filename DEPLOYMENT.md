# Déploiement en ligne — Dossier Synthesizer

Cible : VPS Hetzner + Docker + Cloudflare Tunnel + auth HTTP Basic.
Aucune installation côté collaborateurs : ils ouvrent une URL, saisissent
un identifiant/mot de passe, c'est tout.

Coût : VPS Hetzner CX22 ≈ **3,79 €/mois** · Cloudflare Tunnel **gratuit**.

> Les étapes ci-dessous (VPS) nécessitent **tes** comptes (Hetzner,
> Cloudflare, GitHub). L'app est déjà prête : auth intégrée, Dockerfile,
> compose, healthcheck `/healthz`.

---

## ⭐ Variante recommandée : local + lien consultation (0 €, sans VPS)

Modèle retenu : **toi seul génères** les synthèses (en local), les
collaborateurs **consultent** les dossiers via un lien, en lecture seule.

### 1. Configurer les 2 rôles dans `.env` (local)

```
ANTHROPIC_API_KEY=sk-ant-...        # ta clé (reprends celle de CRY/.env)
CLAUDE_MODEL=claude-sonnet-4-6
WHISPER_MODEL=small
PORT=8000
BASIC_AUTH_USER=ahcene              # TOI : accès complet (génération)
BASIC_AUTH_PASS=<mot de passe fort>
VIEWER_AUTH_USER=equipe             # EUX : consultation seule
VIEWER_AUTH_PASS=<mot de passe partagé à l'équipe>
```

### 2. Lancer l'app

```bash
python run.py            # → http://localhost:8000 (toi, opérateur)
```

### 3. Exposer un lien gratuit pour l'équipe (au choix)

- **Tailscale Funnel** (URL stable `https://<machine>.ts.net`, HTTPS auto,
  gratuit) : `tailscale funnel 8000`
- ou **Cloudflare quick tunnel** (URL aléatoire, gratuit, sans compte) :
  `cloudflared tunnel --url http://localhost:8000`

Tu partages à l'équipe l'**URL + l'identifiant visiteur** (`equipe / …`).
Ils voient la même interface, mais sans bouton de génération : ils
choisissent le programme, parcourent la bibliothèque de dossiers, lisent
et téléchargent. Toute génération/suppression leur est refusée (403).

> Ton Mac doit être allumé pendant qu'ils consultent. Pour un outil
> mensuel, tu lances l'app quand tu publies un dossier et tu laisses
> tourner le temps utile. Zéro coût, zéro serveur.

---

## VPS (option 24/7) — Hetzner

## 1. Créer le VPS (Hetzner Cloud)

1. console.hetzner.cloud → New Server
2. Image **Ubuntu 24.04**, type **CX22** (2 vCPU / 4 Go), datacenter EU
3. Ajouter ta clé SSH → Create
4. Noter l'IP publique, puis : `ssh root@<IP>`

## 2. Installer Docker

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
```

## 3. Récupérer le code (repo privé)

Le repo `ahc20/dossier-synthesizer` est privé → il faut un accès lecture.
Option simple : générer un **Personal Access Token** GitHub (scope `repo`,
lecture seule suffit) puis :

```bash
git clone https://<TOKEN>@github.com/ahc20/dossier-synthesizer.git
cd dossier-synthesizer
```

(Alternative propre : ajouter une **deploy key** SSH au repo.)

## 4. Configurer le `.env` (jamais commité)

```bash
cp .env.example .env
nano .env
```

À renseigner :

```
ANTHROPIC_API_KEY=sk-ant-...        # ta vraie clé
CLAUDE_MODEL=claude-sonnet-4-6
WHISPER_MODEL=small
PORT=8000
BASIC_AUTH_USER=equipe              # identifiant partagé à l'équipe
BASIC_AUTH_PASS=<mot de passe fort> # ex. openssl rand -base64 18
```

> Sans `BASIC_AUTH_USER`/`PASS`, l'app démarre **sans protection**.
> Pour la mise en ligne ils sont **obligatoires**.

## 5. Lancer

```bash
docker compose up -d --build
docker compose logs -f          # vérifier le démarrage
curl -s localhost:8000/healthz  # → {"ok":true}
```

Le port n'est exposé que sur `127.0.0.1:8000` (voir `docker-compose.yml`) :
il n'est **pas** accessible depuis Internet directement — c'est voulu,
Cloudflare Tunnel s'en charge.

## 6. Exposer via Cloudflare Tunnel

1. Avoir un domaine géré par Cloudflare (même un sous-domaine suffit)
2. dash.cloudflare.com → Zero Trust → Networks → **Tunnels** → Create
3. Choisir **Cloudflared**, nommer le tunnel, copier le **token**
4. Dans `.env` du VPS, ajouter : `CLOUDFLARE_TUNNEL_TOKEN=<token>`
5. Décommenter le service `cloudflared` dans `docker-compose.yml`
6. Public Hostname du tunnel :
   - Subdomain : `synthese` · Domain : `tondomaine.com`
   - Service : `http://dossier-synthesizer:8000`
7. `docker compose up -d`

→ Accessible sur `https://synthese.tondomaine.com`, avec invite
identifiant/mot de passe (auth HTTP Basic). HTTPS géré par Cloudflare.

## 7. Mettre à jour plus tard

```bash
cd dossier-synthesizer && git pull && docker compose up -d --build
```

---

## Notes

- **Whisper `small`** tient en RAM sur CX22. Si lenteur sur 3h de vidéo,
  passer à un CX32 ou garder `small` (suffisant en pratique).
- La « mémoire » des dossiers est dans le volume `./outputs` (persisté
  hors conteneur) : `git pull` / rebuild ne l'efface pas.
- Sauvegarde : `tar czf backup.tgz outputs/` périodiquement.
- Sécurité : l'auth Basic protège tout sauf `/healthz`. Le port n'est
  jamais exposé en clair (Cloudflare termine le TLS).
