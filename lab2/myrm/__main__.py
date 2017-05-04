# -*- coding: utf-8 -*-


def get_argument_parcer(remove_only=False):
    parser = argparse.ArgumentParser(prog="myrm")

    if not rm_only:
        parser.add_argument("command",
                            choices=["rm", "rs", "ls", "clear", "autoclear"])
    parser.add_argument("filemasks", nargs='+')
    parser.add_argument("-r", "-R", "--recursive",
                        dest="recursive", action="store_true")
    
    parser.add_argument("-o", "--old", dest="old", default=0, 
                        help="Choose version of file.")
    parser.add_argument("-a", "--all", dest="versions",
                        action="store_const", const=True, 
                        help="display all versions of files.")
    
    parser.add_argument("--config", default=None)
    parser.add_argument("--jsonconfig", default=None)

    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="store_const", const=True, 
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


def main(remove_only=False):
    """Главная точка входа.

    Операциии и аргументы беруться из командной строки.
    """
    parser = get_argument_parcer(remove_only=remove_only)
    args = parser.parse_args()
    cfg = config.get_default_config()

    if args.config is not None:
        cfg = config.load_from_cfg(args.config)

    if args.jsonconfig is not None:
        cfg = config.load_from_json(args.config)

    if args.force is not None:
        cfg["force"] = args.force
    if args.dryrun is not None:
        cfg["dryrun"] = args.dryrun
    if args.verbose is not None:
        cfg["verbose"] = args.verbose
    if args.interactive is not None:
        cfg["interactive"] = args.interactive

    if cfg["verbose"]:
        logging.basicConfig(format="%(message)s", level=logging.INFO)

    mrm = MyRm(cfg)
    
    count = 0
    size = 0
    for fime_mask in args.filemasks:
        if rm_only:
            dcount, dsize = mrm.remove(fime_mask, recursive=args.recursive)
            count += dcount
            size += dsize
        else:
            cmd = args.command
            if cmd == "rm":
                dcount, dsize = mrm.remove(fime_mask , 
                                        recursive=args.recursive)
                count += dcount
                size += dsize
                
            elif cmd == "rs":
                dcount, dsize = mrm.restore(fime_mask, recursive=args.recursive, 
                                          how_old=args.old)
                count += dcount
                size += dsize       
                
            elif cmd == "ls":
                files = mrm.lst(fime_mask, recursive=args.recursive,
                                versions=args.versions)
                for path, version in files:
                    if version == None or not args.versions:
                        log_msg = path
                    else:
                        version_str = version.strftime("%d.%m.%Y %I:%M")
                        log_msg = "{} (removed {})".format(path, version_str)
                    logging.info(log_msg)                    
                    
            elif cmd == "clear":
                dcount, dsize = mrm.clean(fime_mask, recursive=args.recursive, 
                                        how_old=args.old)
                count += dcount
                size += dsize

            elif cmd == "autoclear":
                dcount, dsize = mrm.autoclean()
                count += dcount
                size += dsize

    if rm_only:
        log_fmt = "{count} files ({size} bytes) was removed."
        log_msg = log_fmt.format(count=count, size=size) 
        logging.info(log_msg)
    else:
        cmd = args.command
        if cmd == "rm":
            log_fmt = "{count} files ({size} bytes) was removed."
            log_msg = log_fmt.format(count=count, size=size) 
            logging.info(log_msg)
            
        elif cmd == "rs":
            log_fmt = "{count} files ({size} bytes) was restored."
            log_msg = log_fmt.format(count=count, size=size) 
            logging.info(log_msg)         
                
        elif cmd == "clear":
            log_fmt = "{count} files ({size} bytes) was cleaned."
            log_msg = log_fmt.format(count=count, size=size) 
            logging.info(log_msg)

        elif cmd == "autoclear":
            log_fmt = "{count} files ({size} bytes) was cleaned."
            log_msg = log_fmt.format(count=count, size=size) 
            logging.info(log_msg)


def shor_rm():
    """Краткая точка входа. Выполняет удаление в корзину.
    """
    main(rm_only=True)


if __name__ == "__main__":
    main() 
