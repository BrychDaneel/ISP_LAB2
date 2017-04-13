# -*- coding: utf-8 -*- 

import json
                
def getDefaultConfig():
    res = {}
    res['force'] = True
    res['dryrun'] = True
    res['verbose'] = True
    res['interactive'] = False
    
    res['trash'] = {}
    res['trash']['dir'] = "./trash"
    res['trash']['lockfile'] = "lock"
    res['trash']['allowautoclean'] = True
    
    res['trash']['maximum'] = {}
    res['trash']['maximum']['size'] = 1024
    res['trash']['maximum']['count'] = 5
    
    res['trash']['autoclean'] = {}
    res['trash']['autoclean']['size'] = 300
    res['trash']['autoclean']['count'] = 10
    res['trash']['autoclean']['days'] = 1
    res['trash']['autoclean']['samename'] = 2
    
    return res


def saveToJSON(cfg, filename):
    with open(filename, mode='w') as f:
        json.dump(cfg, f, indent=2)  


def loadFromJSON(filename):
    with open(filename, mode='r') as f:
        return json.load(f)  


def _recursiveSaveToCfg(fp, dct, prefix=""):
    for key in dct:
        
        if len(prefix)>0:
            node = prefix + '.' + key
        else:
            node = key
         
        if isinstance(dct[key], dict):
            _recursiveSaveToCfg(fp, dct[key], node)
        else:
            fp.write("\n{node!s} = {value!r}\n".format(node=node, value=dct[key]))
        

def saveToCFG(cfg, filename):
    with open(filename, mode='w') as f:
        _recursiveSaveToCfg(f, cfg)  


def loadFromCFG(filename):
    res = {}
    
    with open(filename, mode='r') as f:
        for line in f.readlines():
            ln = line.partition('#')[0]
            ln = ln.split('=')
            if (len(ln) == 2):
                node = ln[0]
                value = ln[1]
                nodepath = node.split('.')
                value  = eval(value)
                
                point = res
                for key in nodepath[0:-1]:
                    key = key.strip()
                    if not (key in point):
                        point[key] = {}
                    point = point[key]
                    
                key = nodepath[-1].strip()
                point[key] = value
    return res
