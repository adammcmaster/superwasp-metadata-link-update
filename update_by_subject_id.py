from panoptes_client import Panoptes, Project, Subject
from panoptes_client.panoptes import PanoptesAPIException
from progress.bar import ChargingBar

import yaml

import os
import urllib


SUBJECT_ID_FILE = 'subjects.txt'


with open('config.yaml') as config_f:
    config = yaml.load(config_f, Loader=yaml.FullLoader)

with open(SUBJECT_ID_FILE) as subject_id_f:
    subject_ids = [ s.strip() for s in subject_id_f.readlines() ]

Panoptes.connect(**config)

with ChargingBar(
    'Updating',
    max=len(subject_ids),
    suffix='%(percent).1f%% %(eta_td)s'
) as bar:
    with Subject.async_saves():
        for subject_id in subject_ids:
            bar.next()

            subject = Subject.find(subject_id)

            if '!CERiT' in subject.metadata:
                continue

            superwasp_id = subject.metadata.get('Filename', subject.metadata.get('filename')).split('_')[0]
            coords = superwasp_id.replace('1SWASP', '')
            coords_quoted = urllib.parse.quote(coords)
            ra = urllib.parse.quote('{}:{}:{}'.format(
                coords[1:3],
                coords[3:5],
                coords[5:10]
            ))
            dec = urllib.parse.quote('{}:{}:{}'.format(
                coords[10:13],
                coords[13:15],
                coords[15:]
            ))

            cerit_url = 'https://wasp.cerit-sc.cz/search?objid={}&radius=1&radiusUnit=deg&limit=10'.format(coords_quoted)
            simbad_url = 'http://simbad.u-strasbg.fr/simbad/sim-coo?Coord={}+{}&Radius=2&Radius.unit=arcmin&submit=submit+query'.format(ra, dec)
            asassn_url = 'https://asas-sn.osu.edu/photometry?ra={}&dec={}&radius=2'.format(ra, dec)

            subject.metadata['!CERiT'] = cerit_url
            subject.metadata['!Simbad'] = simbad_url
            subject.metadata['!ASAS-SN Photometry'] = asassn_url

            subject.save()

        bar.finish()