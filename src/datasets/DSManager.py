import glob
import logging
import pickle
import time
import configparser
from pathlib import Path
from datasets.Dataset import Dataset

# region logging
logging.basicConfig(format='{asctime} {levelname} [{filename}:{lineno}] {message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    style='{')

logging.getLogger('asyncio').setLevel(logging.WARNING)
# endregion logging


# region Globals
application_config = configparser.ConfigParser()
application_config.read("/etc/ndn/pnp/app.ini")
try:
    ds_home = application_config.get('Paths', 'ds_home')
except configparser.NoSectionError:
    print('ERROR - config.ini not found, please copy conf/pnp_app.ini to /etc/ndn/pnp/app.ini')
    exit(1)

def get_available_datasets():
    datasets = glob.glob(ds_home + "/publisher*")
    results = {}
    for i in datasets:
        stripped_ds = i.strip(ds_home + '/')
        ds = stripped_ds.split(".")[0].split("_")[1]
        results[i] = ds
    return results


datasets = get_available_datasets()
# endregion Globals


class DSM:
    def __init__(self):
        self.cache = dict()
        self.populate_time = 0
        self._active_dataset = None
        self.populate_cache()

    def __len__(self):
        return len(self.cache)

    @property
    def active_dataset(self):
        return self._active_dataset

    @active_dataset.setter
    def active_dataset(self, dataset_name):
        logging.debug('Setting active dataset to: {}'.format(dataset_name))
        self._active_dataset = dataset_name

    def populate_cache(self):
        start_time = time.time()
        cache_file = Path('/tmp/dsm_cache.pkl')
        if cache_file.is_file():
            logging.info('Dataset Cache exists, reading from the cache')
            with (open(cache_file, 'rb')) as fh:
                self.cache = pickle.load(fh)
        else:
            for ds_file, ds_name in datasets.items():
                self.cache[ds_name + '_utf'] = Dataset(name=ds_name, ndn_encoded=False, dataset_path_on_disk=ds_file)
                self.cache[ds_name + '_named'] = Dataset(name=ds_name, ndn_encoded=True, dataset_path_on_disk=ds_file)
            with (open(cache_file, 'wb')) as fh:
                pickle.dump(self.cache, fh, protocol=pickle.HIGHEST_PROTOCOL)
        self.populate_time = time.time() - start_time
        logging.info('Dataset Manager Cache population in {} seconds'.format(self.populate_time))

    def get_current(self) -> Dataset:
        return self.cache[self.active_dataset]

    def get_cache(self, name) -> Dataset:
        return self.cache[name]

    # def get(self, name: str, database_manager: BEABC) -> Dataset:
    #     """Returns a pickled dataset"""
    #     ds_full_name = name + database_manager.default_dataset_format
    #     return self.cache[ds_full_name]