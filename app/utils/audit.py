
def calcular_diferencas(antes, depois):
    """Calcula as diferenças entre os estados antes e depois"""
    try:
        import json
        antes_dict = json.loads(antes) if isinstance(antes, str) else antes
        depois_dict = json.loads(depois) if isinstance(depois, str) else depois
        
        diferencas = []
        todas_chaves = set(antes_dict.keys()) | set(depois_dict.keys())
        
        for chave in todas_chaves:
            valor_antes = antes_dict.get(chave, 'N/A')
            valor_depois = depois_dict.get(chave, 'N/A')
            
            if valor_antes != valor_depois:
                diferencas.append({
                    'campo': chave,
                    'antes': valor_antes,
                    'depois': valor_depois
                })
        
        return diferencas
    except Exception as e:
        return []