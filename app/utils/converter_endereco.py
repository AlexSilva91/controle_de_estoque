import re


def parse_endereco_string(endereco_str):
    """Converte string de endereço para objeto estruturado"""
    try:
        # Expressão regular para extrair componentes do endereço
        address_regex = r'^(.*?)(?:,\s*(?:nº|no|numero|número)\s*(\d+))?(?:,\s*(.*?))?(?:,\s*(.*?)\s*-\s*([A-Z]{2}))?$'
        matches = re.match(address_regex, endereco_str, re.IGNORECASE)
        
        if not matches:
            return None
            
        logradouro = matches.group(1).strip() if matches.group(1) else ''
        numero = matches.group(2).strip() if matches.group(2) else ''
        bairro = matches.group(3).strip() if matches.group(3) else ''
        cidade_estado = matches.group(4).strip() if matches.group(4) else ''
        estado = matches.group(5).strip() if matches.group(5) else ''
        
        # Separa cidade e estado se estiverem juntos (ex: "Ouricuri-PE")
        if cidade_estado and '-' in cidade_estado:
            cidade, estado = cidade_estado.split('-', 1)
            cidade = cidade.strip()
            estado = estado.strip()
        else:
            cidade = cidade_estado
        
        return {
            "logradouro": logradouro,
            "numero": numero,
            "complemento": "",
            "bairro": bairro,
            "cidade": cidade,
            "estado": estado,
            "cep": "",
            "instrucoes": "",
            "endereco_completo": endereco_str
        }
    except Exception as e:
        print(f"Erro ao parsear endereço: {str(e)}")
        return None