<?php

//include_once "crypt.php";
//session_start();

class UploadInBlocks{
    public static $KEY = "";

    private static $error = false;
    public static function Error(){
        return self::$error;
    }
    public static function Uploading(){
        return isset($_SESSION['uploadtmp']);
    }
    public static function Start($dest){
        self::$error = false;
        if(!isset($_SESSION['uploadtmp'])){
            $_SESSION['uploading']  = true;
            $_SESSION['uploadtmp'] = dirname($dest).'/'.hash('adler32', uniqid(rand(), true));
            $_SESSION['uploadname'] = $dest;
            return true;
        }
        return false;
    }
    public static function Upload($block){
        self::$error = false;
        if(isset($_SESSION['uploadtmp'])){
            if(strlen($block) > 0){
                $file = fopen($_SESSION['uploadtmp'], 'a');
                if(!$file){
                    self::$error = 'Falha ao tentar abrir o arquivo '.$_SESSION['uploadtmp'];
                    return false;
                }
                fwrite($file, $block);
                fclose($file);
            }
            return true;
        }
        return false;
    }
    public static function Stop(){
        self::$error = false;
        if(isset($_SESSION['uploadtmp'])){
            $file = fopen($_SESSION['uploadtmp'], 'r');

            if(!$file){
                self::$error = "Falha ao tentar abrir o arquivo temporário ".$_SESSION['uploadtmp'];
                return false;
            }
            $content = fread($file, filesize($_SESSION['uploadtmp']));
            fclose($file);
            $file = fopen($_SESSION['uploadname'],'w');
            if(!$file){
                self::$error = "Falha ao tentar abrir o arquivo de destino ".$_SESSION['uploadname'];
                return false;
            }
            fwrite($file, Crypt::decode($content, self::$KEY));
            fclose($file);
            self::Cancel();
            return true;
        }
        return false;
    }
    public static function FileName(){
        return isset($_SESSION['uploadname']) ? $_SESSION['uploadname'] : '';
    }
    public static function TempName(){
        return isset($_SESSION['uploadtmp']) ? $_SESSION['uploadtmp'] : '';
    }
    public static function Cancel(){
        if(isset($_SESSION['uploadtmp'])){
            if(file_exists($_SESSION['uploadtmp'])){
                @unlink($_SESSION['uploadtmp']);;
            }
            unset($_SESSION['uploadtmp']);
            unset($_SESSION['uploadname']);
        }
    }
}
