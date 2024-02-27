# Author: Dominik Pop
# Login:  xpopdo00
# Email:  xpopdo00@stud.fit.vutbr.cz
# Date:   3.3.2022
# VUT FIT, 2 BIT, IPP_interpret


# IMPORTS:
import re
import sys
import xml.etree.ElementTree as ET
from collections import deque


# CLASSES
class Args:
    """Class for parsing arguments."""
    def __init__(self):
        """Class constructor."""
        self.source = sys.stdin
        self.input = None

    def help(self):
        """Prints help instructions to STDOUT."""
        print("Usage: ")
        print("\t python3 interpret.py <arguments>\n")
        print("Possible arguments: ")
        print("\t--help")
        print("\t\tPrints how to use this.")
        print("\t--source=file")
        print("\t\tSource file in XML format.")
        print("\t--input=file")
        print("\t\tInput file for READ instruction.\n")
        print("Description:")
        print("\tProgram takes XML source file and executes instructions in it to STDOUT.")
        exit(0)

    def setter(self, arg):
        """Sets input arguments of program."""
        if re.findall('(=)', arg):
            parsed_arg = arg.split('=')
            arg = parsed_arg[0]

        if arg == "--help":
            self.help()
        elif arg == "--source":
            self.source = parsed_arg[1]
        elif arg == "--input":
            self.input = parsed_arg[1]
        else:
            print("Error, wrong input argumets!")
            exit(10)

    def parse_args(self, argv):
        """Starts parsing and calls setter."""
        for arg in argv[1::]:
            self.setter(arg)

    def check_args(self):
        """Check input arguments validity."""
        if self.source is None and self.input is None:
            print("Wrong format of input arguments!")
            print("Source and input cannot be STDIN in the same time!")
            exit(10)


class Instruction:
    def __init__(self, order, opcode):
        """Class constructor."""
        self.order = order
        self.opcode = opcode
        self.args = []

    def add_arg(self, arg):
        """Adds argument to instruction."""
        self.args.append(arg)

    def get_order(self):
        """Returns order of instruction."""
        return self.order

    def get_opcode(self):
        """Returns opcode of instruction."""
        return self.opcode


class Argument:
    def __init__(self, type, value):
        """Class constructor."""
        self.type = type
        self.value = value


class Label:
    def __init__(self, name, number):
        """Class constructor."""
        self.name = name
        self.ins_num = number


class Variable:
    def __init__(self, name):
        """Class constructor."""
        self.name = name
        self.val = None
        self.type = None

    def set_val_type(self, value, type):
        """Sets value and type of instruction."""
        self.val = value
        self.type = type


class Frame:
    def __init__(self):
        """Class constructor."""
        self.dictionary = []

    def add_variable(self, var):
        """Adds variable to frame."""
        self.dictionary.append(var)

    def find_variable(self, name):
        """Returns reference to variable if it is found, None if not."""
        for var in self.dictionary:
            if var.name == name:
                return var
        return None


class Error:
    error_messages = {
        10: 'Missing parametre of script or using wrong combination of parametres.',
        11: 'Error while opening input files.',
        12: 'Error while opening output files.',
        99: 'Internal error.',

        31: 'Wrong XML format in input file.',
        32: 'Error in lexical or syntactical analyse of text elements and attributes in XML input file.'
    }

    def __init__(self):
        pass

    def exit_with_error(self, error_number, msg=None):
        """Prints error message to stderr and exits with error_number"""
        if msg:
            print(msg, file=sys.stderr)
        else:
            print(self.error_messages[error_number], file=sys.stderr)
        exit(error_number)


# GLOBAL VARIABLES
# FRAMES
global_frame = Frame()
local_frame = None
temporary_frame = None
e = Error()

# STACKS
frame_stack = deque()
call_stack = deque()
data_stack = deque()
data_type_stack = deque()


