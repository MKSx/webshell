<?php
global $wShell;

$wShell->on("teste", function($args, $length) use ($wShell){
    return $wShell->setResponse("testando 123");
});
