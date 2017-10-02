import collections

from ...coins.bitcoin.ScriptTools import BitcoinScriptTools as ScriptTools  # BRAIN DAMAGE
from ...coins.bitcoin.VM import BitcoinVM as VM  # BRAIN DAMAGE
from ...serialize import h2b
from pycoin.satoshi import der


from pycoin.intbytes import int2byte


def generate_default_placeholder_signature(generator):
    return h2b(
        "3045022100fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd036414002207"
        "fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a001")


class ScriptType(object):
    """
    In the "match template" we have string that match data types:
      'DATA': matches any data, for example after OP_RETURN
      'PUBKEY': matches data of length 33 - 120 (for public keys)
      'PUBKEYHASH': matches data of length 20 (for public key hashes)
    """
    def __init__(self):
        raise NotImplemented()

    @classmethod
    def subclasses(cls, skip_self=True):
        for c in cls.__subclasses__():
            for c1 in c.subclasses(skip_self=False):
                yield c1
            if not skip_self:
                yield cls

    @classmethod
    def from_address(cls, text, netcodes=None):
        for sc in cls.subclasses():
            try:
                st = sc.from_address(text, netcodes=netcodes)
                return st
            except Exception:
                pass

    @classmethod
    def from_script(cls, script):
        for sc in cls.subclasses():
            try:
                st = sc.from_script(script)
                return st
            except Exception:
                pass

    @classmethod
    def match(cls, script):
        template = cls.TEMPLATE
        r = collections.defaultdict(list)
        pc1 = pc2 = 0
        while 1:
            if pc1 == len(script) and pc2 == len(template):
                return r
            if pc1 >= len(script) or pc2 >= len(template):
                break
            opcode1, data1, pc1 = VM.ScriptStreamer.get_opcode(script, pc1)
            opcode2, data2, pc2 = VM.ScriptStreamer.get_opcode(template, pc2)
            l1 = 0 if data1 is None else len(data1)
            if data2 == b'PUBKEY':
                if l1 < 33 or l1 > 120:
                    break
                r["PUBKEY_LIST"].append(data1)
            elif data2 == b'PUBKEYHASH':
                if l1 != 160/8:
                    break
                r["PUBKEYHASH_LIST"].append(data1)
            elif data2 == b'DATA':
                r["DATA_LIST"].append(data1)
            elif (opcode1, data1) != (opcode2, data2):
                break
        raise ValueError("script doesn't match")

    def _create_script_signature(
            self, secret_exponent, generator, signature_for_hash_type_f, signature_type, script):
        sign_value = signature_for_hash_type_f(signature_type, script)
        order = generator.order()
        r, s = generator.sign(secret_exponent, sign_value)
        if s + s > order:
            s = order - s
        return der.sigencode_der(r, s) + int2byte(signature_type)

    def address(self, netcode=None):
        from pycoin.networks.default import get_current_netcode
        if netcode is None:
            netcode = get_current_netcode()
        return self.info().get("address_f", lambda n: "(unknown)")(netcode)

    def solve(self, **kwargs):
        """
        The kwargs required depend upon the script type.
        """
        raise NotImplemented()
