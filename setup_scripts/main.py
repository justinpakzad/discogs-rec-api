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

    # download and unzip data
    download_files(path=data_path, minimal=args.minimal, ci=args.ci)
    if not args.minimal:
        unzip_data(path=ml_path, ci=args.ci)

    # delete cache from hf
    hf_cache_path = ml_path / "data" / ".cache"
    shutil.rmtree(hf_cache_path)

    # for ci pipeline exit out
    if args.ci:
        return

    # reset alembic and grab latest updates
    reset_alembic()
    # load releases table
    csv_path = ml_path / "data" / "releases.csv"

    load_release_from_csv(csv_path=csv_path)

    # delete csv (not needed as its loaded to db)
    csv_path.unlink()

    # create a super user
    test_superuser = UserCreate(
        username="superuser",
        email="super@super.com",
        password="supaisdaman",
    )
    await create_user(user=test_superuser, is_superuser=True)


if __name__ == "__main__":
    asyncio.run(main())