# FUNCTIONS
def get_type(opcode, num):
    """Returns list of types that can be used for arguments of certain instructions."""
    types = None
    if num == 0:
        pass
    elif num == 1:
        if re.match('^(DEFVAR|POPS)$', opcode):
            types = ['var']
        elif re.match('^(PUSHS|WRITE|EXIT|DPRINT)$', opcode):
            types = ['(int|string|bool|nil|var)']
        elif re.match('^(EXIT)$', opcode):
            types = ['(var|int)']
        elif re.match('^(CALL|LABEL|JUMP)$', opcode):
            types = ['(var|label)']
    elif num == 2:
        if re.match('^(MOVE|TYPE)$', opcode):
            types = ['var', '(int|string|bool|nil|var)']
        elif re.match('^(INT2CHAR)$', opcode):
            types = ['var', '(var|int)']
        elif re.match('^(STRLEN)$', opcode):
            types = ['var', '(var|string)']
        elif re.match('^(NOT)$', opcode):
            types = ['var', '(var|bool)']
        elif re.match('^(READ)$', opcode):
            types = ['var', '(var|type)']
    elif num == 3:
        if re.match('^(EQ)$', opcode):
            types = ['var', '(int|string|bool|nil|var)', '(int|string|bool|nil|var)']
        elif re.match('^(AND|OR)$', opcode):
            types = ['var', '(var|bool)', '(var|bool)']
        elif re.match('^(ADD|SUB|IDIV|MUL)$', opcode):
            types = ['var', '(var|int)', '(var|int)']
        elif re.match('^(GT|LT)$', opcode):
            types = ['var', '(int|string|bool|var)', '(int|string|bool|var)']
        elif re.match('^(STRI2INT|GETCHAR)$', opcode):
            types = ['var', '(var|string)', '(var|int)']
        elif re.match('^(SETCHAR)$', opcode):
            types = ['var', '(var|int)', '(var|string)']
        elif re.match('^(CONCAT)$', opcode):
            types = ['var', '(var|string)', '(var|string)']
        elif re.match('^(JUMPIFEQ|JUMPIFNEQ)$', opcode):
            types = ['label', '(int|string|bool|nil|var)', '(int|string|bool|nil|var)']

    return types


def check_head(root):
    """Checks head of the source XML file."""
    wrong_head = False
    if 'program' not in root.tag:
        e.exit_with_error(32)

    for attrib in root.attrib:
        if attrib not in ['language', 'name', 'description']:
            e.exit_with_error(32)

    if 'language' not in root.attrib:
        e.exit_with_error(32)

    if 'IPPcode22' not in root.attrib.values():
        e.exit_with_error(32)

def check_instruction(instruction, valid_ins):
    """Checks instruction validity."""
    """In case of valid instruction returns reference to instruction object."""
    # Checking tag
    if 'instruction' != instruction.tag:
        e.exit_with_error(32)

    # Checking attributes
    if 'order' not in instruction.attrib:
        e.exit_with_error(32)
    if 'opcode' not in instruction.attrib:
        e.exit_with_error(32)

    # Checking 'order'
    if not re.match('^[1-9][0-9]*$', instruction.attrib['order']):
        e.exit_with_error(32)
    if instruction.attrib['order'] is None:
        e.exit_with_error(32)

    # Checking 'opcode' and getting valid number of arguments
    instruction.attrib['opcode'] = instruction.attrib['opcode'].upper()
    val_num_args = -1
    i = 0
    for dic in valid_ins:
        if instruction.attrib['opcode'] in dic:
            val_num_args = i
            break
        i += 1

    if val_num_args == -1:
        e.exit_with_error(32)

    # Creating new instruction object
    new_ins = Instruction(int(instruction.attrib['order']), instruction.attrib['opcode'])

    # Checking arguments of instruction -> XML format + type
    num_args = 0
    type_list = ['var', 'type', 'bool', 'label', 'int', 'string', 'nil']
    type = get_type(instruction.attrib['opcode'], val_num_args) # List of types for specific instruction

    # Getting arguments order
    arg_dict = dict()
    for arg in instruction:
        tag = re.findall(r'\d+', arg.tag)
        if len(tag) > 0:
            num = int(tag[0]) - 1
            arg_dict[arg] = num

    # Checking number of arguments
    if len(arg_dict) != val_num_args:
        e.exit_with_error(32)

    # Ordering arguments
    arg_list = list()
    for i in range(val_num_args):
        for arg in arg_dict:
            if arg_dict[arg] == i:
                arg_list.append(arg)

    # Processing arguments
    for arg in arg_list:
        new_arg = check_arg(arg, type_list, type[num_args], instruction.attrib['opcode']) # Checking and creating argument
        new_ins.add_arg(new_arg) # Adding argument to instruction
        num_args += 1

    if num_args != val_num_args:
        e.exit_with_error(32)

    return new_ins


