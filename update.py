from panoptes_client import Panoptes, Project

import yaml


with open('config.yaml') as config_f:
    config = yaml.load(config_f, Loader=yaml.FullLoader)

Panoptes.connect(**config)

print(Project(7).display_name)