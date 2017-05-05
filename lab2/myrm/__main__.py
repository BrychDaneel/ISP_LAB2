# -*- coding: utf-8 -*-
import argparse
import logging

import myrm.config as config 

from myrm.remover import Remover

def get_argument_parcer(remove_only=False):
    """
    """
    parser = argparse.ArgumentParser(prog="myrm")

    if not remove_only:
        parser.add_argument("command",
                            choices=["rm", "rs", "ls", "clear", "autoclear"])

    parser.add_argument("filemasks", nargs='+')

    parser.add_argument("-r", "-R", "--recursive",
                        dest="recursive", action="store_true")

    parser.add_argument("-o", "--old", dest="old", default=0,
                        help="Choose version of file.")

    parser.add_argument("-a", "--all", dest="versions",
                        action="store_true",
                        help="display all versions of files.")

    parser.add_argument("--config", default=None)

    parser.add_argument("--jsonconfig", default=None)

    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="store_false",
                        help="show list of operate files.")

    parser.add_argument("-d", "--dryrun", dest="dryrun",
                        action="store_const", const=True,
                        help="just emulate work.")

    parser.add_argument("-f", "--force", dest="force",
                        action="store_const", const=True,
                        help="igrnore errors.")

    parser.add_argument("-i", "--interactive", dest="interactive",
                        action="store_const", const=True,
                        help="ask you before operation.")
    return parser


def perfome(remover, operation, file_mask, how_old=0,
            recursive=False, versions=False):
    """
    """
    if operation == "rm":
        dcount, dsize = remover.remove(file_mask, ecursive=recursive)

    elif operation == "rs":
        dcount, dsize = remover.restore(file_mask, recursive=recursive,
                                        how_old=how_old)

    elif operation == "ls":
        files = remover.lst(file_mask, recursive=recursive, versions=versions)
        for path, version in files:
            if not versions:
                log_msg = path
            else:
                version_str = version.strftime("%d.%m.%Y %I:%M")
                log_msg = "{} (removed {})".format(path, version_str)
            logging.info(log_msg)

    elif operation == "clear":
        dcount, dsize = remover.clean(file_mask, recursive=recursive,
                                      how_old=how_old)

    elif operation == "autoclear":
        dcount, dsize = remover.autoclean()

    else:
        raise ValueError("Unsoported operation {}".format(operation))

    return dcount, dsize


def log_summ(operation, count, size):
    """
    """
    if operation == "rm":
        log_fmt = "{count} files ({size} bytes) was removed."
        log_msg = log_fmt.format(count=count, size=size)
        logging.info(log_msg)

    elif operation == "rs":
        log_fmt = "{count} files ({size} bytes) was restored."
        log_msg = log_fmt.format(count=count, size=size)
        logging.info(log_msg)

    elif operation == "clear":
        log_fmt = "{count} files ({size} bytes) was cleaned."
        log_msg = log_fmt.format(count=count, size=size)
        logging.info(log_msg)

    elif operation == "autoclear":
        log_fmt = "{count} files ({size} bytes) was cleaned."
        log_msg = log_fmt.format(count=count, size=size)
        logging.info(log_msg)

    else:
        raise ValueError("Unsoported operation {}".format(operation))


def main(remove_only=False):
    """Главная точка входа.

    Операциии и аргументы беруться из командной строки.
    """
    parser = get_argument_parcer(remove_only=remove_only)
    args = parser.parse_args()

    remover_parametrs = {}

    if args.config is not None:
        cfg = config.load_from_cfg(args.config)
        remover_parametrs.update(cfg)

    if args.jsonconfig is not None:
        cfg = config.load_from_json(args.config)
        remover_parametrs.update(cfg)

    if args.force is not None:
        remover_parametrs["force"] = args.force
    if args.dryrun is not None:
        remover_parametrs["dryrun"] = args.dryrun
    if args.interactive is not None:
        remover_parametrs["interactive"] = args.interactive


    if args.verbose:
        logging.basicConfig(format="%(message)s", level=logging.INFO)

    mrm = Remover(**remover_parametrs)

    if remove_only:
        operation = "rm"
    else:
        operation = args.command

    count = 0
    size = 0
    for file_mask in args.filemasks:
        dsize, dcount = perfome(mrm, operation, file_mask,
                                how_old=args.how_old,
                                recursive=args.recursive,
                                versions=args.versions)
        count += dcount
        size += dsize

    log_summ(operation, count, size)


def remove():
    """Краткая точка входа. Выполняет удаление в корзину.
    """
    main(remove_only=True)


if __name__ == "__main__":
    main()
