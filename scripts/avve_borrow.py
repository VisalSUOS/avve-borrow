from cmath import acos
from operator import le
import re
from sqlite3 import adapt, converters
from webbrowser import get
from brownie import config, network, interface
from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth
from web3 import Web3

# 0.1
amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]

    if network.show_active() in ["mainnet-fork"]:
        get_weth()

    # ABI
    # Address
    lending_pool = get_lending_pool()
    # Approve sending out ERC20 tokens
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    print("Depoisting.....")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited!")
    # ...how much i can borrow?
    borrowable_eth, total_debt = get_borrowable_data(
        lending_pool=lending_pool, account=account
    )
    print("Let's borrow")
    # DAI in terms of ETH
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    # borrowable_eth -> borrowable_dai * 95%
    print(f"We are going to borrow {amount_dai_to_borrow} DAI")
    # start borrow
    borrow_dai(lending_pool, amount_dai_to_borrow, account)
    # repay_all(amount=amount, lending_pool=lending_pool, account=account)


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Rapaied")
    print("We borrowed some DAI")
    print("You just deposited, borrowed and repayed the AVVE, Brownie and Chainlink.")
    get_borrowable_data(lending_pool=lending_pool, account=account)


def borrow_dai(lending_pool, amount_dai_to_borrow, account):
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrow some DAI")
    get_borrowable_data(lending_pool, account)


def get_asset_price(price_feed_address):
    # ABI
    # address
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    lastest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_lateset_price = Web3.fromWei(lastest_price, "ether")
    print(f"The DAI/ETH price is {converted_lateset_price}")
    return float(converted_lateset_price)


def get_borrowable_data(lending_pool, account):
    (
        total_callateral_eth,
        total_debt_eth,
        avaialbe_borrows_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    avaiable_borrow_eth = Web3.fromWei(avaialbe_borrows_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_callateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {avaiable_borrow_eth} worth of ETH.")
    return (float(avaiable_borrow_eth), float(total_debt_eth))


def approve_erc20(amount, spender, erc20_address, account):
    print("Aprroving ERC20 token....")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return tx


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    # ABI
    # Address - Check!
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
