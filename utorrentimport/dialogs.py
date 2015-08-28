import gtk


class AsyncDialog(gtk.Dialog):
    """
    A gtk Dialog that does not block.
    has these additional arguments:
    response_callback: the callback to handle the response signal
    destroy_signals: A convince for setting signals that will destroy the dialog.
    """

    def __init__(self,
                 title=None,
                 parent=None,
                 flags=None,
                 buttons=None,
                 response_callback=None,
                 destroy_signals=None):
        gtk.Dialog.__init__(self, title, parent, flags, buttons)

        self.response_callback = response_callback

        if not isinstance(destroy_signals, list):
            destroy_signals = [destroy_signals]
        self.destroy_signals = destroy_signals

    def run(self):
        """a version of gtk.Dialog.run that does not block"""

        def dialog_response_cb(dialog, response_id):
            if response_id in self.destroy_signals:
                self.destroy()
            if self.response_callback:
                self.response_callback(response_id)

        self.connect('response', dialog_response_cb)
        if not self.modal:
            self.set_modal(True)
        self.show()
