import logging

class AcsessManager:
    
    def __init__(self, cfg):
        self.cfg = cfg
    
    def ask(self, operation, filename):
        u_ans = raw_input("Do you want to {} '{}'? [Y/n]".format(operation,filename))
        u_ans = u_ans.lower()
        return  not u_ans or u_ans == 'y'
    
    def removeAcsess(self, path):
        if self.cfg.interactive and not ask('remove file ', path):
            return False
        logging.info('Remove {}'.format(path))
        if self.cfg.dryrun:
            return False
        return True
    
    def restoreAcsess(self, path):
        if self.cfg.interactive and not ask('restore file ', path):
            return False
        logging.info('Restore {}'.format(path))
        if self.cfg.dryrun:
            return False
        return True
    
    def cleanAcsess(self, path):
        if self.cfg.interactive and not ask('clean file(forever)', path):
            return False
        logging.info("Clean '{}'".format(path))
        if self.cfg.dryrun:
            return False
        return True

    def autocleanAcsess(self):
        if self.cfg.interactive and not ask('autoclean file(forever) in', self.cfg.trash_dir):
            return False
        logging.info("Autoclean '{}'".format(self.cfg.trash_dir))
        if self.cfg.dryrun:
            return False
        return True

