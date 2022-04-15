from brownie import network, config, accounts
from web3 import Web3

FORKED_LOCAL_ENVIRONMENT = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local", "mainnet-fork"]

DECIMALS = 8
INITIAL_VALUE = 200000000000


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENT
    ):
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])
