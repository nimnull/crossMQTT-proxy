import click
import yaml

from bridge.worker import MqttListener

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


@click.command()
@click.option('-c', '--config', type=click.Path(exists=True, readable=True), default="config.yaml", help='Configuration file')
def run(config):
    with open(config) as fp:
        config_data = yaml.load(fp, Loader)

    forwarder = MqttListener(config_data["servers"])
    forwarder.run()
