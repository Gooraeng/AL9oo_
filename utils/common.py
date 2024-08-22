from __future__ import annotations
from discord import ui

class InviteLinkView(ui.View):
    def __init__(self, label : str, url : str):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label=label, url=url))