from leaflet_client import LeafletFullNodeRpcClient
from typing import List
import models
import sys
import os

client: LeafletFullNodeRpcClient = None

def ensure_client():
    global client
    if client is not None:
        return

    network = os.environ.get("TIBET_NETWORK")
    api_key = os.environ.get()
    url = f"https://kraken.fireacademy.io/{api-key}/leaflet"

    if network == "testnet10":
        url += "-tesntet10/"
    elif network == "mainnet":
        url += "/"
    else:
        print("Unknown TIBET_NETWORK")
        sys.exit(1)

    client = LeafletFullNodeRpcClient(url)


def create_new_pair(asset_id: str, launcher_id: str) -> models.Pair:
    pass


async def sync_router(router: models.Router) -> [models.Router, List[models.Pair]]:
    new_pairs: List[models.Pair] = []
    router_updated = False

    current_router_coin_id = bytes.fromhex(router.current_coin_id)
    router_coin_record = await client.get_coin_record_by_name(router_coin_id)
    if not coin_record.spent:
        return None, []

    while router_coin_record.spent:
        creation_spend = await full_node_client.get_puzzle_and_solution(
            current_router_coin_id,
            router_coin_record.spent_block_index
        )

        _, conditions_dict, __ = conditions_dict_for_solution(
            creation_spend.puzzle_reveal,
            creation_spend.solution,
            INFINITE_COST
        )

        tail_hash = None
        if coin_record.coin.puzzle_hash != SINGLETON_LAUNCHER_HASH:
            tail_hash = [_ for _ in solution_program.as_iter()][-1].as_python()[-1]

        for cwa in conditions_dict[ConditionOpcode.CREATE_COIN]:
            new_puzzle_hash = cwa.vars[0]
            new_amount = cwa.vars[1]

            if new_amount == b"\x01": # CREATE_COIN with amount=1 -> router recreated
                new_router_coin = Coin(current_router_coin_id, new_puzzle_hash, 1)

                current_router_coin_id = new_router_coin.name()
            elif new_amount == b"\x02": # CREATE_COIN with amount=2 -> pair launcher deployed
                assert new_puzzle_hash == SINGLETON_LAUNCHER_HASH
                
                pair_launcher_coin = Coin(creation_spend.coin.name(), new_puzzle_hash, 2)
                pair_launcher_id = pair_launcher_coin.name()
                
                new_pairs.append(create_new_pair(tail_hash.hex(), pair_launcher_id.hex()))
            else:
                print("Someone did something extremely weird with the router - time to call the cops.")
                sys.exit(1)

        coin_record = await full_node_client.get_coin_record_by_name(current_router_coin_id)

    router.current_coin_id = current_router_coin_id.hex()
    return router, new_pairs

async def sync_pair(pair: models.Pair) -> [models.Pair, List[models.Transaction]]:
    print("sync_pair", pair)
    return None, []