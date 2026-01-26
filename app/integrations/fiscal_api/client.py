# app/integrations/fiscal_api/client.py

import requests
import logging
from config import Config


logger = logging.getLogger(__name__)

class BrasilNFeClient:
    """
    Cliente de baixo nível para a API Brasil NFe.
    Lida com a autenticação via Header 'Token' e comunicação HTTP para todos os serviços fiscais.
    """
    def __init__(self):
        self.base_url = Config.API_FISCAL_BASE_URL.rstrip("/")
        self.token = Config.API_FISCAL_TOKEN

        self.headers = {
            "Token": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


    def _request(self, method, endpoint, payload=None):
        """Método genérico para realizar as chamadas HTTP com tratamento de erro padronizado."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.info(f"BrasilNFe Request: {method} {url}")
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                headers=self.headers,
                timeout=45 # Timeout maior para processos de transmissão
            )
            
            response_data = response.json()
            
            if response.status_code == 200:
                return {"success": True, "data": response_data}
            else:
                logger.error(f"BrasilNFe API Error {response.status_code}: {response.text}")
                return {
                    "success": False, 
                    "error": "api_error", 
                    "status_code": response.status_code,
                    "message": response_data.get("Error") or response_data.get("DsMotivo") or "Erro desconhecido na API"
                }

        except requests.exceptions.RequestException as e:
            logger.exception("Erro de conexão/rede com BrasilNFe")
            return {"success": False, "error": "connection_error", "message": str(e)}

    def transmitir_nota(self, payload: dict):
        """POST /EnviarNotaFiscal - Transmissão de NF-e/NFC-e"""
        return self._request("POST", "EnviarNotaFiscal", payload)

    def pre_visualizar(self, payload: dict):
        """POST /PreVisualizarNotaFiscal - Gera PDF/XML sem valor fiscal"""
        return self._request("POST", "PreVisualizarNotaFiscal", payload)

    def cancelar_nota(self, payload: dict):
        """POST /CancelarNotaFiscal - Evento de cancelamento"""
        return self._request("POST", "CancelarNotaFiscal", payload)

    def carta_correcao(self, payload: dict):
        """POST /EnviarCartaCorrecao - Evento de CC-e"""
        return self._request("POST", "EnviarCartaCorrecao", payload)

    def manifestar_nota(self, payload: dict):
        """POST /ManifestarNotaFiscal - Manifestação do Destinatário"""
        return self._request("POST", "ManifestarNotaFiscal", payload)

    def inutilizar_numeracao(self, payload: dict):
        """POST /InutilizarNumeracao - Inutilização de faixa numérica"""
        return self._request("POST", "InutilizarNumeracao", payload)

# Instância Singleton para exportação
brasil_nfe_client = BrasilNFeClient()