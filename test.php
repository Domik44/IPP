
<!DOCTYPE html>
<html>
<body style="background-color:#D5D5D8;">
<title>IPP-Tester</title>
<h1>IPP-21/22 Tester</h1>
<?php

/**
 * @author Dominik Pop <xpopdo00@vutbr.cz>
 */

    // Class for storing input arguments
    class Args{
        public $directory; // path to dir with tests
        public $recursive; // boolean
        public $parse_script; // file
        public $parse_s_bool; // boolean
        public $int_script; // file
        public $int_s_bool; // boolean
        public $parse_only; // boolean
        public $int_only; // boolean
        public $jexam_path; // path to jexam
        public $noclean; // boolean
        public $jexam_bool; // boolean
        public $num_args; // number of arguments
        public $passed_tests; // number of passed tests
        public $failed_tests; // number of failed tests
        public $args_list; // list of some input arguments for HTML output
        public $wrong_tests_list; // list containing names and paths of wrong tests

        // Arguments constructor
        function __construct($argc){
            $this->directory = getcwd(); // gets actuall folder path
            $this->recusive = false;
            $this->parse_script = "parse.php";
            $this->int_script = "interpret.py";
            $this->parse_only = false;
            $this->int_only = false;
            $this->jexam_path = "/pub/courses/ipp/jexamxml";
            $this->noclean = false;
            $this->parse_s_bool = false;
            $this->int_s_bool = false;
            $this->jexam_bool = false;
            $this->num_args = $argc;
            $this->passed_tests = 0;
            $this->failed_tests = 0;
            $this->wrong_tests_list = array();
        }

        // Help function
        function help(){
            fprintf(STDOUT, "Usage: \n");
            fprintf(STDOUT, "\tphp8.1 test.php <arguments> \n");
            fprintf(STDOUT, "Possible arguments: \n");
            fprintf(STDOUT, "\t--help \n");
            fprintf(STDOUT, "\t--directory=\"path\" \n");
            fprintf(STDOUT, "\t--recursive \n");
            fprintf(STDOUT, "\t--parse-script=\"file\" \n");
            fprintf(STDOUT, "\t--int-script=\"file\" \n");
            fprintf(STDOUT, "\t--parse-only \n");
            fprintf(STDOUT, "\t--int-only \n");
            fprintf(STDOUT, "\t--jexampath=\"path\" \n");
            fprintf(STDOUT, "\t--noclean \n");
            fprintf(STDOUT, "Description: \n");
            fprintf(STDOUT, "\tProgram tests functionality of parse.php / interpret.py \n");
            exit(0);
        }

        // Setter of arguments
        function set_arg($arg){
            if(preg_match("/(=)/", $arg)){
                $parsed_arg = explode('=', $arg);
                $arg = $parsed_arg[0];
            }

            switch($arg){
                case "--help":
                    if($this->num_args != 2){
                        fprintf(STDERR, "Cannot combine --help with another arguments!\n");
                        exit(10);
                    }
                    $this->help();
                    break;
                case "--directory":
                    $this->directory = $parsed_arg[1];
                    $this->args_list = $this->args_list . "<li>directory</li>";
                    break;
                case "--recursive":
                    $this->recursive = true;
                    $this->args_list = $this->args_list . "<li>recursive</li>";
                    break;
                case "--parse-script":
                    $this->parse_script = $parsed_arg[1];
                    $this->parse_s_bool = true;
                    $this->args_list = $this->args_list . "<li>parse-script</li>";
                    break;
                case "--int-script":
                    $this->int_script = $parsed_arg[1];
                    $this->int_s_bool = true;
                    $this->args_list = $this->args_list . "<li>int-script</li>";
                    break;
                case "--parse-only":
                    $this->parse_only = true;
                    $this->args_list = $this->args_list . "<li>parse-only</li>";
                    break;
                case "--int-only":
                    $this->int_only = true;
                    $this->args_list = $this->args_list . "<li>int-only</li>";
                    break;
                case "--jexampath":
                    $this->jexam_path = $parsed_arg[1];
                    $this->args_list = $this->args_list . "<li>jexampath</li>";
                    break;
                case "--noclean":
                    $this->noclean = true;
                    $this->args_list = $this->args_list . "<li>noclean</li>";
                    break;
                default:
                    break;
            }
        }

        // Function begins parsing of arguments
        function parse_args($argv){
            $this->args_list = "<ul>";
            foreach($argv as &$arg){
                $this->set_arg($arg);
            }
            if($this->args_list == "<ul>"){
                $this->args_list = $this->args_list . "<li>None</li>";
            }
            $this->args_list = $this->args_list . "</ul>";
            $this->check_bools();
        }

        // Function checks arguments compability
        function check_bools(){
            if($this->parse_only){
                if($this->int_only || $this->int_s_bool){
                    fprintf(STDERR, "Cannot combine --parse-only with --int-only / --int-script\n");
                    exit(10);
                }
            }
            else if($this->int_only){
                if($this->parse_only || $this->parse_s_bool || $this->jexam_bool){
                    fprintf(STDERR, "Cannot combine --int-only with --parse-only / --parse-script / --jexampath\n");
                    exit(10);
                }
            }
        }

        // Function checks if given tester files exist
        function check_files(){
            if(!file_exists($this->directory)){
                fprintf(STDERR, "Directory path does not exist!\n");
                exit(41);
            }

            if(!file_exists($this->jexam_path)){
                fprintf(STDERR, "Jexam path does not exist!\n");
                exit(41);
            }

            if(!file_exists($this->parse_script) && !$this->int_only){
                fprintf(STDERR, "Parse-script file does not exist!\n");
                exit(41);
            }

            if(!file_exists($this->int_script) && !$this->parse_only){
                fprintf(STDERR, "Int-script file does not exist!\n");
                exit(41);
            }
        }
    }

