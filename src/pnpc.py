import configparser
import logging
import pathlib

from ndn import appv2, types
from ndn import encoding as enc

import validator
from pnpc_arg_parser import get_args, get_examples
from OurModel import AddMessage, GetMessage, GetLpmMessage, PnpDMessage, PnpIMessage, RemoveMessage, SetMessage
from utils import convert_names_to_strings, convert_strings_to_names

# region Logging
try:
    logging.basicConfig(
        level=logging.ERROR,
        handlers=[logging.FileHandler("/var/log/ndn/pnpc.log"),
                  logging.StreamHandler()],
        format='{asctime} {levelname} [{filename}:{lineno}] {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{')
except PermissionError:
    logging.basicConfig(
        level=logging.ERROR,
        handlers=[logging.StreamHandler()],
        format='{asctime} {levelname} [{filename}:{lineno}] {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{')
# endregion


# region Globals
app = appv2.NDNApp()
keychain = app.default_keychain()
keychain.get_signer({})
# endregion Globals


def switcher(pnpc_args):
    logging.debug("Switcher Arguments: %s", pnpc_args)
    if pnpc_args.add is not None:
        logging.debug('Advertising {0} in {1}'.format(pnpc_args.add.publisher_name, pnpc_args.add.as_list))
        o_msg = PnpIMessage()
        msg = AddMessage()
        msg.publisher_name = enc.Name.from_str(pnpc_args.add.publisher_name[0])
        logging.debug('AS List: {}'.format(pnpc_args.add.as_list))
        named_list = convert_strings_to_names(pnpc_args.add.as_list)
        msg.hosting_as_list[:] = named_list
        logging.debug('Named list: {}'.format(msg.hosting_as_list))
        o_msg.add_message = msg
        logging.debug('Add message:\n{}'.format(o_msg.add_message))
    elif pnpc_args.remove is not None:
        logging.debug('Removing {0} from {1}'.format(pnpc_args.remove.publisher_name, pnpc_args.remove.as_list))
        o_msg = PnpIMessage()
        msg = RemoveMessage()
        msg.publisher_name = enc.Name.from_str(pnpc_args.remove.publisher_name[0])
        msg.hosting_as_list = convert_strings_to_names(pnpc_args.remove.as_list)
        o_msg.remove_message = msg
        logging.debug('Remove message:\n{}'.format(o_msg.remove_message))
    elif pnpc_args.set is not None:
        logging.debug(
            'Setting the advertisements of {0} to {1}'.format(pnpc_args.set.publisher_name, pnpc_args.set.as_list))
        o_msg = PnpIMessage()
        msg = SetMessage()
        msg.publisher_name = enc.Name.from_str(pnpc_args.set.publisher_name[0])
        msg.hosting_as_list = convert_strings_to_names(pnpc_args.set.as_list)
        o_msg.set_message = msg
        logging.debug('Set message:\n{}'.format(o_msg.set_message))
    elif pnpc_args.get is not None:
        logging.debug('Getting the advertisements of {0}'.format(pnpc_args.get.publisher_name))
        o_msg = PnpIMessage()
        msg = GetMessage()
        msg.publisher_name = enc.Name.from_str(pnpc_args.get.publisher_name[0])
        o_msg.get_message = msg
        logging.debug('Get message:\n{}'.format(o_msg.get_message))
    elif pnpc_args.getlpm is not None:
        logging.debug('Getting (LPM Mode) the advertisements of {0}'.format(pnpc_args.getlpm.publisher_name))
        o_msg = PnpIMessage()
        msg = GetLpmMessage()
        msg.publisher_name = enc.Name.from_str(pnpc_args.getlpm.publisher_name[0])
        o_msg.getlpm_message = msg
        logging.debug('Get message:\n{}'.format(o_msg.getlpm_message))
    else:
        exit(get_examples())
    return o_msg


async def main(msg):
    try:
        logging.debug('About to express an interest to: {}'.format(pnps_string_name))
        app_param_encoded_message = msg.encode()
        logging.debug('App Param encoded message: {}'.format(app_param_encoded_message))
        logging.debug('Sending Interest {} {}'
                      .format(pnps_string_name, enc.InterestParam(must_be_fresh=True, lifetime=6000)))
        data_name, content, pkt_context = await app.express(
            # Interest Name
            pnps_string_name,
            validator=appv2.pass_all,
            app_param=app_param_encoded_message,
            signer=keychain.get_signer({}),
            must_be_fresh=True,
            can_be_prefix=False,
            lifetime=6000)
        # Print out Data Name, MetaInfo and its content.
        logging.debug('Received Data Name: {}'.format(enc.Name.to_str(data_name)))
        logging.debug(pkt_context['meta_info'])
        logging.debug(bytes(content) if content else None)
        dpkt = PnpDMessage.parse(content)
        print('{} -> {}'.format(enc.Name.to_str(dpkt.publisher_name), convert_names_to_strings(dpkt.hosting_as_list)))
    except types.InterestNack as err:
        # A NACK is received
        print('Nacked with reason={}'.format(err.reason))
    except types.InterestTimeout:
        # Interest times out
        print('Timeout')
    except types.InterestCanceled:
        # Connection to NFD is broken
        print('Canceled')
    except types.ValidationFailure:
        # Validation failure
        print('Data failed to validate')
    except TypeError:
        print('not found')
    finally:
        app.shutdown()


if __name__ == "__main__":
    args = get_args()

    # region Configuration
    path = pathlib.Path(args.config)
    if not path.exists():
        exit('Can not find the configuration file in: {}'.format(args.config))
    application_config = configparser.ConfigParser()
    application_config.read(args.config)
    pnps_string_name = application_config.get('PNPC', 'server_route')
    pnps_ndn_name = enc.Name.from_str(pnps_string_name)
    # endregion Configuration

    msg_to_send = switcher(args)
    logging.debug('Start Encoding')
    logging.debug(msg_to_send.encode())
    logging.debug('Finish Encoding')
    logging.debug(msg_to_send)
    app.run_forever(after_start=main(msg_to_send))
