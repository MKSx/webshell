import argparse, json, sys, os


class Menu:
    Config = None
    ConfigFile = ''
    def Init(config, filename='webshell.config.json'):
        Menu.Config = config
        Menu.ConfigFile = filename
        def is_file(file):
            if os.path.isfile(file):
                return file
            raise argparse.ArgumentTypeError(f"Leitura de arquivo: {file} não é um arquivo válido")

        parser = argparse.ArgumentParser(usage='%(prog)s [options]')
        parser.add_argument('-u', '--url', help='Url da webshell', type=str)
        parser.add_argument('--username', help='Nome de usuário da webshell', type=str, default=Menu.Config.User)
        parser.add_argument('--password', help='Nome de usuário da webshell', type=str, default=Menu.Config.Pass)
        parser.add_argument('--key', help='Chave usada para cifrar as mensagens enviadas e recebidas da webshell', type=str, default=Menu.Config.Key)
        parser.add_argument('--bigip-name', help='Nome do Cookie do Big Ip', type=str, default=Menu.Config.CookieIPName)
        parser.add_argument('--bigip-value', help='Valor do Cookie do Big Ip', type=str, default=Menu.Config.CookieIPValue)
        parser.add_argument('--post-cmd', help='Nome da variável que irá receber os comandos na webshell', type=str, default=Menu.Config.PostCmd)
        parser.add_argument('--post-file', help='Nome da variável que irá receber o arquivo na webshell', type=str, default=Menu.Config.PostFile)
        parser.add_argument('--disable-ping', help='Desabilita o ping inicial', action='store_true')
        parser.add_argument('--create-config', help='Cria uma configuração rápida', action='store_true')
        parser.add_argument('--load-config', help='Carrega arquivo de configuração rápido', type=str)
        parser.add_argument('--config-file', help='Arquivo de configuração', type=is_file)
        parser.add_argument('--remove-config', help='Remove uma configuração salva', type=str)
        parser.add_argument('--update-config', help='Atualiza uma configuração existente', type=str)
        

        
        args = parser.parse_args(sys.argv[1:])
        if args.update_config:
            args.create_config = args.update_config
            
        
        if args.config_file:
            Menu.ConfigFile = args.config_file

        if args.create_config:
            if not Menu.CreateConfig():
                return False
        elif args.load_config:
            if not Menu.LoadConfig(args.load_config):
                return False
        elif args.remove_config:
            print(f'Configuração {args.remove_config} removida com sucesso!' if Menu.RemoveConfig(args.remove_config) else f'Configuração {args.remove_config} não foi localizada')
            return False
        else:
            if not args.url:
                print("Informe a url da webshell com --url ou -u")
                return False
                
            Menu.SetConfig(args)
        
        return True

    def RemoveConfig(configname):
        config = Menu.LoadConfigFile(Menu.ConfigFile)

        if not config or configname not in config:
            return False

        del config[configname]
        
        return Menu.SaveConfigFile(Menu.ConfigFile, config)
    def LoadConfigFile(filename):
        if not os.path.isfile(filename):
            return False

        with open(filename, 'r') as file:
            try:
                return json.load(file)
            except Exception as e:
                print(e)
        
        return False
    def SaveConfigFile(filename, data):
        with open(filename, 'w') as file:
            try:
                file.write(json.dumps(data))
                return True
            except Exception as e:
                print(e)
        return False
        
    def CreateConfig():
        options = {
            'name': {'message': 'Nome da configuração: ', 'default': None},
            'url': {'message': f'URL: ({Menu.Config.Url}) ', 'default': Menu.Config.Url},
            'user': {'message': f'Nome de usuário: ({Menu.Config.User}) ', 'default': Menu.Config.User},
            'pass': {'message': f'Senha do usuário: ({Menu.Config.Pass}) ', 'default': Menu.Config.Pass},
            'key': {'message': f'Chave da comunicação: ({Menu.Config.Key}) ', 'default': Menu.Config.Key},
            'ping': {'message': f'Habilitar ping de inicio: ({"yes" if Menu.Config.AllowPing else "no"}) ', 'default': 'yes' if Menu.Config.AllowPing else 'no', 'bool': True},
            'ipname': {'message': f'Nome do Cookie Bip IP: ({Menu.Config.CookieIPName}) ', 'default': Menu.Config.CookieIPName},
            'ipvalue': {'message': f'Valor do Cookie Big Ip: {f"({Menu.Config.CookieIPValue}) " if isinstance(Menu.Config.CookieIPValue, str) else ""}', 'default': Menu.Config.CookieIPValue if isinstance(Menu.Config.CookieIPValue, str) else ''},
            'cmd': {'message': f'Parâmetro para envio dos comandos: ({Menu.Config.PostCmd}) ', 'default': Menu.Config.PostCmd},
            'file': {'message': f'Parâmetro para envio de arquivos: ({Menu.Config.PostFile}) ', 'default': Menu.Config.PostFile}
        }
        try:
            data = {}
            for name in options:
                temp = input(options[name]['message']).strip()
                if len(temp) < 1 and options[name]['default'] != None:
                    temp = options[name]['default']
                
                if 'bool' in options[name]:
                    temp = True if temp.lower() in ['yes', 'y'] else False
                    
                data[name] = temp

            print(json.dumps(data, indent=4))

            temp = input("Salvar configuração? (yes) ").strip()
            if len(temp) < 1:
                temp = 'yes'

            if temp.lower() in ['yes', 'y']:
                config = Menu.LoadConfigFile(Menu.ConfigFile)
                name = data['name']
                del data['name']
                if config:
                    if name in config:
                        temp = input(f"Deseja atualizar a configuração {name}? (yes) ").strip()
                        if len(temp) < 1:
                            temp = 'yes'
                        if temp.lower() not in ['yes', 'y']:
                            print("Operação abortada pelo usuário!")
                            return False
                else:
                    config = {}
                
                config[name] = data
                
                Menu.SaveConfigFile(Menu.ConfigFile, config)
                Menu.LoadConfigData(config[name])
                print("Configuração salva com sucesso!")
                return True
        except KeyboardInterrupt:
            pass
        

        print("\nOperação abortada pelo usuário!")
        return False


    def LoadConfigData(config):
        
        Menu.Config.Url = config['url']
        Menu.Config.User = config['user']
        Menu.Config.Pass = config['pass']
        Menu.Config.Key = config['key']
        Menu.Config.AllowPing = config['ping']
        Menu.Config.CookieIPName = config['ipname']
        Menu.Config.CookieIPValue = config['ipvalue']
        Menu.Config.PostCmd = config['cmd']
        Menu.Config.PostFile = config['file']

    def LoadConfig(name):
        config = Menu.LoadConfigFile(Menu.ConfigFile)
        if not config or name not in config:
            print(f"Configuração {name} não encontrada")
            return False
        
        Menu.LoadConfigData(config[name])
        return True

    
    def SetConfig(args):
        
        Menu.Config.AllowPing = args.disable_ping
        Menu.Config.User = args.username
        Menu.Config.Pass = args.password
        Menu.Config.Key = args.key
        Menu.Config.PostCmd = args.post_cmd
        Menu.Config.PostFile = args.post_file
        Menu.Config.Url = args.url
        Menu.Config.CookieIPValue = False if not(isinstance(args.bigip_value, str)) or len(args.bigip_value) < 1 else args.bigip_value
        Menu.Config.CookieIPName = False if Menu.Config.CookieIPValue == False or not args.bigip_name or len(args.bigip_name) < 1 else args.bigip_name

    