def check_arg(arg, type_list, type_ins, name):
    """Checks argument validity."""
    """In case of success returns reference to argument object."""
    # Checking XML format
    if not re.match('^(arg)[1-9][0-9]*$', arg.tag):
        e.exit_with_error(32)

    if 'type' not in arg.attrib:
        e.exit_with_error(32)

    # Checking type of argument
    if arg.attrib['type'] not in type_list: # Checking if type is valid
        e.exit_with_error(32)
    if arg.attrib['type'] not in type_ins: # Checking if type is valid for specific instruction
        err_msg = "Wrong type of argument for " + name + "!"
        e.exit_with_error(53, err_msg)
    if not check_arg_value(arg.text, arg.attrib['type']):
        e.exit_with_error(32)

    if arg.attrib['type'] == 'string' and arg.text is None:
        arg.text = ''
    new_argument = Argument(arg.attrib['type'], arg.text)
    return new_argument

# Jeste se podivat na ty regexy
def check_arg_value(value, type):
    """Checks validity of argument value."""
    """In case of success returns True."""
    if type == 'int':
        if not re.match('^([+-]?[1-9][0-9]*|[+-]?[0-9])$', value):
            return False
    elif type == 'string':
        pass
    elif type == 'bool':
        if not re.match('^(true|false)$', value):
            return False
    elif type == 'label':
        if not re.match('^([a-zA-Z]|!|\?|%|\*|\$|_|-)(!|\?|%|\*|\$|_|-|[\w])*$', value):
            return False
    elif type == 'var':
        if not re.match('^(TF|LF|GF)@([a-zA-Z]|!|\?|%|\*|\$|_|-)(!|\?|%|\*|\$|_|-|[\w])*$', value):
            return False
    elif type == 'nil':
        if not re.match('^(nil)$', value):
            return False

    return True


def does_label_exist(list, name):
    """Returns reference to label object if it exists, None if it doesn't."""
    if len(list) == 0:
        return None
    for label in list:
        if label.name == name:
            return label

    return None


def does_frame_exist(frame):
    """Returns True if frame it exists, False if it doesn't."""
    if frame is None:
        return False
    else:
        return True


def does_var_exist(var):
    """Returns reference to variable object if it exists, None if it doesn't."""
    frame_type, separator, var_name = var.rpartition('@')
    result = None
    if frame_type == 'GF':
        result = global_frame.find_variable(var_name)
    elif frame_type == 'TF':
        if does_frame_exist(temporary_frame):
            result = temporary_frame.find_variable(var_name)
        else:
            e.exit_with_error(55, "Temporary frame does not exist!")
    else:
        if does_frame_exist(local_frame):
            result = local_frame.find_variable(var_name)
        else:
            e.exit_with_error(55, "Local frame does not exist!")

    return result


def convert_escape_seq(string):
    """Function for converting escape sequences to characters"""
    string = re.sub(r'\\([0-9]{3})', lambda x: chr(int(x.group(1))), string)
    return string


