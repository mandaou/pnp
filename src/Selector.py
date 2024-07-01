from aenum import Enum, NoAlias


class BackEndType(Enum):
    utf = 1
    named = 2


class Algorithms(Enum):
    _settings_ = NoAlias
    SimpleDictionary = BackEndType.utf
    Trie = BackEndType.utf                 # https://github.com/google/pygtrie - Normal Trie
    STrie = BackEndType.utf                # https://github.com/google/pygtrie - String Trie
    CTrie = BackEndType.utf                # https://github.com/google/pygtrie - Char Trie
    ComponentTextTrie = BackEndType.utf
    CharacterTextTrie = BackEndType.utf
    NamedTree = BackEndType.named        # Based on https://github.com/google/pygtrie and use NDN Names instead of Strings
    ECHT = BackEndType.named
    UTFTest = BackEndType.utf
    NamedTest = BackEndType.named
