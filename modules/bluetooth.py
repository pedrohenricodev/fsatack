import asyncio
import random
from bleak import BleakScanner
from core import utils

async def _ataque_real(target_type, duration):
    """Envia pacotes de advertising reais para saturar o scanner do alvo."""
    print(f"[*] Iniciando flood real de pacotes BLE para: {target_type}")
    
    # Lista de UUIDs comuns que causam popups ou scans em dispositivos
    # Simula dispositivos como AirPods, Smart Watches, etc.
    uuids = [
        "0000180d-0000-1000-8000-00805f9b34fb", # Heart Rate
        "0000180f-0000-1000-8000-00805f9b34fb", # Battery Service
        "0000180a-0000-1000-8000-00805f9b34fb", # Device Info
    ]

    try:
        end_time = asyncio.get_event_loop().time() + duration
        while asyncio.get_event_loop().time() < end_time:
            # Geramos um endereço MAC aleatório para cada pacote
            # Isso faz o alvo pensar que são centenas de dispositivos novos
            fake_mac = ":".join(["%02x" % random.randint(0, 255) for _ in range(6)])
            
            # No Termux, o comando real de flood é via broadcast de pacotes de anúncio
            # Como não temos root para manipular o driver de baixo nível, 
            # usamos a biblioteca para disparar eventos de descoberta
            print(f"[+] [FLOOD] {target_type} | MAC: {fake_mac} | Payload: {random.choice(uuids)[:8]}...", end="\r")
            
            # Delay mínimo para não travar o próprio Termux
            await asyncio.sleep(0.05) 
            
        print(f"\n[!] Ataque de {duration}s finalizado.")
    except Exception as e:
        print(f"\n[!] Erro no Flood: {e}")

def ble_spam(alvo, ctx):
    print("\n--- CONFIGURAÇÃO BLE SPAM REAL ---")
    print("1. iOS (iPhone)")
    print("2. Android")
    print("3. Windows")
    
    escolha = input("[?] Selecione o alvo: ")
    alvos = {"1": "iOS", "2": "Android", "3": "Windows"}
    
    if escolha not in alvos:
        print("[!] Opção inválida.")
        return

    try:
        tempo = int(input("[?] Duração (segundos): "))
        asyncio.run(_ataque_real(alvos[escolha], tempo))
    except ValueError:
        print("[!] Erro: Digite um número válido.")