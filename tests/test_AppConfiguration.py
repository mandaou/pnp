from unittest import TestCase
import configparser
import pathlib


class TestAppConfiguration(TestCase):

    def setUp(self) -> None:
        self.ini_file = "/etc/ndn/pnp/app.ini"
        self.application_config = configparser.ConfigParser()
        self.application_config.read(self.ini_file )
        x = 1

    def test_file_exists(self):
        path = pathlib.Path(self.ini_file)
        self.assertTrue(path.is_file())

    def test_app_home_directory(self):
        app_home = self.application_config.get('Paths', 'home_dir')
        path = pathlib.Path(app_home)
        self.assertTrue(path.is_dir())

    def test_ds_home_directory(self):
        ds_home = self.application_config.get('Paths', 'ds_home')
        path = pathlib.Path(ds_home)
        self.assertTrue(path.is_dir())

    def test_default_ds_is_set(self):
        default_ds = self.application_config.get('DatasetManager', 'default_ds')
        self.assertIsNotNone(default_ds)
