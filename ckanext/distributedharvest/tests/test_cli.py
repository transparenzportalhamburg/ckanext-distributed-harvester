from click.testing import CliRunner
from ckanext.distributedharvest.commands.harvester import start_distributed_gather_consumer,start_distributed_fetch_consumer, run_harvester, purge_queues

def test_errored_start():
  runner = CliRunner()
  result = runner.invoke(run_harvester, ['Peter'])
  assert result.exit_code == 1
  assert result.output == ""
  
def test_start_distributed_gather_consumer():
  pass

def test_start_distributed_fetch_consumer():
  pass
  
def test_run_harvester():
  pass

def test_purge_queues():
  pass