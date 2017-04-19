# -*- coding: utf-8 -*- 


"""Содержит функции для работы с объектом конфигурации myrm.

Объект конфигурации представляет собой 
словарь произвольной вложенности.

"""


import json

                
def get_default_config():
    """Возвращает программно заданный словарь конфигураций.
    """
    result = {}
    result["force"] = True
    result["dryrun"] = True
    result["verbose"] = True
    result["interactive"] = False
    
    result["trash"] = {}
    result["trash"]["dir"] = "./trash"
    result["trash"]["lockfile"] = "lock"
    result["trash"]["allowautoclean"] = True
    
    result["trash"]["max"] = {}
    result["trash"]["max"]["size"] = 1024
    result["trash"]["max"]["count"] = 5
    
    result["trash"]["autoclean"] = {}
    result["trash"]["autoclean"]["size"] = 300
    result["trash"]["autoclean"]["count"] = 10
    result["trash"]["autoclean"]["days"] = 1
    result["trash"]["autoclean"]["samename"] = 2
    
    return res


def save_to_JSON(cfg, filename):
    """Сохраняет объект конфигурации в JSON файл.
    
    Позицонные аргументы:
    cfg -- объект конфигурации
    filename -- имя выходного файла
    
    """
    with open(filename, mode="w") as f:
        json.dump(cfg, f, indent=2)  


def load_from_JSON(filename):
    """Загружает объект конфигурации из файла.
    
    Позицонные аргументы:
    filename -- имя входного файла
    
    """
    with open(filename, mode="r") as f:
        return json.load(f)  


def _recursive_save_to_CFG(output, dct, prefix=""):
    """Рекурсивно выводит словарь в поток.
    
    Позицонные аргументы:
    output -- выходной поток
    dct -- словарь для записи
    prefix -- префикс для всех ключей
    
    Значение преобразуется в строку через repr. Ключ через str.
    
    """
    for key in dct:
        if len(prefix)>0:
            node = prefix + "." + key
        else:
            node = key
        if isinstance(dct[key], dict):
            _recursiveSaveToCfg(output, dct[key], node)
        else:
            fmt = "\n{node!s} = {value!r}\n"
            line = fmt.format(node=node, value=dct[key])
            output.write(line)
        

def save_to_CFG(cfg, filename):
    """Сохраняет объект конфигурации в CFG подобный формат.
    
    В данном формате возможно хранить данные в следующем виде:
    Ключ[.субключ[.субключ]] = Значение
    При использовании субключей создается вложенный слорварь.
    Символ # обозначает коментарии.
    
    Позицонные аргументы:
    cfg -- объект конфигурации
    filename -- имя выходного файла
    
    """
    with open(filename, mode="w") as f:
        _recursiveSaveToCfg(f, cfg)  


def load_from_CFG(filename):
    """Загружает объект конфигурации в CFG подобный формат.
        
    В данном формате возможно хранить данные в следующем виде:
    Ключ[.субключ[.субключ]] = Значение
    При использовании субключей создается вложенный слорварь.
    Символ # обозначает коментарии.
    
    Позицонные аргументы:
    filename -- имя входного файла  
    
    """
    result = getDefaultConfig()
    with open(filename, mode="r") as f:
        for line in f.readlines():
            line = line.partition("#")[0]
            node_value = ln.split("=")
            if (len(node_value) == 2):
                node = node_value[0]
                value = node_value[1]
                node_path = node.split(".")
                value = eval(value)
                
                point = result
                for key in node_path[0:-1]:
                    key = key.strip()
                    if not (key in point):
                        point[key] = {}
                    point = point[key]
                    
                key = nodepath[-1].strip()
                point[key] = value
    return result

