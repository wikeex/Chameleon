from configparser import ConfigParser
import os
base_dir = os.path.dirname(__file__)

config = ConfigParser()
config.read(os.path.join(base_dir, 'config.ini'))
