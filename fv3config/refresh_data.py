from ._datastore import refresh_downloaded_data
from fv3config import get_cache_dir

if __name__ == "__main__":
    print(
        f"You are about to delete all files in {get_cache_dir()} and re-download the cache."
    )
    user_input = input("Hit return/enter to proceed, or enter any value to cancel: ")
    if len(user_input) == 0:
        print("proceeding...")
        refresh_downloaded_data()
        print("done.")
    else:
        print("cancelled.")
