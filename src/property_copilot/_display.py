"""Optional rich presentation for notebooks; importing workflows needs no IPython."""

try:
    from IPython.display import HTML, display
except ImportError:

    class HTML(str):
        """Plain representation when notebook dependencies are absent."""

    def display(*values):
        """Rich inspection is optional in command-line runs."""


__all__ = ["HTML", "display"]
