from typing import Optional
from .AbstractView import AbstractView
from .BoardView import BoardView  # Change import from CursesView to BoardView

class ViewFactory:
    @staticmethod
    def create_view(view_type: str, config: Optional[dict] = None) -> AbstractView:
        """Create a view instance based on type"""
        if view_type.lower() == "curses":
            return BoardView(config)  # Return BoardView instead of CursesView
        # Add other view implementations here
        # elif view_type.lower() == "pygame":
        #     return PygameView(config)
        else:
            raise ValueError(f"Unknown view type: {view_type}")
