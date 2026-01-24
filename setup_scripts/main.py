import argparse
import asyncio
import shutil
from pathlib import Path
from setup_scripts.utils import (
    download_files,
    unzip_data,
    create_user,
    load_release_from_csv,
    reset_alembic,
)
from discogs_rec_api.schemas import UserCreate


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimal", action="store_true")
    parser.add_argument("--ci", action="store_true")
    args = parser.parse_args()

    ml_path = Path(__file__).parents[1] / "ml"
    data_path = ml_path / "data"
    Path(data_path).mkdir(exist_ok=True, parents=True)

    download_files(path=data_path, minimal=args.minimal, ci=args.ci)
    if not args.minimal:
        unzip_data(path=ml_path, ci=args.ci)

    hf_cache_path = ml_path / "data" / ".cache"
    shutil.rmtree(hf_cache_path)

    if args.ci:
        return

    reset_alembic()

    csv_path = ml_path / "data" / "releases.csv"

    load_release_from_csv(csv_path=csv_path)

    csv_path.unlink()

    test_superuser = UserCreate(
        username="superuser",
        email="super@super.com",
        password="supaisdaman",
    )
    await create_user(user=test_superuser, is_superuser=True)


if __name__ == "__main__":
    asyncio.run(main())
