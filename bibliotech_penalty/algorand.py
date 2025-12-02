# core/algorand.py
import os
from dataclasses import dataclass
from typing import Optional
from algosdk.v2client import algod, indexer
from algosdk import account, mnemonic
from algosdk.future.transaction import PaymentTxn, NoteField, SuggestedParams
from django.conf import settings

@dataclass
class AlgoClients:
    algod: algod.AlgodClient
    indexer: indexer.IndexerClient

def get_clients() -> AlgoClients:
    algod_client = algod.AlgodClient(settings.ALGORAND_ALGOD_TOKEN, settings.ALGORAND_ALGOD_URL)
    indexer_client = indexer.IndexerClient("", settings.ALGORAND_INDEXER_URL)
    return AlgoClients(algod=algod_client, indexer=indexer_client)

def lib_account() -> tuple[str, str]:
    mnemonic_phrase = settings.ALGORAND_LIB_ACCOUNT_MNEMONIC
    if not mnemonic_phrase:
        raise RuntimeError("Falta ALGORAND_LIB_ACCOUNT_MNEMONIC en .env")
    sk = mnemonic.to_private_key(mnemonic_phrase)
    addr = mnemonic.to_public_key(mnemonic_phrase)
    return addr, sk

def microalgos(amount_float: float) -> int:
    # 1 Algo = 1_000_000 microalgos
    return int(round(amount_float * 1_000_000))

def register_loan_onchain(loan) -> Optional[str]:
    """
    Guarda un hash del préstamo en una transacción 0-ALGO con nota.
    Devuelve txid al confirmarse.
    """
    clients = get_clients()
    addr, sk = lib_account()
    params: SuggestedParams = clients.algod.suggested_params()
    # tx 0 ALGO con nota (hash del préstamo)
    note_bytes = bytes(f"LoanHash:{loan.content_hash()}", "utf-8")
    txn = PaymentTxn(sender=addr, sp=params, receiver=addr, amt=0, note=note_bytes)
    signed = txn.sign(sk)
    txid = clients.algod.send_transaction(signed)
    # esperar confirmación simple (polling)
    wait_rounds = 10
    current_round = clients.algod.status()["last-round"]
    for _ in range(wait_rounds):
        pending = clients.algod.pending_transaction_info(txid)
        if pending.get("confirmed-round", 0) > 0:
            return txid
        current_round += 1
        clients.algod.status_after_block(current_round)
    return txid  # si no confirmó aún, devolvemos txid

def pay_fine_onchain(student_wallet: str, amount: float) -> Optional[str]:
    """
    Envía pago de multa desde la cuenta del estudiante hacia la cuenta del biblioteca.
    Nota: en producción el estudiante firmaría desde su dispositivo.
    Aquí simulamos un pago desde la cuenta del biblioteca hacia sí misma para registrar.
    """
    clients = get_clients()
    lib_addr, lib_sk = lib_account()

    params: SuggestedParams = clients.algod.suggested_params()
    note_bytes = bytes(f"FinePayment:{amount}", "utf-8")
    # Por simplicidad: registramos la multa como transferencia 0-ALGO con nota
    txn = PaymentTxn(sender=lib_addr, sp=params, receiver=lib_addr, amt=0, note=note_bytes)
    signed = txn.sign(lib_sk)
    txid = clients.algod.send_transaction(signed)

    current_round = clients.algod.status()["last-round"]
    for _ in range(10):
        pending = clients.algod.pending_transaction_info(txid)
        if pending.get("confirmed-round", 0) > 0:
            return txid
        current_round += 1
        clients.algod.status_after_block(current_round)
    return txid

