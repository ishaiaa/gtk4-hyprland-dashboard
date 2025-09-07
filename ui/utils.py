from gi.repository import Gtk, Gdk

def load_css(path: str):
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(path)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def make_tile(label: str):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.set_css_classes(["tile", "tile-bg"])
    lbl = Gtk.Label(label=label)
    lbl.set_wrap(True)
    lbl.set_justify(Gtk.Justification.CENTER)
    box.append(lbl)
    return box

def apply_css(widget: Gtk.Widget, path: str):
    print(path)
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(path)
    widget.get_style_context().add_provider(
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )