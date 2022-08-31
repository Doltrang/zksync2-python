from abc import ABC

# from eth_utils import apply_formatter_if, apply_formatters_to_dict
from eth_utils import to_checksum_address
from eth_utils.curried import apply_formatter_at_index, hexstr_if_str
from hexbytes import HexBytes
from web3 import Web3
from web3._utils.formatters import integer_to_hex
from web3._utils.method_formatters import (
    ABI_REQUEST_FORMATTERS,
    METHOD_NORMALIZERS,
    PYTHONIC_REQUEST_FORMATTERS,
    combine_formatters,
    STANDARD_NORMALIZERS,
    apply_formatter_if,
    apply_formatters_to_dict,
    is_not_null,
    apply_list_to_array_formatter,
    to_hex_if_integer, to_hexbytes, to_ascii_if_bytes
)

from web3._utils.normalizers import (
    abi_address_to_hex,
    abi_int_to_hex,
    abi_bytes_to_hex,
    abi_bytes_to_bytes
)
from web3._utils.rpc_abi import abi_request_formatters

from web3.eth import Eth
from web3.types import RPCEndpoint

from protocol.core.types import TransactionHash, Limit, L2WithdrawTxHash, From, ContractSourceDebugInfo, BridgeAddresses
from protocol.request.request_types import *
from protocol.response.response_types import *
from eth_typing import Address
from eth_utils.toolz import compose
from web3.method import Method, default_root_munger
from typing import Any, Callable, List


zks_estimate_fee_rpc = RPCEndpoint("zks_estimateFee")
zks_main_contract_rpc = RPCEndpoint("zks_getMainContract")
zks_get_l1_withdraw_tx_rpc = RPCEndpoint("zks_getL1WithdrawalTx")
zks_get_confirmed_tokens_rpc = RPCEndpoint("zks_getConfirmedTokens")
zks_is_token_liquid_rpc = RPCEndpoint("zks_isTokenLiquid")
zks_get_token_price_rpc = RPCEndpoint("zks_getTokenPrice")
zks_l1_chain_id_rpc = RPCEndpoint("zks_L1ChainId")
zks_eth_get_balance_rpc = RPCEndpoint("eth_getBalance")
zks_get_all_account_balances_rpc = RPCEndpoint("zks_getAllAccountBalances")
zks_get_bridge_contracts_rpc = RPCEndpoint("zks_getBridgeContracts")
zks_get_l2_to_l1_msg_proof_prc = RPCEndpoint("zks_getL2ToL1MsgProof")
# eth_gas_price_rpc = RPCEndpoint("eth_gasPrice")
eth_estimate_gas_rpc = RPCEndpoint("eth_estimateGas")

zks_set_contract_debug_info_rpc = RPCEndpoint("zks_setContractDebugInfo")
zks_get_contract_debug_info_rpc = RPCEndpoint("zks_getContractDebugInfo")
zks_get_transaction_trace_rpc = RPCEndpoint("zks_getTransactionTrace")

# AA_PARAMS_FORMATTERS = {
#     "from": abi_address_to_hex,
#     "signature": abi_bytes_to_hex
# }
#
# aa_params_formatter = apply_formatters_to_dict(AA_PARAMS_FORMATTERS)

# EIP712_META_FORMATTERS = {
#     "feeToken": to_checksum_address,
#     "ergsPerPubdata": integer_to_hex,
#     "ergsPerStorage": integer_to_hex,
#     "factoryDeps": apply_formatter_if(is_not_null, apply_list_to_array_formatter(abi_bytes_to_hex)),
#     "aaParams": apply_formatter_if(is_not_null, aa_params_formatter)
# }

PAYMENT_PARAMS = {
    "paymaster": to_checksum_address,
    "paymasterInput": abi_bytes_to_hex
}

payments_params_formatter = apply_formatters_to_dict(PAYMENT_PARAMS)

EIP712_META_FORMATTERS = {
    "ergsPerPubdata": integer_to_hex,
    "customSignature": apply_formatter_if(is_not_null, abi_bytes_to_hex),
    "factoryDeps": apply_formatter_if(is_not_null, apply_list_to_array_formatter(abi_bytes_to_hex)),
    "paymasterParams": apply_formatter_if(is_not_null, payments_params_formatter)
}

meta_formatter = apply_formatters_to_dict(EIP712_META_FORMATTERS)

ZKS_TRANSACTION_PARAMS_FORMATTERS = {
    # 'data': abi_bytes_to_bytes,
    'data': to_ascii_if_bytes,
    'from': to_checksum_address,
    'gas': to_hex_if_integer,
    'gasPrice': to_hex_if_integer,
    'nonce': to_hex_if_integer,
    'to': to_checksum_address,
    'value': to_hex_if_integer,
    'chainId': to_hex_if_integer,
    'transactionType': to_hex_if_integer,
    'eip712Meta': meta_formatter
}

zks_transaction_request_formatter = apply_formatters_to_dict(ZKS_TRANSACTION_PARAMS_FORMATTERS)


ZKSYNC_FORMATTERS: [RPCEndpoint, Callable[..., Any]] = {
    eth_estimate_gas_rpc: apply_formatter_at_index(zks_transaction_request_formatter, 0),
}

# ZKSYNC_ABI_REQUEST_FORMATTERS = abi_request_formatters(STANDARD_NORMALIZERS, ZKSYNC_RPC_ABIS)


def zksync_get_request_formatters(
    method_name: Union[RPCEndpoint, Callable[..., RPCEndpoint]]
) -> Dict[str, Callable[..., Any]]:
    request_formatter_maps = (
        ZKSYNC_FORMATTERS,
        ABI_REQUEST_FORMATTERS,
        # METHOD_NORMALIZERS needs to be after ABI_REQUEST_FORMATTERS
        # so that eth_getLogs's apply_formatter_at_index formatter
        # is applied to the whole address
        # rather than on the first byte of the address
        METHOD_NORMALIZERS,
        PYTHONIC_REQUEST_FORMATTERS,
    )
    formatters = combine_formatters(request_formatter_maps, method_name)
    return compose(*formatters)


