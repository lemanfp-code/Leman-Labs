"""Registre des programmes de synthèse.

Un « programme » = tout ce qui distingue un dossier d'un autre :
le prompt système, le nom du webinaire, les intervenants attendus,
le préfixe de fichier et le thème visuel.

Ajouter un programme = ajouter une entrée dans PROGRAMS + déposer son
fichier prompt dans app/prompts/. Zéro autre changement de code.
"""

from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@dataclass(frozen=True)
class Program:
    id: str               # identifiant technique (slug), ex. "cpc"
    name: str             # nom complet, ex. "Club Privé Crypto"
    short: str             # préfixe fichier / badge, ex. "CPC"
    webinar_name: str     # phrase injectée dans le message utilisateur
    prompt_file: str      # nom du fichier dans app/prompts/
    tagline: str          # sous-titre du hero (texte simple)
    format_label: str     # description courte du format de sortie
    speakers: tuple       # intervenants attendus (fidélité des noms)
    theme: dict           # surcharges de variables CSS (vide = thème par défaut)
    docx_accent: str = "1F3A93"  # couleur d'accent du .docx (hex sans #)

    @property
    def prompt_path(self) -> Path:
        return PROMPTS_DIR / self.prompt_file

    def public_dict(self) -> dict:
        """Données exposées au front (jamais le prompt)."""
        return {
            "id": self.id,
            "name": self.name,
            "short": self.short,
            "tagline": self.tagline,
            "format_label": self.format_label,
            "speakers": list(self.speakers),
            "theme": self.theme,
        }


PROGRAMS: dict[str, Program] = {
    "cry": Program(
        id="cry",
        name="Cryptos Exponentielles",
        short="CRY",
        webinar_name="Cryptos Exponentielles",
        prompt_file="cry_prompt.txt",
        tagline=(
            "Transformez le replay de la conférence Cryptos Exponentielles en "
            "dossier : avis macro de Saturnin, analyse technique de Christophe, "
            "revue de portefeuille CORE & SATELLITE, ZAP/ZVP et Q&A des membres."
        ),
        format_label=(
            "6 blocs · couverture · conférence · macro Saturnin · "
            "technique Christophe · portefeuille CORE & SATELLITE · questions"
        ),
        speakers=("Saturnin Devins", "Christophe Schmitt", "Lucas"),
        theme={},  # thème par défaut (navy + cyan)
        docx_accent="0E7490",  # cyan profond (identité CRY, lisible sur blanc)
    ),
    "cpc": Program(
        id="cpc",
        name="Club Privé Crypto",
        short="CPC",
        webinar_name="Club Privé Crypto",
        prompt_file="cpc_prompt.txt",
        tagline=(
            "Transformez le replay du webinaire mensuel Club Privé Crypto en "
            "dossier complet : actualité du mois, recommandation, analyse du pro, "
            "suivi des recommandations passées et questions de la communauté."
        ),
        format_label=(
            "8 blocs · couverture · conférence · actualité · recommandation · "
            "analyse pro · suivi · questions · disclaimer"
        ),
        speakers=("Ahcène", "Louis-Alexandre Defroissard", "Saturnin"),
        theme={
            "--bg-0": "#0f0f1a",
            "--bg-1": "#16162a",
            "--bg-2": "#1a1a2e",
            "--panel": "#1a1a2e",
            "--panel-2": "#22223c",
            "--border": "#2c2c46",
            "--border-2": "#3c3c5a",
            "--accent": "#e8792b",
            "--accent-soft": "#f59e4f",
            "--accent-deep": "#d96a1f",
        },
        docx_accent="E8792B",  # orange CPC officiel
    ),
}

DEFAULT_PROGRAM = "cry"


def get_program(program_id: str | None) -> Program:
    """Retourne le programme demandé, ou le programme par défaut si invalide."""
    if program_id and program_id in PROGRAMS:
        return PROGRAMS[program_id]
    return PROGRAMS[DEFAULT_PROGRAM]


def list_programs() -> list[dict]:
    return [p.public_dict() for p in PROGRAMS.values()]
