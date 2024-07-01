import argparse
import pathlib
import typing
import logging
import os
from ndn import appv2
from ndn import encoding as enc

import validator
from Algo_ECHT import ECHTBE
from OurModel import AddMessage, PnpDMessage, PnpIMessage
import configparser
from datasets.DSManager import DSM
from utils import convert_names_to_strings

# region logging
logging.basicConfig(format='{asctime} {levelname} [{filename}:{lineno}] {message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG,
                    style='{')

logging.getLogger('asyncio').setLevel(logging.WARNING)
# endregion logging

# region Globals
app = appv2.NDNApp()
keychain = app.default_keychain()
keychain.get_signer({})
pid = os.getpid()
# endregion Globals


def construct_proper_reply(received_app_params, dbm):
    msg = PnpIMessage.parse(received_app_params)
    logging.debug('Received the following PNP_Interest message:{}'.format(msg))
    reply = []
    if msg.add_message is not None:
        logging.debug('Add message:\n{}'.format(msg.add_message))
        entry_key = [i.tobytes() for i in msg.add_message.publisher_name]
        entry_values = [[location.tobytes() for location in locations] for locations in msg.add_message.hosting_as_list]
        logging.debug('Received a pnps-add request to advertise {} in {}'.format(entry_key, entry_values))
        dbm.add(entry_key, entry_values)
        reply = dbm.get(entry_key)
        logging.debug('Replying to pnps-add({}) with: {}'.format(entry_key, reply))
        reply = (entry_key, reply)
    elif msg.remove_message is not None:
        logging.debug('Received a pnps-remove request for: %s', enc.Name.to_str(msg.remove_message.publisher_name))
        entry_key = enc.Name.to_str(msg.remove_message.publisher_name)
        entry_values = convert_names_to_strings(msg.remove_message.hosting_as_list)
        if entry_values is None:
            reply = dbm.remove(entry_key)
        else:
            reply = dbm.remove(entry_key, entry_values)
        reply = (entry_key, reply)
    elif msg.set_message is not None:
        logging.debug('Received a pnps-set request for: %s', enc.Name.to_str(msg.set_message.publisher_name))
        entry_key = [i.tobytes() for i in msg.set_message.publisher_name]
        entry_values = [[location.tobytes() for location in locations] for locations in msg.set_message.hosting_as_list]
        dbm.set(entry_key, entry_values)
        reply = dbm.get(entry_key)
        logging.debug('Replying to pnps-set({}) with: {}'.format(entry_key, reply))
        reply = (entry_key, reply)
    elif msg.get_message is not None:
        entry_key = [i.tobytes() for i in msg.get_message.publisher_name]
        logging.debug('Received a pnps-get request for: {}'.format(entry_key))
        reply = dbm.get(entry_key)
        logging.debug('Replying to pnps-get({}) with: {}'.format(entry_key, reply))
        reply = (entry_key, reply)
    elif msg.getlpm_message is not None:
        entry_key = [i.tobytes() for i in msg.getlpm_message.publisher_name]
        logging.debug('Received a pnps-getlpm request for: {}'.format(entry_key))
        reply = dbm.lpm(entry_key)
        logging.debug('Replying to pnps-getlpm({}) with: {}'.format(entry_key, reply))
    logging.debug("Returning the following reply to express_interest: {}".format(reply))
    return reply


async def main(database_manager):
    logging.info('The ndn app server on {} is ready ...'.format(app_route))

    @app.route(app_route, validator=appv2.pass_all)
    def on_interest(name: enc.FormalName, _app_param: typing.Optional[enc.BinaryStr],
                    reply: appv2.ReplyFunc, context: appv2.PktContext):
        publisher_lpm, data_packet_content = construct_proper_reply(_app_param, database_manager)
        data_packet = PnpDMessage()
        data_packet.publisher_name = publisher_lpm
        data_packet.hosting_as_list = data_packet_content
        logging.debug('>> I: {}, {}'.format(enc.Name.to_str(name), context["int_param"]))
        content = data_packet.encode()
        reply(app.make_data(name, content=content, signer=keychain.get_signer({}), freshness_period=10000))
        logging.debug('<< D: {}'.format(enc.Name.to_str(name)))
        logging.debug(enc.MetaInfo(freshness_period=10000))
        logging.debug('Content: (size: {})'.format(len(content)))


if __name__ == "__main__":
    # region Arguments Parser
    algorithms = {'echt': ECHTBE}
    parser = argparse.ArgumentParser('pnps.py')
    parser.add_argument('--algo', nargs=1, metavar='Algorithm', default='echt',
                        help='Backend algorithm (Options: echt. Default: echt)')
    parser.add_argument('--route', nargs=1, metavar='Route', default='/AS1/PNPS',
                        help='Server mounting point (Default: /AS1/PNPS)')
    parser.add_argument('--noload', action='store_true',
                        help='Do not preload the default dataset (Default: load)')
    parser.add_argument('--config', nargs=1, metavar='ConfigFile', default='/etc/ndn/pnp/app.ini',
                        help='Configuration File. (Created by running: sudo ./runme.sh)')
    args = parser.parse_args()
    print(args)
    # endregion Arguments Parser

    # region Configuration
    path = pathlib.Path(args.config)
    if not path.exists():
        exit('Can not find the configuration file in: {}'.format(args.config))
    application_config = configparser.ConfigParser()
    application_config.read(args.config)
    app_route = application_config.get('PNPS', 'app_route')
    # endregion Configuration

    # region Backend Algorithm - instantiation
    if args.algo in algorithms:
        dbm = algorithms[args.algo]()
    else:
        exit('{} is not an implemented algorithm'.format(args.algo))

    logging.info('Staring the server on {}'.format(app_route))
    # endregion Backend Algorithm - instantiation

    # region Dataset Manager -if configured-
    if not args.noload:
        default_ds = application_config.get('DatasetManager', 'default_ds')
        loading_batch_size = int(application_config.get('AlgorithmsConfiguration',
                                                        'batch_size_for_batch_loading'))
        dsm = DSM()
        dsm.active_dataset = default_ds + '_' + dbm.default_dataset_format
        dataset = dsm.get_current()
        dbm.batch_load(dataset, loading_batch_size)
    # endregion Dataset Manager -if configured-

    # region main
    try:
        # Start the ndn listening server
        app.run_forever(after_start=main(dbm))
    except ConnectionRefusedError:
        logging.warning("NFD is not running ... exiting.")
        exit('NFD is not running .. exiting.')
    # endregion main

    logging.info('Shutting down the server on ' + app_route)
