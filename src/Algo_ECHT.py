import pickle
from BEABC import BEABC
from Selector import Algorithms


class ECHTBE(BEABC):
    def __init__(self):
        super().__init__(Algorithms.ECHT)
        self.description = 'Encoded Component Hashed Trie'
        self._data = {}
        self.total_nodes = 0
        self.processed_nodes = 0
        self.total_components = 0

    def size(self):
        return len(pickle.dumps(self._data))

    def add(self, entry_key, entry_value):
        i = 0
        current_dict = self._data
        for component_byte in entry_key:
            self.total_components += 1
            b = bytes(component_byte)
            i += 1
            if i == len(entry_key):
                # is executed when we reach the last node
                try:
                    # poke the key, if it does not exist, create it under keyError
                    current_dict[b]
                    # the next statement will be reached only if the previous line didn't throw an error
                    # in this case, this leaf node has already been created earlier, so set its value
                    current_dict = current_dict[b]

                    # TODO: to be checked !!
                    # current_dict[''] = entry_value
                    v = current_dict['']
                    if v is not None:
                        for e in entry_value:
                            if e not in v:
                                v.append(e)
                    current_dict[''] = v

                except KeyError:
                    entry_dict = {'': entry_value}
                    current_dict[b] = entry_dict
                    current_dict = entry_dict
                    self.total_nodes += 1
            else:
                try:
                    current_dict[b]
                    # the next statement will be reached only if the previous line didn't throw an error
                    # in this case, this intermediary node has already been created earlier
                    current_dict = current_dict[b]
                except KeyError:
                    # this is where we handle intermediary non-existent nodes
                    intermediary_dict = {'': None}
                    current_dict[b] = intermediary_dict
                    current_dict = intermediary_dict
                    self.total_nodes += 1
        i += 1
        self.processed_nodes += 1

    def manual_add(self, entry_key, entry_value):
        self.add(entry_key, entry_value)

    def get(self, entry_key):
        d = self._data
        i = 1
        for component_byte in entry_key:
            b = bytes(component_byte)
            try:
                d[b]
                d = d[b]
                if i == len(entry_key):
                    r = d['']
                    # Manar try to fix
                    if r is not None:
                        if len(r) == 1:
                            return d[''][0]
                        else:
                            return d['']
                i += 1
            except KeyError:
                return []
        return []

    def lpm(self, entry_key):
        current_key = []
        last_good_node_key = None
        last_good_node_value = None
        d = self._data
        i = 1
        for component_byte in entry_key:
            b = bytes(component_byte)
            try:
                d[b]
                current_key.append(component_byte)
                if d[b][''] != '':
                    last_good_node_key = current_key
                    last_good_node_value = d[b]['']
                d = d[b]
                if i == len(entry_key):
                    r = d['']
                    # Manar try to fix
                    if r is not None:
                        if len(r) == 1:
                            return last_good_node_key, d[''][0]
                        else:
                            return last_good_node_key, d['']
                i += 1
            except KeyError:
                return last_good_node_key, last_good_node_value
        return last_good_node_key, last_good_node_value

    def bcm(self, entry_key):
        return self.lpm(entry_key)

    def set(self, entry_key, entry_value):
        # ToDo: implement method
        raise NotImplementedError

    def remove(self, entry_key, entry_values='all'):
        d = self._data
        i = 1
        for c in entry_key:
            b = bytes(c)
            try:
                d[b]
                d = d[b]
                if i == len(entry_key):
                    r = d['']
                    if len(entry_values) == 1:
                        r.remove(entry_values)
                    else:
                        for v in entry_values:
                            r.remove(v)
                    return d['']
                i += 1
            except KeyError:
                return []
        return []

    def is_entry(self, entry_key):
        d = self._data
        i = 1
        for c in entry_key:
            b = bytes(c)
            try:
                d[b]
                d = d[b]
                if i == len(entry_key):
                    r = d['']
                    return True, None
                i += 1
            except KeyError:
                return False, None
        return False, None

    def to_dict(self):
        return self._data

    def get_total_nodes(self):
        return self.total_nodes

    def get_total_components(self):
        return self.total_components

    def get_depth(self):
        # ToDo : implement method
        raise NotImplementedError

    def dump(self):
        # ToDo : implement method
        raise NotImplementedError