def get_value_type(type, value):
    """Returns value and type of variable/constant."""
    result_value = None
    result_type = None
    if type == 'var':
        var = does_var_exist(value)
        if var is None:
            e.exit_with_error(54, "Variable does not exist!")
        else:
            result_value = var.val
            result_type = var.type
            # return var.val, var.type
    else:
        result_value = value
        result_type = type
        # return value, type

    if result_type == 'string':
        result_value = convert_escape_seq(result_value)

    return result_value, result_type


def both_int(type1, type2):
    """Returns True if both types are intiger"""
    if type1 == 'int' and type2 == 'int':
        return True
    else:
        return False


# MAIN ###################################
# INSTRUCTION LISTS
no_arg = ['CREATEFRAME', 'PUSHFRAME', 'POPFRAME', 'RETURN', 'BREAK']
one_arg = ['DEFVAR', 'POPS', 'PUSHS', 'WRITE', 'EXIT', 'DPRINT', 'CALL', 'LABEL', 'JUMP']
two_arg = ['MOVE', 'INT2CHAR', 'STRLEN', 'TYPE', 'NOT', 'READ']
three_arg = ['ADD', 'SUB', 'IDIV', 'MUL', 'AND', 'OR', 'GT', 'EQ', 'LT', 'CONCAT', 'GETCHAR', 'SETCHAR', 'STRI2INT', 'JUMPIFEQ', 'JUMPIFNEQ']
valid_ins = [no_arg, one_arg, two_arg, three_arg]

# Getting input arguments
args = Args()
args.parse_args(sys.argv)
args.check_args()


# Reading XML file
try:
    tree = ET.parse(args.source)
    root = tree.getroot()
except FileNotFoundError as nf:
    e.exit_with_error(11)
except Exception as ex:
    e.exit_with_error(31)

# Checking XML file
check_head(root)
instruction_list = []
label_list = []

# Checking instructions and arguments, detecting labels
num_ins = 0
for instruction in root:
    num_ins += 1
    # Checking instruction and adding it to list
    instruction_list.append(check_instruction(instruction, valid_ins));
    if 'LABEL' in instruction.attrib['opcode']:
        label = Label(instruction[0].text, num_ins)
        duplicate = does_label_exist(label_list, label.name)
        if duplicate is None:
            label_list.append(label)
        else:
            e.exit_with_error(52, "Label does not exist!")

# Sorting list by order of instructions
instruction_list.sort(key=Instruction.get_order)

# Checking if there are no duplicate orders
order_list = [obj.get_order() for obj in instruction_list]
if len(order_list) != len(set(order_list)):
    e.exit_with_error(32)

