"""Assemble le site statique (GitHub Pages) et la version artefact du tableau de bord.

- site/index.html    : page complète, lit data/today.json (publié à côté) — GitHub Pages
- site/artifact.html : corps de page + instantané JSON intégré — pour un artefact claude.ai
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

HEAD = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>[hidden]{display:none!important}body{margin:0}img{max-width:100%}</style></head><body>')


def main():
    body = (SITE / "dashboard.body.html").read_text(encoding="utf-8")
    (SITE / "index.html").write_text(HEAD + body + "</body></html>", encoding="utf-8")
    snap = SITE / "data" / "today.json"
    if snap.exists():
        data = snap.read_text(encoding="utf-8").replace("</", "<\\/")
        tag = f'<script type="application/json" id="snapshot">{data}</script>'
        (SITE / "artifact.html").write_text(body.replace("<!--SNAPSHOT-->", tag), encoding="utf-8")
    print("site/index.html et site/artifact.html écrits")


if __name__ == "__main__":
    main()
