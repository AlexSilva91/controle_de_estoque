# app/integrations/fiscal_api/service.py

from .client import brasil_nfe_client
import logging

logger = logging.getLogger(__name__)

class FiscalService:
    """
    Serviço de alto nível para gerenciar todas as operações fiscais da Brasil NFe.
    Encapsula a lógica de negócio e o mapeamento de dados para a API.
    """

    def emitir_nota(self, dados: dict, ambiente: int = 2) -> dict:
        """
        Transmite uma NF-e ou NFC-e.
        :param dados: Dicionário completo com Serie, Numero, Cliente, Produtos, etc.
        :param ambiente: 1=Produção, 2=Homologação.
        """
        dados["TipoAmbiente"] = str(ambiente)
        return brasil_nfe_client.transmitir_nota(dados)

    def cancelar_nota(self, chave_nf: str, justificativa: str, protocolo: str = None, ambiente: int = 2) -> dict:
        """
        Cancela uma nota fiscal autorizada.
        :param chave_nf: Chave de 44 dígitos.
        :param justificativa: Mínimo 15 caracteres.
        :param protocolo: Protocolo de autorização (opcional se emitido pelo Brasil NFe).
        """
        payload = {
            "ChaveNF": chave_nf,
            "Justificativa": justificativa,
            "TipoAmbiente": ambiente
        }
        if protocolo:
            payload["NumeroProtocolo"] = protocolo
            
        return brasil_nfe_client.cancelar_nota(payload)

    def enviar_carta_correcao(self, chave_nf: str, correcao: str, sequencial: int = 1, ambiente: int = 2) -> dict:
        """
        Envia uma Carta de Correção Eletrônica (CC-e).
        :param correcao: Texto da correção (15 a 1000 caracteres).
        """
        payload = {
            "ChaveNF": chave_nf,
            "Correcao": correcao,
            "NumeroSequencial": sequencial,
            "TipoAmbiente": ambiente
        }
        return brasil_nfe_client.carta_correcao(payload)

    def inutilizar_numeracao(self, modelo: int, serie: int, inicial: int, final: int, justificativa: str, ambiente: int = 2) -> dict:
        """
        Inutiliza uma faixa de numeração que não foi utilizada.
        :param modelo: 55 (NF-e) ou 65 (NFC-e).
        """
        payload = {
            "ModeloDocumento": modelo,
            "Serie": serie,
            "NumeracaoInicial": inicial,
            "NumeracaoFinal": final,
            "Justificativa": justificativa,
            "TipoAmbiente": ambiente
        }
        return brasil_nfe_client.inutilizar_numeracao(payload)

    def manifestar_destinatario(self, chave: str, tipo_manifestacao: int, sequencial: int = 1, ambiente: int = 2) -> dict:
        """
        Envia evento de Manifestação do Destinatário.
        :param tipo_manifestacao: 1=Confirmação, 2=Ciência, 3=Desconhecimento, 4=Não Realizada.
        """
        payload = {
            "Chave": chave,
            "TipoManifestacao": tipo_manifestacao,
            "NumeroSequencial": sequencial,
            "TipoAmbiente": ambiente
        }
        return brasil_nfe_client.manifestar_nota(payload)

    def pre_visualizar(self, dados_nota: dict, tipo_arquivo: int = 1) -> dict:
        """
        Gera pré-visualização (PDF ou XML) sem valor fiscal.
        :param tipo_arquivo: 0=XML, 1=PDF.
        """
        payload = {
            "TipoArquivo": tipo_arquivo,
            "TipoEnvio": 1, # 1=Objeto JSON
            "mostrarTarjaPreVisualizacao": True,
            "notaFiscal": {
                "nFInfos": [dados_nota]
            }
        }
        return brasil_nfe_client.pre_visualizar(payload)

# Instância Singleton para uso global
fiscal_service = FiscalService()
