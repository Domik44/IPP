<?php
    ini_set('display_errors', 'stderr');

    class XML{
        // Head
        private $encoding;
        private $version;
        // Instruction
        private $order;
        private $opcode;
        // Argument
        private $num_args;
        private $types;
        private $param;

        // Constructor
        function __construct($encoding, $version){
            $this->encoding = $encoding;
            $this->version = $version;
            $this->order = 1;
        }

        // Setter
        function setter($opcode, $num_args, $types, $param){
            // Clearing arrays
            $this->types = array();
            $this->param = array();

            // Setting parametres for intsruction
            $this->opcode = $opcode;
            $this->num_args = $num_args;
            $this->types = $types;
            $this->param = $param;
        }

        // Printing XML head to output
        function make_head($language){
            fprintf(STDOUT, "<?xml version=\"%0.1f\" encoding=\"%s\"?>\n", $this->version, $this->encoding);
            fprintf(STDOUT, "<program language=\"%s\">\n", trim($language,'.')); // PREDELAT -> na vystupu chteji bez tecky -> misto .IPP -> IPP
        }

        // Creating instruction
        function make_instruction(){
            fprintf(STDOUT, "    <instruction order=\"%d\" opcode=\"%s\">\n", $this->order, $this->opcode);
            for($i = 0; $i < $this->num_args; $i++){
                $this->add_argument($i);
            }
            fprintf(STDOUT, "    </instruction>\n");
            $this->order++;
        }

        // Adding arguments to instruction
        function add_argument($num){
            if($this->types[$num] == "bool")
                $this->types[$num] = strtolower($this->types[$num]);
            fprintf(STDOUT, "        <arg%d type=\"%s\">%s</arg%d>\n", $num+1, $this->types[$num], $this->param[$num], $num+1);
        }

        // Ending XML file
        function end_xml(){
            fprintf(STDOUT, "</program>\n");
        }
    }

    // BASIC CHECKIGN AND EDITING FUNCTIONS ///////////////////////////////////////////////////
    // Checking input arguments validity
    function check_args($argc, $argv){
        if($argc > 1){ // HELP function
            if($argv[1] == "--help"){ // Prints out help function
                fprintf(STDOUT, "Usage: \n");
                fprintf(STDOUT, "\tphp8.1 parse.php <arguments> \n");
                fprintf(STDOUT, "Possible arguments: \n");
                fprintf(STDOUT, "\t<input_file \n");
                fprintf(STDOUT, "\t--help \n");
                fprintf(STDOUT, "Description: \n");
                fprintf(STDOUT, "\tProgram takes source code from STDIN, checks lexical and syntactical analyse. \n");
                fprintf(STDOUT, "\tIf everything is all right, program proceeds to write code in XML format. \n");
                exit(0);
            }
            else{ // Wrong format of arguments -> ends program
                fprintf(STDERR, "Wrong arguments! \n");
                fprintf(STDERR, "For right usage see: --help \n");
                exit(10);
            }
        }
    }

    // Trimming comments from lines
    function trim_comments($line){ 
        $found = strpos($line, "#");
        if($found || $line[0] == '#'){
            $line = substr($line, 0, $found);
        }

        return $line;
    }

    // LEXICAL AND SYNTACKICAL CHECKIGN FUNCTIONS ///////////////////////////////////////////////////
    // Checking head of the source file
    function check_head($line_parsed, $xml){
        if($line_parsed[0] != ".IPPcode22" || count($line_parsed) > 1){ // Must have .IPPcode22, otherwise its error
            fprintf(STDERR, "Wrong head format!\n");
            exit(21);
        }

        $xml->make_head($line_parsed[0]);

        return true;
    }

    // Checking number of parameres
    function check_params($line_parsed, $correct_params, $err_msg){
        if(count($line_parsed) != $correct_params){
            fprintf(STDERR, "Wrong parametres for %s!\n", $line_parsed[0]);
            fprintf(STDERR, "%s should have %d parametre/s%s!\n", $line_parsed[0], ($correct_params - 1), $err_msg);
            exit(23);
        }
    }

    // Checking symb type validity
    function check_symb($str){
        $res = explode('@', $str);
        if(preg_match("(GF|LF|TF)", $res[0])){
            check_var($str);
            $res[0] = "var";
            $res[1] = $str;
            
        }
        elseif($res[0] == "int"){
            if(!preg_match("/^[-|+]?[[:digit:]]+$/", $res[1])){
                fprintf(STDERR, "Wrong format of int number %s!\n", $res[1]);
                exit(23);
            }
        }
        elseif($res[0] == "bool"){
            if(!preg_match("/^(true|false)$/", $res[1])){
                fprintf(STDERR, "Wrong format of bool type %s!\n", $res[1]);
                exit(23);
            }
        }
        elseif($res[0] == "string"){
            if(!preg_match("/^string@(\\\[0-9]{3}|[^\\\\\"'])*$/", $str)){
                fprintf(STDERR, "Wrong format of string %s!\n", $res[1]);
                exit(23);
            }
        }
        elseif($res[0] == "nil"){
            if(!preg_match("/^(nil)$/", $res[1])){
                fprintf(STDERR, "Wrong format of nil!\n");
                exit(23);
            }
        }
        elseif($res[0] == "label"){
            if(count($res) <= 1){
                exit(23);
            }
            check_label($res[1]);
        }
        else{
            fprintf(STDERR, "Wrong format of symb %s!\n", $str);
            exit(23);
        }

        if($res[0] == "string" || $res[0] == "var" || $res[0] == "label"){ // Replacing problematic characters
            if(preg_match("/<|>|&/", $res[1])){
                $res[1] = replace_special_chars($res[1]);
            }    
        }

        return $res; // Returns splitted string by @
    }

    // Checking var type validity
    function check_var($str){
        if(!preg_match("/^(GF|LF|TF)@[_\-$&%*!?[:alpha:]][_\-$&%*!?[:alnum:]]*$/", $str)){
            fprintf(STDERR, "Wrong format of variable %s!\n", $str);
            exit(23);
        }
    }

    // Checking label type validity
    function check_label($str){
        if(!preg_match("/^([_\-$&%*!?[:alpha:]])([_\-$&%*!?[:alnum:]])*$/", $str)){
            fprintf(STDERR, "Wrong format of label %s!\n", $str);
            exit(23);
        }
    }

    // Checking type validity
    function check_type($str){
        if(!preg_match("/^(int|bool|nil|string)$/", $str)){
            fprintf(STDERR, "Wrong format of type %s!\n", $str);
            exit(23);
        }
    }

    // OTEHR FUNCTIONS ///////////////////////////////////////////////////
    // Replacing problematic chars in XML
    function replace_special_chars($str){
       $str = preg_replace("/&/", "&amp;",$str);
       $str = preg_replace("/</", "&lt;",$str);
       $str = preg_replace("/>/", "&gt;",$str);

       return $str;
    }

    // MAIN ///////////////////////////////////////////////////////
    $xml = new XML("UTF-8", 1.0);
    check_args($argc, $argv);

    $head = false;
    while($line = fgets(STDIN)){ // Loading lines from input file
        $line = trim_comments($line); // Getting rid of comments
        $line = trim($line); // Getting rid of whitespaces in the begining/end
        $line = trim(preg_replace('/\s\s+/', ' ', str_replace("\n", " ", $line))); // replacing useless whitespaces in between words

        if(empty($line)){ // Skipping empty lines
            continue;
        }

        $line_parsed = explode(' ', trim($line, "\n")); // Parsing lines

        if(!$head){ // Checking first line for head of the file
            $head = check_head($line_parsed, $xml);
        }
        else{
            $line_parsed[0] = strtoupper($line_parsed[0]); // Making opcode with uppercases
            switch($line_parsed[0]){ // Instruction checking
                // No parameters:
                case "CREATEFRAME":
                case "PUSHFRAME":
                case "POPFRAME":
                case "RETURN":
                case "BREAK":
                    // Checking validity
                    check_params($line_parsed, 1, ""); // Checking number of parameters
                    // Writing out
                    $xml->setter($line_parsed[0], 0, array(), array()); // Setting xml parameters
                    $xml->make_instruction(); // Writing on STDOUT
                    break;

                // One param:
                // <var>:
                case "DEFVAR":
                case "POPS":
                    // Checking validity
                    check_params($line_parsed, 2, " <var>");
                    check_var($line_parsed[1]);
                    // Parsing string arguments
                    $line_parsed[1] = replace_special_chars($line_parsed[1]);
                    // Writing out
                    $xml->setter($line_parsed[0], 1, array("var"), array($line_parsed[1]));
                    $xml->make_instruction();
                    break;
                // <symb>:
                case "PUSHS":
                case "WRITE":
                case "EXIT":
                case "DPRINT":
                    // Checking validity
                    check_params($line_parsed, 2, " <symb>");
                    check_symb($line_parsed[1]);
                    // Parsing string arguments
                    $parsed = check_symb($line_parsed[1]);
                    // Writing out
                    $xml->setter($line_parsed[0], 1, array($parsed[0]), array($parsed[1]));
                    $xml->make_instruction();
                    break;
                // <label>:
                case "CALL":
                case "LABEL":
                case "JUMP":
                    // Checking validity
                    check_params($line_parsed, 2, " <label>");
                    check_label($line_parsed[1]);
                    $line_parsed[1] = replace_special_chars($line_parsed[1]);
                    // Writing out
                    $xml->setter($line_parsed[0], 1, array("label"), array($line_parsed[1]));
                    $xml->make_instruction();
                    break;

                // Two param:
                // <var> <symb>:
                case "MOVE":
                case "INT2CHAR":
                case "STRLEN":
                case "TYPE":
                case "NOT":
                    // Checking validity
                    check_params($line_parsed, 3, " <var> <symb>");
                    check_var($line_parsed[1]);
                    check_symb($line_parsed[2]);
                    // Parsing string arguments
                    $line_parsed[1] = replace_special_chars($line_parsed[1]);
                    $parsed = check_symb($line_parsed[2]);
                    // Writing out
                    $xml->setter($line_parsed[0], 2, array("var",$parsed[0]), array($line_parsed[1], $parsed[1]));
                    $xml->make_instruction();
                    break;
                // <var> <type>:
                case "READ":
                    // Checking validity
                    check_params($line_parsed, 3, " <var> <type>");
                    check_var($line_parsed[1]);
                    check_type($line_parsed[2]);
                    // Parsing string arguments
                    $line_parsed[1] = replace_special_chars($line_parsed[1]);
                    // Writing out
                    $xml->setter($line_parsed[0], 2, array("var","type"), array($line_parsed[1], $line_parsed[2]));
                    $xml->make_instruction();
                    break;

                // Three param:
                // <var> <symb> <symb>
                case "ADD":
                case "SUB":
                case "IDIV":
                case "MUL":
                case "AND":
                case "OR":
                case "GT":
                case "EQ":
                case "LT":
                case "CONCAT":
                case "GETCHAR":
                case "SETCHAR":
                case "STRI2INT":
                    // Checking validity
                    check_params($line_parsed, 4, " <var> <symb> <symb>");
                    check_var($line_parsed[1]);
                    check_symb($line_parsed[2]);
                    check_symb($line_parsed[3]);
                    // Parsing string arguments
                    $line_parsed[1] = replace_special_chars($line_parsed[1]);
                    $parsed = check_symb($line_parsed[2]);
                    $parsed_2 = check_symb($line_parsed[3]);
                    // Writing out
                    $xml->setter($line_parsed[0], 3, array("var", $parsed[0], $parsed_2[0]), array($line_parsed[1], $parsed[1], $parsed_2[1]));
                    $xml->make_instruction();
                    break;
                // <label> <symb> <symb>
                case "JUMPIFEQ":
                case "JUMPIFNEQ":
                    // Checking validity
                    check_params($line_parsed, 4, " <label> <symb> <symb>");
                    check_label($line_parsed[1]);
                    check_symb($line_parsed[2]);
                    check_symb($line_parsed[3]);
                    // Parsing string arguments
                    $parsed = check_symb($line_parsed[2]);
                    $parsed_2 = check_symb($line_parsed[3]);
                    $line_parsed[1] = replace_special_chars($line_parsed[1]);
                    // Writing out
                    $xml->setter($line_parsed[0], 3, array("label", $parsed[0], $parsed_2[0]),  array($line_parsed[1], $parsed[1], $parsed_2[1]));
                    $xml->make_instruction();
                    break;
                // Not valid instruction 
                default:
                    fprintf(STDERR, "%s is not an instruction!\n", $line_parsed[0]);
                    exit(22);
                    break;
            }
        }
    }

    $xml->end_xml();
?>