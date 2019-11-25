import os
import shutil
import gcsfs

GOOGLE_PROJECT = 'VCM-ML'

def _copy_directory(local_source_dir, dest_dir, fs=None):
    """Copy the contents of a local directory to a local or remote directory.
    """
    if fs is None:
        fs = gcsfs.GCSFileSystem(project=GOOGLE_PROJECT)
    for token in os.listdir(local_source_dir):
        source = os.path.join(os.path.abspath(local_source_dir), token)
        dest = os.path.join(os.path.abspath(dest_dir), token)
        if os.path.isdir(source):
            if not _is_gcloud_path(dest) and not os.path.isdir(dest):
                os.mkdir(dest)
            _copy_directory(source, dest, fs)
        else:
            _copy_file(source, dest, fs)


def _copy_file(source_filename, dest_filename, fs=None):
    """Copy a local or remote file to a local or remote target location."""
    if fs is None and (_is_gcloud_path(source_filename) or _is_gcloud_path(dest_filename)):
        fs = gcsfs.GCSFileSystem(project=GOOGLE_PROJECT)
    if not _is_gcloud_path(source_filename):
        if not _is_gcloud_path(dest_filename):
            shutil.copy2(source_filename, dest_filename, follow_symlinks=True)
        else:
            fs.put(source_filename, dest_filename)
    else:  # source is remote
        if not _is_gcloud_path(dest_filename):
            fs.get(source_filename, dest_filename)
        else:
            raise NotImplementedError('Cannot copy from Google cloud to Google cloud')


def _is_gcloud_path(path):
    return path[:5] == 'gs://'
