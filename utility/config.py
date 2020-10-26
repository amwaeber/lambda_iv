import datetime
import os
from configparser import ConfigParser

from utility.version import __version__

PROJECT_PATH = os.path.dirname(os.path.dirname(__file__))

global_confs = {'progname': 'Lambda IV',
                'progversion': __version__}

defaults = {'info': ['N/A', datetime.date.today(), 'unknown', 'unknown', 25.0, 'Vinery Way',
                     datetime.date(1970, 1, 1), -1, 8, 209, 38, 0.46, 0.1, 0.1, 25, -1, -1],
            'cell': [-0.01, 0.7, 0.005, 142, 0.5, 20, 5, 0.0, 5, 5.0, 1, 30.0, False, False],
            'arduino': [38400, 100, 2, 4, 0.25, 60.]}

paths = {'icons': os.path.join(PROJECT_PATH, 'icons'),
         'last_save': PROJECT_PATH}

ports = {'arduino': 'dummy',
         'keithley': 'dummy'}


def read_config():
    if not os.path.exists(os.path.join(PROJECT_PATH, 'config.ini')):
        write_config()
    config = ConfigParser()
    config.read(os.path.join(PROJECT_PATH, 'config.ini'))

    for key in config['defaults']:
        defaults[key] = eval(config['defaults'][key])

    for key in config['paths']:
        paths[key] = str(config['paths'][key])

    for key in config['ports']:
        ports[key] = str(config['ports'][key])


def write_config(**kwargs):
    config_path = os.path.join(PROJECT_PATH, 'config.ini')

    config = ConfigParser()

    config['globals'] = {'progname': global_confs['progname'],
                         'progversion': global_confs['progversion']
                         }

    config['defaults'] = {'info': defaults['info'],
                          'cell': defaults['cell'],
                          'arduino': defaults['arduino']}

    config['paths'] = {'icons': os.path.join(PROJECT_PATH, 'icons'),
                       'last_save': kwargs.get('save_path', paths['last_save'])
                       }

    config['ports'] = {'arduino': kwargs.get('arduino', ports['arduino']),
                       'keithley': kwargs.get('keithley', ports['keithley'])
                       }

    with open(config_path, 'w') as f:
        config.write(f)
