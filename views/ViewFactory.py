from typing import Optional
from .AbstractView import AbstractView
from .BoardView import BoardView
from .PyGameView import PyGameView

class ViewFactory:
    @staticmethod
    def create_view(view_type: str, config: Optional[dict] = None) -> AbstractView:
        """Create a view instance based on type"""
        if view_type.lower() == "curses":
            return BoardView(config)
        elif view_type.lower() == "pygame":
            return PyGameView(config)
        else:
            raise ValueError(f"Unknown view type: {view_type}")
