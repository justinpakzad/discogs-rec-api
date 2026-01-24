import subprocess
import psycopg2
import csv
from zipfile import ZipFile
from pathlib import Path
from discogs_rec_api.schemas import UserCreate
from discogs_rec_api.database import async_session
from discogs_rec_api.security import get_password_hash
from discogs_rec_api.models import Users
from discogs_rec_api.config import Config
from huggingface_hub import hf_hub_download

settings = Config()


def download_files(path: Path | str, minimal: bool = False, ci: bool = False) -> None:
    """
    Download the ann files and mappings from Hugging Face Hub to the local data directory.

    Args:
        path: Local directory path where the data.zip file will be downloaded
        minimal: Just downloads release metadata
        ci: Downloads a lite version of the model for ci
    """
    if ci:
        hf_hub_download(
            repo_id="justinp303/discogs-recommender-model",
            repo_type="dataset",
            filename="data-lite.zip",
            local_dir=str(path),
        )
    elif minimal:
        hf_hub_download(
            repo_id="justinp303/discogs-recommender-model",
            repo_type="dataset",
            filename="releases.csv",
            local_dir=str(path),
        )
    else:
        hf_hub_download(
            repo_id="justinp303/discogs-recommender-model",
            repo_type="dataset",
            filename="data.zip",
            local_dir=str(path),
        )


def unzip_data(path: Path, ci: bool = False) -> None:
    """
    Extract files from the downloaded data.zip archive.

    Args:
        path: Base directory path containing the data subdirectory with data.zip
        ci: Unzip lite verison of model for ci pipeline
    """
    file_type = "data" if not ci else "data-lite"
    files_to_extract = [
        "data/discogs_rec.ann",
        "data/release_id_to_idx.pkl",
        "data/idx_to_release_info.pkl",
        "data/n_components.txt",
        "data/releases.csv",
    ]
    zip_path = path / "data" / f"{file_type}.zip"
    with ZipFile(zip_path, "r") as zip_object:
        for item in zip_object.namelist():
            if item in files_to_extract:
                zip_object.extract(item, path)

    # remove zip file
    zip_path.unlink()


async def create_user(user: UserCreate, is_superuser: bool = False) -> None:
    """
    Create a new user in the database.

    Args:
        user: User creation schema containing username, email, and password
        is_superuser: Whether to grant superuser privileges to the new user
    """
    async with async_session() as db:
        hashed_password = get_password_hash(user.password)
        db_user = Users(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        if is_superuser:
            db_user.is_superuser = True
            await db.commit()


def load_release_from_csv(csv_path: Path | str) -> None:
    """
    Load release data from CSV file into Postgres.

    Args:
        csv_path: Path to the CSV file containing release data

    """
    conn = psycopg2.connect(settings.sync_database_url)
    curr = conn.cursor()

    with open(csv_path, "r") as f:
        csv_reader = csv.DictReader(f)
        cols = csv_reader.fieldnames
        columns = ", ".join(cols)

        f.seek(0)

        sql = f"""
            COPY releases ({columns})
            FROM STDIN
            WITH (FORMAT CSV, HEADER TRUE, QUOTE '"')
        """
        curr.copy_expert(sql, f)

    curr.close()
    conn.commit()
    conn.close()


def reset_alembic() -> None:
    """
    Reset Alembic migrations by downgrading to base and upgrading to head.
    """
    subprocess.run(["python", "-m", "alembic", "downgrade", "base"])
    subprocess.run(["python", "-m", "alembic", "upgrade", "head"])
