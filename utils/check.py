from __future__ import annotations
from discord import app_commands, Interaction
from difflib import SequenceMatcher


def _match_check(text : str, original_list : list[str], output : int = 3):
    result : list[dict[str, float]] = []
    text_bytes = list(bytes(text, encoding='utf-8'))
    
    for i in list(set(original_list)):
        input_bytes = list(bytes(i, encoding='utf-8'))
        sm = SequenceMatcher(None, input_bytes, text_bytes)
        ratio = sm.ratio()
        if ratio > 0.47:
            result.append({
                i : ratio
            })
            
    result.sort(key=lambda i : list(i.values())[0], reverse=True)
    result = [i for key in result for i, _ in key.items()] 
    if len(result) > output:
        result = result[:output]
    return result 


def match_helper(text, original_list):
    result = _match_check(text, original_list, 1)
    result = [val for diction in result for val, _ in diction.items()][0]
    return result


def is_me():
    def pred(interaction : Interaction):
        return interaction.user.id == 303915314062557185
    return app_commands.check(pred)