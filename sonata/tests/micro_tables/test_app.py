#!/usr/bin/python
from sonata.dataplane_driver.p4_old.p4_dataplane import P4DataPlane
from sonata.dataplane_driver.utils import write_to_file
from sonata.tests.micro_tables.utils import get_sequential_code, get_filter_table
import random, logging, time

BASE_PATH = '/home/vagrant/dev/sonata/tests/micro_tables/results/'

def create_return_logger(PATH):
    # create a logger for the object
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    # create file handler which logs messages
    fh = logging.FileHandler(PATH)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    return logger

def delete_entries_from_table(number_of_entries,table_name,dataplane,JSON_P4_COMPILED,P4_DELTA_COMMANDS, logger):
    start = time.time()
    commands = []
    for i in range(0, number_of_entries):
        CMD = "table_delete %s %s"%(table_name, i)
        commands.append(CMD)

    commands_string = "\n".join(commands)
    # print commands_string
    write_to_file(P4_DELTA_COMMANDS, commands_string)
    dataplane.send_commands(JSON_P4_COMPILED,P4_DELTA_COMMANDS)
    end = time.time()

    logger.info("delete|"+str(number_of_entries) +"|"+str(start)+"|"+str(end))

def add_entries_to_table(number_of_entries, table_name, p4_dataplane_obj, JSON_P4_COMPILED, P4_DELTA_COMMANDS, logger):
    start = time.time()

    commands = []
    for i in range(0, number_of_entries):
        IP = "%d.%d.0.0" % (random.randint(0, 255),random.randint(0, 255))
        CMD = "table_add %s _nop  %s/16 =>"%(table_name, IP)
        commands.append(CMD)

    commands_string = "\n".join(commands)
    # print commands_string
    write_to_file(P4_DELTA_COMMANDS, commands_string)
    p4_dataplane_obj.send_commands(JSON_P4_COMPILED,P4_DELTA_COMMANDS)
    end = time.time()

    logger.info("update|"+str(number_of_entries)+"|"+str(start)+"|"+str(end))

if __name__ == '__main__':

    NUMBER_OF_QUERIES = 1
    MAX_TABLE_ENTRIES = 100000

    target_conf = {
        'compiled_srcs': '/home/vagrant/dev/sonata/tests/micro_tables/compiled_srcs/',
        'json_p4_compiled': 'compiled_test.json',
        'p4_compiled': 'compiled_test.p4',
        'p4c_bm_script': '/home/vagrant/p4c-bmv2/p4c_bm/__main__.py',
        'bmv2_path': '/home/vagrant/bmv2',
        'bmv2_switch_base': '/targets/simple_switch',
        'switch_path': '/simple_switch',
        'cli_path': '/sswitch_CLI',
        'thriftport': 22222,
        'p4_commands': 'commands.txt',
        'p4_delta_commands': 'delta_commands.txt'
    }

    # Code Compilation
    COMPILED_SRCS = target_conf['compiled_srcs']
    JSON_P4_COMPILED = COMPILED_SRCS + target_conf['json_p4_compiled']
    P4_COMPILED = COMPILED_SRCS + target_conf['p4_compiled']
    P4C_BM_SCRIPT = target_conf['p4c_bm_script']

    # Initialization of Switch
    BMV2_PATH = target_conf['bmv2_path']
    BMV2_SWITCH_BASE = BMV2_PATH + target_conf['bmv2_switch_base']

    SWITCH_PATH = BMV2_SWITCH_BASE + target_conf['switch_path']
    CLI_PATH = BMV2_SWITCH_BASE + target_conf['cli_path']
    THRIFTPORT = target_conf['thriftport']

    P4_COMMANDS = COMPILED_SRCS + target_conf['p4_commands']
    P4_DELTA_COMMANDS = COMPILED_SRCS + target_conf['p4_delta_commands']

    # interfaces
    interfaces = {
        'receiver': ['m-veth-1', 'out-veth-1'],
        'sender': ['m-veth-2', 'out-veth-2'],
        'original': ['m-veth-3', 'out-veth-3']
    }

    p4_src,p4_commands,filter_table_name = get_sequential_code(NUMBER_OF_QUERIES, MAX_TABLE_ENTRIES)

    write_to_file(P4_COMPILED, p4_src)

    commands_string = "\n".join(p4_commands)
    write_to_file(P4_COMMANDS, commands_string)

    dataplane = P4DataPlane(interfaces, SWITCH_PATH, CLI_PATH, THRIFTPORT, P4C_BM_SCRIPT)
    dataplane.compile_p4(P4_COMPILED, JSON_P4_COMPILED)

    # initialize dataplane and run the configuration
    dataplane.initialize(JSON_P4_COMPILED, P4_COMMANDS)

    entries = [1, 10, 10, 100, 1000, 10000, 100000]
    logger = create_return_logger(BASE_PATH+"tables.log")

    for entry in entries:
        add_entries_to_table(entry,filter_table_name,dataplane,JSON_P4_COMPILED,P4_DELTA_COMMANDS,logger)
        delete_entries_from_table(entry,filter_table_name,dataplane,JSON_P4_COMPILED,P4_DELTA_COMMANDS,logger)