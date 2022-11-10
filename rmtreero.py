import shutil
import stat
import os


def rmtree(directory):
    """rmtree but also works on readonly directory."""
    for (root, _, _) in os.walk(directory, topdown=True):
        stat_result = os.stat(root)
        os.chmod(root, stat_result.st_mode | stat.S_IRUSR | stat.S_IWUSR)
    shutil.rmtree(directory)
