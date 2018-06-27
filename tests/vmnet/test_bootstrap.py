from vmnet.test.base import *
import unittest, time, random
import vmnet, cilantro
from os.path import dirname

cilantro_path = dirname(dirname(cilantro.__path__[0]))
# cilantro_path = cilantro.__path__[0]


def wrap_func(fn, *args, **kwargs):
    def wrapper():
        return fn(*args, **kwargs)
    return wrapper


def run_mn():
    from cilantro.logger import get_logger
    from cilantro import Constants
    from cilantro.nodes import NodeFactory
    import os
    log = get_logger("MASTERNODE FACTORY")

    ip = os.getenv('HOST_IP') #Constants.Testnet.Masternodes[0]['ip']
    sk = Constants.Testnet.Masternodes[0]['sk']

    NodeFactory.run_masternode(ip=ip, signing_key=sk)


def run_witness(slot_num):
    from cilantro.logger import get_logger
    from cilantro import Constants
    from cilantro.nodes import NodeFactory
    import os

    log = get_logger("WITNESS FACTORY")

    w_info = Constants.Testnet.Witnesses[slot_num]
    w_info['ip'] = os.getenv('HOST_IP')

    NodeFactory.run_witness(ip=w_info['ip'], signing_key=w_info['sk'])


def run_delegate(slot_num):
    from cilantro.logger import get_logger
    from cilantro import Constants
    from cilantro.nodes import NodeFactory
    import os

    log = get_logger("DELEGATE FACTORY")

    d_info = Constants.Testnet.Delegates[slot_num]
    d_info['ip'] = os.getenv('HOST_IP')

    log.critical("Building delegate on slot {} with info {}".format(slot_num, d_info))
    
    NodeFactory.run_delegate(ip=d_info['ip'], signing_key=d_info['sk'])


def start_mysqld():
    import os
    os.system('mysqld \
   --skip-grant-tables \
   --skip-innodb \
   --collation-server latin1_bin \
   --default-storage-engine ROCKSDB \
   --default-tmp-storage-engine MyISAM \
   --binlog_format ROW \
   --user=mysql &')


class TestBootstrap(BaseNetworkTestCase):
    testname = 'bootstrap'
    setuptime = 10
    compose_file = '{}/cilantro/tests/vmnet/compose_files/cilantro-bootstrap.yml'.format(cilantro_path)
    local_path = cilantro_path
    docker_dir = '{}/cilantro/tests/vmnet/docker_dir'.format(cilantro_path)
    logdir = '{}/cilantro/logs'.format(cilantro_path)

    NUM_WITNESS = 2
    NUM_DELEGATES = 3

    @vmnet_test
    def test_bootstrap(self):
        # start mysql in all nodes
        for node_name in ['masternode'] + self.groups['witness'] + self.groups['delegate']:
            self.execute_python(node_name, start_mysqld, async=True)
        time.sleep(1)

        # Bootstrap master
        self.execute_python('masternode', run_mn, async=True)

        # Bootstrap witnesses
        for i, nodename in enumerate(self.groups['witness']):
            self.execute_python(nodename, wrap_func(run_witness, i), async=True)

        # Bootstrap delegates
        for i, nodename in enumerate(self.groups['delegate']):
            self.execute_python(nodename, wrap_func(run_delegate, i), async=True)

        input("\n\nEnter any key to terminate")

if __name__ == '__main__':
    unittest.main()
