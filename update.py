from panoptes_client import Panoptes, Project, Subject
from panoptes_client.panoptes import PanoptesAPIException
from progress.bar import ChargingBar

import yaml

import os
import urllib


PROJECT_ID = 6767
PROCESSED_SUBJECTS_FILE = 'processed_subjects.txt'
PROCESSED_SETS_FILE = 'processed_sets.txt'


with open('config.yaml') as config_f:
    config = yaml.load(config_f, Loader=yaml.FullLoader)

if os.path.isfile(PROCESSED_SUBJECTS_FILE):
    with open(PROCESSED_SUBJECTS_FILE) as processed_f:
        processed_subjects = { s.strip() for s in processed_f.readlines() }
else:
    processed_subjects = set()

if os.path.isfile(PROCESSED_SETS_FILE):
    with open(PROCESSED_SETS_FILE) as processed_f:
        processed_sets = { s.strip() for s in processed_f.readlines() }
else:
    processed_sets = set()

Panoptes.connect(**config)
project = Project(PROJECT_ID)

with open(PROCESSED_SUBJECTS_FILE, 'a') as processed_subjects_f:
    with open(PROCESSED_SETS_FILE, 'a') as processed_sets_f:
        for subject_set in project.links.subject_sets:
            if subject_set.id in processed_sets:
                continue
            with ChargingBar(
                'Updating {}'.format(subject_set.display_name),
                max=subject_set.set_member_subjects_count,
                suffix='%(percent).1f%% %(eta_td)s'
            ) as bar:
                for subject in Subject.where(subject_set_id=subject_set.id, page_size=100):
                    bar.next()
                    if subject.id in processed_subjects:
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

                    for retry in (True, False):
                        try:
                            subject.metadata['!CERiT'] = cerit_url
                            subject.metadata['!Simbad'] = simbad_url
                            subject.metadata['!ASAS-SN Photometry'] = asassn_url

                            subject.save()
                        except PanoptesAPIException:
                            if retry:
                                # Reload the subject to refresh the etag
                                # This works around what seems to be a bug in the Panoptes client
                                # https://github.com/zooniverse/panoptes-python-client/issues/220
                                subject.reload()
                            else:
                                raise

                    processed_subjects.add(subject.id)
                    processed_subjects_f.write('{}\n'.format(subject.id))
                bar.finish()
            processed_sets.add(subject_set.id)
            processed_sets_f.write('{}\n'.format(subject_set.id))