# MAIN CYCLE
index = 0
read_file = None
while index < len(instruction_list):
    instruction = instruction_list[index]
    opcode = instruction.get_opcode()

    # Deciding instruction
    if 'MOVE' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable in MOVE does not exist!")
        source, source_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        if source is None:
            e.exit_with_error(56, "Invalid source value in MOVE!")
        destination.val = source
        destination.type = source_type
    elif 'CREATEFRAME' == opcode:
        temporary_frame = Frame()
    elif 'PUSHFRAME' == opcode:
        if not does_frame_exist(temporary_frame):
            e.exit_with_error(55, "Temporary frame does not exist!")
        else:
            frame_stack.append(temporary_frame)
            local_frame = frame_stack[-1]
            temporary_frame = None
    elif 'POPFRAME' == opcode:
        if not does_frame_exist(local_frame):
            e.exit_with_error(55, "Local frame does not exist!")
        else:
            temporary_frame = frame_stack.pop()
            if len(frame_stack) != 0:
                local_frame = frame_stack[-1]
            else:
                local_frame = None
    elif 'DEFVAR' == opcode:
        if does_var_exist(instruction.args[0].value) is not None:
            e.exit_with_error(52, "Variable in DEFVAR already exists!")
        else:
            frame_type, separator, var_name = instruction.args[0].value.rpartition('@')
            var = Variable(var_name)
            if frame_type == 'GF':
                global_frame.add_variable(var)
            elif frame_type == 'TF':
                temporary_frame.add_variable(var)
            else:
                local_frame.add_variable(var)
    elif 'CALL' == opcode:
        # index += 1
        call_stack.append(index)
        label = does_label_exist(label_list, instruction.args[0].value)
        if label is None:
            e.exit_with_error(52, "Label in CALL does not exist!")
        index = label.ins_num - 1
    elif 'RETURN' == opcode:
        if len(call_stack) == 0:
            e.exit_with_error(56, "Missing value in call_stack of RETURN!")
        index = call_stack.pop()
    elif 'PUSHS' == opcode:
        value, value_type = get_value_type(instruction.args[0].type, instruction.args[0].value)
        if value is None:
            e.exit_with_error(56, "Missing value to be pushed in PUSHS")
        data_stack.append(value)
        data_type_stack.append(value_type)
    elif 'POPS' == opcode:
        if len(data_stack) == 0:
            e.exit_with_error(56, "Missing value to be poped in POPS")
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for POPS does not exist!")
        destination.val = data_stack.pop()
        destination.type = data_type_stack.pop()
    elif 'ADD' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for ADD does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for ADD!")
        if not both_int(left_type, right_type):
            e.exit_with_error(53, "Wrong types of operands for ADD!")
        destination.val = str(int(left) + int(right))
        destination.type = left_type
    elif 'SUB' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for SUB does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for SUB!")
        if not both_int(left_type, right_type):
            e.exit_with_error(53, "Wrong types of operands for SUB!")
        destination.val = str(int(left) - int(right))
        destination.type = left_type
    elif 'MUL' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for MUL does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for MUL!")
        if not both_int(left_type, right_type):
            e.exit_with_error(53, "Wrong types of operands for MUL!")
        destination.val = str(int(left) * int(right))
        destination.type = left_type
    elif 'IDIV' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for IDIV does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for IDIV!")
        if not both_int(left_type, right_type):
            e.exit_with_error(53, "Wrong types of operands for IDIV!")
        if int(right) == 0:
            e.exit_with_error(57, "Diversion by zero in IDIV!")
        destination.val = str(int(left) // int(right))
        destination.type = left_type
    elif 'LT' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for LT does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for LT!")
        if right_type != left_type:
            e.exit_with_error(53, "Wrong types of operands for LT!")
        if left_type == 'int':
            if int(left) < int(right):
                destination.val = 'true'
            else:
                destination.val = 'false'
        elif left_type == 'string':
            if left < right:
                destination.val = 'true'
            else:
                destination.val = 'false'
        elif left_type == 'bool':
            if left == 'false' and right == 'true':
                destination.val = 'true'
            else:
                destination.val = 'false'
        destination.type = 'bool'
    elif 'GT' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for GT does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for GT!")
        if right_type != left_type:
            e.exit_with_error(53, "Wrong types of operands for GT!")
        if left_type == 'int':
            if int(left) > int(right):
                destination.val = 'true'
            else:
                destination.val = 'false'
        elif left_type == 'string':
            if left > right:
                destination.val = 'true'
            else:
                destination.val = 'false'
        elif left_type == 'bool':
            if left == 'true' and right == 'false':
                destination.val = 'true'
            else:
                destination.val = 'false'
        destination.type = 'bool'
    elif 'EQ' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for EQ does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for EQ!")
        if right_type != left_type:
            if right_type != 'nil' and left_type != 'nil':
                e.exit_with_error(53, "Wrong types of operands for EQ!")
        if left_type == 'int' and right_type == 'int':
            if int(left) == int(right):
                destination.val = 'true'
            else:
                destination.val = 'false'
        else:
            if left == right:
                destination.val = 'true'
            else:
                destination.val = 'false'
        destination.type = 'bool'
    elif 'AND' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for AND does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for AND!")
        if left_type != 'bool' and right_type != 'bool':
            e.exit_with_error(53, "Wrong types of operands for AND!")
        if left == 'true' and right == 'true':
            destination.val = 'true'
        else:
            destination.val = 'false'
        destination.type = 'bool'
    elif 'OR' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for OR does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for OR!")
        if left_type != 'bool' and right_type != 'bool':
            e.exit_with_error(53, "Wrong types of operands for OR!")
        if left == 'false' and right == 'false':
            destination.val = 'false'
        else:
            destination.val = 'true'
        destination.type = 'bool'
    elif 'NOT' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for NOT does not exist!")
        value, value_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        if value is None:
            e.exit_with_error(56, "Missing value for NOT!")
        if value_type != 'bool':
            e.exit_with_error(53, "Wrong type of operand for NOT!")
        if value == 'true':
            destination.val = 'false'
        else:
            destination.val = 'true'
        destination.type = 'bool'
    elif 'INT2CHAR' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for INT2CHAR does not exist!")
        value, value_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        if value is None:
            e.exit_with_error(56, "Missing value for INT2CHAR!")
        if value_type != 'int':
            e.exit_with_error(53, "Wrong type of operand for INT2CHAR!")
        try:
            destination.type = 'string'
            destination.val = chr(int(value))
        except ValueError as ex:
            e.exit_with_error(58, "Wrong ipnut value (out of range) for INT2CHAR")
    elif 'STRI2INT' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for STRI2INT does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for STRI2INT!")
        if int(right) < 0:
            e.exit_with_error(58, "Index out of range for STRI2INT!")
        try:
            destination.val = str(ord(left[int(right)]))
            destination.type = 'int'
        except IndexError as ix:
            e.exit_with_error(58, "Index out of range for STRI2INT!")
    elif 'READ' == opcode:
        if args.input is None:
            try:
                input_value = input()
            except:
                input_value = ''
        else:
            if read_file is None:
                read_file = open(args.input, 'r')
            input_value = read_file.readline()

        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for READ does not exist!")
        value, value_type = get_value_type(instruction.args[1].type, instruction.args[1].value)

        wrong_type = False
        if input_value is None or input_value == '':
            wrong_type = True
        input_value = input_value.strip()
        if value == 'int':
            if re.match('^[+-]?[0-9]+$', input_value):
                destination.val = str(int(input_value))
                destination.type = 'int'
            else:
                wrong_type = True
        elif value == 'string':
            if re.match(r'(\S)*', input_value):
                destination.val = input_value
                destination.type = 'string'
            else:
                wrong_type = True
        elif value == 'bool':
            input_value = input_value.lower()
            if input_value == 'true':
                destination.val = input_value
                destination.type = 'bool'
            else:
                destination.val = 'false'
                destination.type = 'bool'

        if wrong_type is True:
            destination.val = 'nil'
            destination.type = 'nil'
    elif 'WRITE' == opcode:
        value, value_type = get_value_type(instruction.args[0].type, instruction.args[0].value)
        if value is None:
            e.exit_with_error(56, "Missing value for WRITE!")
        if value_type == 'nil':
            print('', end='')
        else:
            print(value, end='')
    elif 'CONCAT' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for CONCAT does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)

        if left is None and left_type == 'string':
            left = ''
        elif left is None:
            e.exit_with_error(56, "Missing left value for CONCAT!")

        if right is None and right_type == 'string':
            right = ''
        elif right is None:
            e.exit_with_error(56, "Missing right value for CONCAT!")

        if left_type != 'string' and right_type != 'string':
            e.exit_with_error(53, "Wrong types of operands for CONCAT!")
        destination.val = left + right
        destination.type = left_type
    elif 'STRLEN' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for STRLEN does not exist!")
        source, source_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        if source is None:
            e.exit_with_error(56, "Missing value for STRLEN!")
        if source_type != 'string':
            e.exit_with_error(53, "Wrong type of operand for STRLEN!")
        destination.val = str(len(source))
        destination.type = 'int'
    elif 'GETCHAR' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for GETCHAR does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for GETCHAR!")
        try:
            if int(right) < 0:
                e.exit_with_error(58, "Index out of range for GETCHAR!")
            destination.val = left[int(right)]
        except IndexError as ix:
            e.exit_with_error(58, "Index out of range for GETCHAR!")
        destination.type = left_type
    elif 'SETCHAR' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for SETCHAR does not exist!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None or destination.val is None:
            e.exit_with_error(56, "Missing value for SETCHAR!")
        if destination.type != 'string':
            e.exit_with_error(53, "Wrong type of operand for SETCHAR!")
        if len(destination.val) > int(left) >= 0 and right != '':
            destination.val = destination.val[:int(left)] + right[0] + destination.val[int(left) + 1:]
        else:
            e.exit_with_error(58, "Index out of range for SETCHAR!")
        destination.type = 'string'
    elif 'TYPE' == opcode:
        destination = does_var_exist(instruction.args[0].value)
        if destination is None:
            e.exit_with_error(54, "Destination variable for TYPE does not exist!")
        value, value_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        if value_type is None:
            value_type = ''
        destination.type = 'string'
        destination.val = value_type
    elif 'LABEL' == opcode:
        pass
    elif 'JUMP' == opcode:
        label = does_label_exist(label_list, instruction_list[index].args[0].value)
        if label is None:
            e.exit_with_error(52, "Label does not exist for JUMP!")
        index = label.ins_num - 1
    elif 'JUMPIFEQ' == opcode:
        label = does_label_exist(label_list, instruction_list[index].args[0].value)
        if label is None:
            e.exit_with_error(52, "Label does not exist for JUMPIFEQ!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for JUMPIFEQ!")
        if left_type == right_type or left_type == 'nil' or right_type == 'nil':
            if left == right:
                index = label.ins_num - 1
        else:
            e.exit_with_error(53, "Wrong types of operands for JUMPIFEQ!")
    elif 'JUMPIFNEQ' == opcode:
        label = does_label_exist(label_list, instruction_list[index].args[0].value)
        if label is None:
            e.exit_with_error(52, "Label does not exist for JUMPIFNEQ!")
        left, left_type = get_value_type(instruction.args[1].type, instruction.args[1].value)
        right, right_type = get_value_type(instruction.args[2].type, instruction.args[2].value)
        if left is None or right is None:
            e.exit_with_error(56, "Missing value for JUMPIFNEQ!")
        if left_type == right_type or left_type == 'nil' or right_type == 'nil':
            if left != right:
                index = label.ins_num - 1
        else:
            e.exit_with_error(53, "Wrong types of operands for JUMPIFNEQ!")
    elif 'EXIT' == opcode:
        return_code, return_code_type = get_value_type(instruction.args[0].type, instruction.args[0].value)
        if return_code is None:
            e.exit_with_error(56, "Missing value for EXIT!")
        if return_code_type != 'int':
            e.exit_with_error(53, "Wrong type of operand for EXIT!")
        if 0 <= int(return_code) <= 49:
            exit(int(return_code))
        else:
            e.exit_with_error(57, "Exit value out of range for EXIT!")
    elif 'DPRINT' == opcode:
        value, value_type = get_value_type(instruction.args[0].type, instruction.args[0].value)
        if value is None:
            e.exit_with_error(56, "Missing value for DPRINT!")
        sys.stderr.write(value)
    elif 'BREAK' == opcode:
        sys.stderr.write("Pozice v kódu:\n")
        sys.stderr.write("\t" + (instruction.order+1) + "\n")
        sys.stderr.write("Obsah rámců:\n")
        sys.stderr.write("\tGlobální:" + global_frame + "\n")
        sys.stderr.write("\tLokální:" + local_frame + "\n")
        sys.stderr.write("\tDočasný:" + temporary_frame + "\n")
        sys.stderr.write("Počet vykonaných instrukcí:\n")
        sys.stderr.write("\t" + (instruction.order-1) + "\n")
    index += 1

exit(0)