// Function checks in test files exist
function check_for_files($file, $dir){
    $file_name = explode('.', $file);
    $file_name[0] = $dir."/".$file_name[0];

    if(!file_exists($file_name[0].".in")){
        $new = fopen($file_name[0].".in", "w");
        fclose($new);
    }

    if(!file_exists($file_name[0].".out")){
        $new = fopen($file_name[0].".out", "w");
        fclose($new);
    }

    if(!file_exists($file_name[0].".rc")){
        $new = fopen($file_name[0].".rc", "w");
        fprintf($new, "0");
        fclose($new);
    }

    return $file_name[0];
}

// Function for comparing tester output with example
function compare_output($exit_code, $path, $args){
    $new = fopen($path.".rc", "r");
    $example_exit_code = fgets($new);

    if($example_exit_code != $exit_code){
        fprintf(STDOUT, "<li><span style=\"background-color: #CB0000\">WRONG EXIT CODE</span> in: %s.src <br> &emsp; &emsp; 
        <span style=\"background-color: #CB0000\">  EXIT_CODE: %d </span> &emsp; &emsp; 
        <span style=\"background-color: #00C000\">SHOULD BE: %d </span>  </li>\n", $path, $exit_code, $example_exit_code);
        array_push($args->wrong_tests_list, $path." <span style=\"background-color: #CB0000\"> WRONG EXIT CODE</span> ".$exit_code);
        $args->failed_tests++;
    }
    else{
        if($example_exit_code != 0){
            fprintf(STDOUT, "<li><span style=\"background-color: #00C000\">TEST PASSED</span>: %s.src </li>\n", $path);
            $args->passed_tests++;
        }
        else if($args->parse_only){
            exec("java -jar \"$args->jexam_path/jexamxml.jar\" \"$path.parsed.out\" \"$path.out\" \"$path.dif\" /pub/courses/ipp/jexamxml/options", $trash, $jexam_exit_code);
            if($jexam_exit_code == 0){
                fprintf(STDOUT, "<li><span style=\"background-color: #00C000\">TEST PASSED</span>: %s.src </li>\n", $path);
                $args->passed_tests++;
            }
            else{
                fprintf(STDOUT, "<li><span style=\"background-color: #CB0000\">WRONG XML OUTPUT</span> in: %s.src</li>\n", $path);
                array_push($args->wrong_tests_list, $path." <span style=\"background-color: #CB0000\"> WRONG XML OUTPUT</span>");
                $args->failed_tests++;
            }

        }
        else{
            exec("diff -q \"$path.int.out\" \"$path.out\"", $trash, $diff_exit_code);
            if($diff_exit_code == 0){
                fprintf(STDOUT, "<li><span style=\"background-color: #00C000\">TEST PASSED</span>: %s.src </li>\n", $path);
                $args->passed_tests++;
            }
            else{
                fprintf(STDOUT, "<li><span style=\"background-color: #CB0000\">WRONG OUTPUT</span> in: %s.src </li>\n", $path);
                array_push($args->wrong_tests_list, $path." <span style=\"background-color: #CB0000\"> WRONG OUTPUT</span>");
                $args->failed_tests++;
            }
        }
    }
    fclose($new);
}

