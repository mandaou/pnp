import logging
from ndn import encoding as enc


# region Text <-> Name conversation
def convert_names_to_strings(name_or_list) -> list:
    result = []
    if len(name_or_list) == 0:
        # for empty names/list return empty
        result.append('')
    if type(name_or_list) is list:
        if len(name_or_list) == 1:
            logging.debug('Converting a list containing one NDN name {} to a single string'.format(name_or_list[0]))
            return enc.Name.to_str(name_or_list[0])
        logging.debug('Converting a list of NDN names to a list of strings')
        for n in name_or_list:
            result.append(enc.Name.to_str(n))
    else:
        logging.debug('Converting an NDN name to a string')
        result.append(enc.Name.to_str(name_or_list))
    logging.debug('Name->String conversation: {}'.format(result))
    return result


def convert_strings_to_names(string_or_list) -> list:
    result = []
    if len(string_or_list) == 0:
        logging.error("do we need to do something here? the name/list is empty")
        result.append(enc.Name.from_str(''))
    if type(string_or_list) is list:
        if len(string_or_list) == 1:
            logging.debug('Converting a list containing one string {} to a single NDN name'.format(string_or_list[0]))
            publisher = enc.Name.from_str(string_or_list[0])
            logging.debug('Converted name: {}'.format(publisher))
            return publisher
        else:
            logging.debug('Converting a list of strings to a list of NDN names')
            for n in string_or_list:
                result.append(enc.Name.from_str(n))
    else:
        logging.debug('Converting {} string to an NDN name'.format(string_or_list))
        result.append(enc.Name.from_str(string_or_list))
    logging.debug('String->Name conversation: {}'.format(result))
    return result
# endregion Text <-> Name conversation

# region Text-based NDN Modifications
def insert_component_prefix(text: str):
    t_list = text.split('/')
    results = list()
    for i in t_list[1:]:
        new_text = text.replace('/' + i, '/x' + i)
        results.append(new_text)
    return results


def insert_component_suffix(text: str):
    t_list = text.split('/')
    results = list()
    for i in t_list[1:]:
        new_text = text.replace('/' + i, '/' + i + 'x')
        results.append(new_text)
    return results


def insert_component_suffix_component(text: str):
    results = text + '/x'
    return results
# endregion Text Modifications
