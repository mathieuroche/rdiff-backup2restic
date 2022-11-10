import logging
import os
import stat

logging.basicConfig(
    format="%(asctime)-15s %(levelname)s %(message)s", level=logging.INFO
)


def make_writeable(directory, dry_run=False):
    if not os.access(directory, os.W_OK):
        logging.info("No write access in '%s'", directory)
        logging.info("chmod u+w '%s'", directory)
        if not dry_run:
            stat_result = os.stat(directory)
            os.chmod(directory, stat_result.st_mode | stat.S_IWUSR)


def change_arbo_encoding(
    directory, src_encoding="ISO-8859-1", dst_encoding="utf-8", dry_run=False
):
    logging.info(
        "Change arborescence encoding of %s (%s=>%s)",
        directory,
        src_encoding,
        dst_encoding,
    )
    number_of_changes = 0
    for root, dirs, files in os.walk(directory.encode("utf-8")):
        for filename in files:
            try:
                decoded = filename.decode(dst_encoding)
            except UnicodeDecodeError:
                decoded = filename.decode(src_encoding)
                src = os.path.join(root, filename)
                dst = os.path.join(root, decoded.encode(dst_encoding))
                logging.info("Rename %s => %s", src, dst)
                number_of_changes = number_of_changes + 1
                make_writeable(root, dry_run)
                if not dry_run:
                    os.rename(src, dst)

        for dirname in dirs:
            try:
                decoded = dirname.decode(dst_encoding)
            except UnicodeDecodeError:
                decoded = dirname.decode(src_encoding)
                src = os.path.join(root, dirname)
                dst = os.path.join(root, decoded.encode(dst_encoding))
                logging.info("Rename %s => %s", src, dst)
                number_of_changes = number_of_changes + 1
                make_writeable(root, dry_run)
                if not dry_run:
                    os.rename(src, dst)
                dirs.append(decoded.encode(dst_encoding))

    return number_of_changes
