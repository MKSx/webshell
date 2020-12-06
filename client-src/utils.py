from urllib.parse import urlparse
import json, pingparsing, sys
from colorama import Style, Fore
from colorama import init as colorama_init
from termcolor import colored

colorama_init()

class Util(object):
    domain = lambda url: urlparse(url).netloc
    def ping(dest):
        ping_parser = pingparsing.PingParsing()
        transmitter = pingparsing.PingTransmitter()
        transmitter.destination = dest
        transmitter.count = 1
        result = ping_parser.parse(transmitter.ping()).as_dict()

        if 'rtt_avg' in result:
            return result['rtt_avg']
        
        return None

    def Fatal(msg):
        print(f'{Style.BRIGHT}{Fore.RED}[FATAL ERROR] {Style.RESET_ALL}{Style.BRIGHT}{msg}{Style.RESET_ALL}')
        sys.exit(0)
    def Error(msg):
        print(f'{Style.BRIGHT}{Fore.RED}[ERROR] {Style.RESET_ALL}{Style.BRIGHT}{msg}{Style.RESET_ALL}')
    def Warn(msg):
        print(f'{Style.BRIGHT}{Fore.YELLOW}[WARNING] {Style.RESET_ALL}{Style.BRIGHT}{msg}{Style.RESET_ALL}')
    def Success(msg):
        print(f'{Style.BRIGHT}{Fore.GREEN}[WARNING] {Style.RESET_ALL}{Style.BRIGHT}{msg}{Style.RESET_ALL}')
    def Info(msg):
        print(f'{Style.BRIGHT}{Fore.BLUE}[INFO] {Style.RESET_ALL}{Style.BRIGHT}{msg}{Style.RESET_ALL}')

    def verifyCodes(res):
        if res.status_code == 500:
            print(res.text.strip())
            Util.Fatal("Erro Interno no servidor!")
            return False
        if res.status_code == 302 or res.status_code == 301 or res.status_code == 404:
            
            Util.Fatal("Verifique se o arquivo ainda existe no servidor, redirecionamento feito para " + res.headers.get('Location'))
        if res.status_code == 403:
            Util.Faltal("Requisição bloqueada, verifique a existência de WAF na aplicação")

        return True