class ZkSync(Eth, ABC):
    _zks_estimate_fee: Method[Callable[[Transaction], ZksEstimateFee]] = Method(
        zks_estimate_fee_rpc,
        mungers=[default_root_munger]
    )

    _zks_main_contract: Method[Callable[[], ZksMainContract]] = Method(
        zks_main_contract_rpc,
        mungers=None
    )

    _zks_get_l1_withdraw_tx: Method[Callable[[L2WithdrawTxHash], TransactionHash]] = Method(
        zks_get_l1_withdraw_tx_rpc,
        mungers=[default_root_munger]
    )

    _zks_get_confirmed_tokens: Method[Callable[[From, Limit], ZksTokens]] = Method(
        zks_get_confirmed_tokens_rpc,
        mungers=[default_root_munger]
    )

    _zks_is_token_liquid: Method[Callable[[TokenAddress], ZksIsTokenLiquid]] = Method(
        zks_is_token_liquid_rpc,
        mungers=[default_root_munger]
    )

    _zks_get_token_price: Method[Callable[[TokenAddress], ZksTokenPrice]] = Method(
        zks_get_token_price_rpc,
        mungers=[default_root_munger]
    )

    _zks_l1_chain_id: Method[Callable[[], ZksL1ChainId]] = Method(
        zks_l1_chain_id_rpc,
        mungers=None
    )

    _zks_eth_get_balance: Method[Callable[[Address, Any, TokenAddress], Any]] = Method(
        zks_eth_get_balance_rpc,
        mungers=[default_root_munger]
    )

    _zks_get_all_account_balances: Method[Callable[[Address], ZksAccountBalances]] = Method(
        zks_get_all_account_balances_rpc,
        mungers=[default_root_munger]
    )

    _zks_get_bridge_contracts: Method[Callable[[], ZksBridgeAddresses]] = Method(
        zks_get_bridge_contracts_rpc,
        mungers=[default_root_munger]
    )

    _zks_get_l2_to_l1_msg_proof: Method[Callable[[int, HexStr, str, Optional[int]], ZksMessageProof]] = Method(
        zks_get_l2_to_l1_msg_proof_prc,
        mungers=[default_root_munger]
    )

    # _eth_gas_price: Method[Callable[[TokenAddress], str]] = Method(
    #     eth_gas_price_rpc,
    #     mungers=[default_root_munger]
    # )

    _eth_estimate_gas: Method[Callable[[Transaction], str]] = Method(
        eth_estimate_gas_rpc,
        mungers=[default_root_munger],
        request_formatters=zksync_get_request_formatters
    )

    # TODO: implement it
    _zks_set_contract_debug_info: Method[Callable[[Address,
                                                   ContractSourceDebugInfo],
                                                  ZksSetContractDebugInfoResult]] = Method(
        zks_set_contract_debug_info_rpc,
        mungers=[default_root_munger]
    )
    _zks_get_contract_debug_info: Method[Callable[[Address], ContractSourceDebugInfo]] = Method(
        zks_get_contract_debug_info_rpc,
        mungers=[default_root_munger]
    )

    _zks_get_transaction_trace: Method[Callable[[Address], ZksTransactionTrace]] = Method(
        zks_get_transaction_trace_rpc,
        mungers=[default_root_munger]
    )

    def __init__(self, web3: "Web3"):
        super(ZkSync, self).__init__(web3)

    def zks_estimate_fee(self, transaction: Transaction) -> Fee:
        return self._zks_estimate_fee(transaction)

    def zks_main_contract(self) -> HexStr:
        return self._zks_main_contract()

    def zks_get_l1_withdraw_tx(self, withdraw_hash: L2WithdrawTxHash) -> TransactionHash:
        return self._zks_get_l1_withdraw_tx(withdraw_hash)

    def zks_get_confirmed_tokens(self, offset: From, limit: Limit) -> List[Token]:
        return self._zks_get_confirmed_tokens(offset, limit)

    def zks_is_token_liquid(self, token_address: TokenAddress) -> bool:
        return self._zks_is_token_liquid(token_address)

    def zks_get_token_price(self, token_address: TokenAddress) -> Decimal:
        return self._zks_get_token_price(token_address)

    def zks_l1_chain_id(self) -> int:
        return self._zks_l1_chain_id()

    def eth_get_balance(self, address: Address, default_block, token_address: TokenAddress) -> Any:
        return self._zks_eth_get_balance(address, default_block, token_address)

    def zks_get_all_account_balances(self, addr: Address):
        return self._zks_get_all_account_balances(addr)

    def zks_get_bridge_contracts(self) -> BridgeAddresses:
        response: ZksBridgeAddresses = self._zks_get_bridge_contracts()
        return BridgeAddresses(response["l1EthDefaultBridge"],
                               response["l2EthDefaultBridge"],
                               response["l1Erc20DefaultBridge"],
                               response["l2Erc20DefaultBridge"])

    def zks_get_l2_to_l1_msg_proof(self,
                                   block: int,
                                   sender: HexStr,
                                   message: str,
                                   l2log_pos: Optional[int]) -> ZksMessageProof:
        return self._zks_get_l2_to_l1_msg_proof(block, sender, message, l2log_pos)

    # def eth_gas_price(self, token_address: TokenAddress) -> str:
    #     return self._eth_gas_price(token_address)

    def eth_estimate_gas(self, tx: Transaction) -> str:
        return self._eth_estimate_gas(tx)
