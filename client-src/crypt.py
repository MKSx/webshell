import base64

class crypt(object):
    Key = False
    Len = 0
    @staticmethod
    def encode(value, pr=False):
        if len(value) < 1:
            return ''
    
        value = base64.b64encode(crypt.xor(value, pr).encode('latin-1')).decode('latin-1')[::-1]
        if len(value) > 2:
            value = value[2:] + (value[:2])[::-1]
        return value


    @staticmethod
    def decode(value):
        l = len(value)

        if not (l > 0 or crypt.Len > 0):
            return ''
    
        return crypt.xor(base64.b64decode(((value[l - 2:])[::-1] + value[:l - 2] if l > 2 else value)[::-1].encode('latin-1')).decode('latin-1'))

    @staticmethod
    def xor(value, pr=False):
        l = len(value)
        

        if crypt.Len > 0 and l > 0:
            k = crypt.generateKey(l)
            if pr:
                print("keylen:", len(k), "|", "valuelen:", l)
            return ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(value, k))
        
        return ''
        
    @staticmethod
    def generateKey(l):
        if crypt.Len < 1 and l < 1:
            return False

        dif = l - crypt.Len
        if dif > 0:
            return (crypt.Key + crypt.Key * (dif // crypt.Len + (1 if dif % crypt.Len else 0)))[0:l]

        return crypt.Key if dif == 0 else crypt.Key[0:l]
        
        
    def setKey(value):
        crypt.Key = value
        if value:
            crypt.Len = len(crypt.Key)
        else:
            crypt.Len = 0
