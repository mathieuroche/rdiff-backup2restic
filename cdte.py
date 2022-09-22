import logging
import os

logging.basicConfig(format = '%(asctime)-15s %(levelname)s %(message)s', level = logging.INFO)

def change_arbo_encoding(directory, src_encoding = 'ISO-8859-1', dst_encoding = 'utf-8'):
    nb_renamed = 0
    logging.info('Change arborescence encoding of %s (%s=>%s)',directory, src_encoding, dst_encoding)
    for root, dirs, files in os.walk(directory):
        for filename in files:
            try:
                decoded = filename.decode(dst_encoding)
            except UnicodeDecodeError:
                decoded = filename.decode(src_encoding)
                src = os.path.join(root, filename)
                dst = os.path.join(root, decoded.encode(dst_encoding))
                logging.info("Rename %s => %s", src, dst)
                nb_renamed = nb_renamed + 1
                os.rename(src, dst)

        for dirname in dirs:
            try:
                decoded = dirname.decode(dst_encoding)
            except UnicodeDecodeError:
                decoded = dirname.decode(src_encoding)
                src = os.path.join(root, dirname)
                dst = os.path.join(root, decoded.encode(dst_encoding))
                logging.info("Rename %s => %s" , src, dst)
                nb_renamed = nb_renamed + 1
                os.rename(src, dst)
                dirs.append(decoded.encode(dst_encoding))

    return nb_renamed
