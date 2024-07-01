from ndn.types import ValidResult
import ndn.encoding as enc
from Cryptodome.Hash import SHA256


async def pass_all(_name, _sig, _context):
    # ToDo: implement method
    h = SHA256.new()
    for content in _sig.signature_covered_part:
        h.update(content)
    kl = enc.Name.normalize(_sig.signature_info.key_locator.name)

    # return pass on all cases
    return ValidResult.PASS