// Function for cleaning up files created while testing
function clean_up($dir){
    $file_list = scandir($dir);
    foreach($file_list as $file){
        if(preg_match("/(parsed.out|.dif|int.out)$/", $file)){
            unlink($dir."/".$file);
        }
    }
}

// Function for finding files and directories in given directory
function go_through_dir($dir, $args){
    $directories = array();
    $files = array();
    foreach(scandir($dir) as $file){
        if(($file != '.') && ($file != '..')){
            if(is_dir($dir.'/'.$file)){
                $directories[] = $file;
            }
            else{
                $files[] = $file;
            }
        }
    }

    if($args->recursive){
        foreach($directories as $directory){
            $path = $dir."/".$directory;
            go_through_dir($path, $args);
            fprintf(STDOUT, "<hr size=\"3\" color=\"#D50000\" align=\"left\" noshade>");
        }
    }

    foreach($files as $file){
        $path = $dir."/".$file;

        if($args->parse_only && !$args->int_only && preg_match("/(.src)$/", $file)){
            $path = check_for_files($file, $dir);
            exec("php8.1 \"$args->parse_script\" <\"$path.src\" >\"$path.parsed.out\"", $trash, $parse_exit_code);
            compare_output($parse_exit_code, $path, $args);
        }
        else if($args->int_only && !$args->parse_only && preg_match("/(.src)$/", $file)){
            $path = check_for_files($file, $dir);
            exec("python3.8 \"$args->int_script\" --source=\"$path.src\" --input=\"$path.in\" >\"$path.int.out\"", $trash, $int_exit_code);
            compare_output($int_exit_code, $path, $args);
        }
        else if(!$args->int_only && !$args->parse_only && preg_match("/(.src)$/", $file)){
            $path = check_for_files($file, $dir);
            exec("php8.1 \"$args->parse_script\" <\"$path.src\" >\"$path.parsed.out\"", $trash, $parse_exit_code);
            exec("python3.8 \"$args->int_script\" --source=\"$path.parsed.out\" --input=\"$path.in\" >\"$path.int.out\"", $trash, $int_exit_code);
            compare_output($int_exit_code, $path, $args);
        }
    }

    if(!$args->noclean){
        clean_up($dir);
    }
}

// Function for printing out WRONG TESTS
function print_wrong_tests($args){
    fprintf(STDOUT, "<h2>WRONG TESTS:</h2><ul>");
    foreach($args->wrong_tests_list as $test){
        fprintf(STDOUT, "<li>%s</li>", $test);
    }
    fprintf(STDOUT, "</ul>");
}

// MAIN //////////////////////////////////////////////////////////    

$args = new Args($argc);
$args->parse_args($argv);
$args->check_files();
$colour = "#00E400";

fprintf(STDOUT, "<h2>Given parametres:</h2>");
fprintf(STDOUT, "<b>%s </b>", $args->args_list);
fprintf(STDOUT, "<h2>Testing directory:</h2><ul><li>%s</li></ul>", $args->directory);
fprintf(STDOUT, "<h2>TESTS SUMMARY:</h2><ul>");
go_through_dir($args->directory, $args);
fprintf(STDOUT, "</ul>");
if($args->failed_tests != 0){
    $colour = "#D50000";
}

fprintf(STDOUT, "<p><font size=\"+2\"><br> Passed  <span style=\"background-color: %s\"><b>%d</b> tests out of <b>%d</b></span></font></p> \n", $colour, $args->passed_tests, $args->passed_tests + $args->failed_tests);

if($args->failed_tests != 0){
    print_wrong_tests($args);
}

?>
</body>
</html>