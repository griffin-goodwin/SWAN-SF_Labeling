import configparser

def read_config_map(path='config.ini'):
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

