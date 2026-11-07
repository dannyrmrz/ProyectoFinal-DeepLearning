import argparse
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVOS = ["Dockerfile", ".dockerignore", "requirements.txt", "config.json", "servicio", "modelo"]

p = argparse.ArgumentParser()
p.add_argument("space", help="usuario/nombre del Space")
p.add_argument("--mensaje", default="Despliegue desde GitHub")
args = p.parse_args()

operaciones = [CommitOperationAdd("README.md", str(RAIZ / "despliegue" / "README_space.md"))]
for nombre in ARCHIVOS:
    ruta = RAIZ / nombre
    for f in ([ruta] if ruta.is_file() else sorted(ruta.rglob("*"))):
        if f.is_file() and "__pycache__" not in f.parts:
            operaciones.append(CommitOperationAdd(f.relative_to(RAIZ).as_posix(), str(f)))

api = HfApi()
api.create_repo(args.space, repo_type="space", space_sdk="docker", exist_ok=True)
info = api.create_commit(args.space, operaciones, commit_message=args.mensaje, repo_type="space")
print(f"{len(operaciones)} archivos -> {info.commit_url}\nhttps://huggingface.co/spaces/{args.space}")
