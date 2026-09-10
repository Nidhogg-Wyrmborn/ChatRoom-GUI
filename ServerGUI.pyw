try:
    import tkinter as tk
    import Assets.Server as Server
    from Assets.utils import check_allowed_values, ask_dropdown, create_packet
    import threading
    import re
    from Assets import GUI
    from tkinter import ttk, messagebox, simpledialog
    from Assets.Ansi_Text_Box import ANSIText
except ImportError as IE:
    from Assets.utils import handleIE
    handleIE(IE)
    quit()

class ServerUI(GUI.GUI):
    def __init__(self, root: tk.Tk, server: Server.Server):
        self.server = server
        self.version = self.server.VERSION
        self.server_commands = []
        self.command2packet = {}
        self.aServer = {}
        self.color = "white"
        super().__init__(root, "Server")
        self.root.title("Server")
        self.server.redirect(target=self.display_system_message)
        self.stop_signal = threading.Event()
        self.server_thread = threading.Thread(target=self.start_server, args=(self.stop_signal,),daemon=True)
        self.server_thread.start()
        self.server_running = True

    def start_server(self, stop_event):
        try:
            self.server.start(stop_event)
            self.server.close()
        except Exception as e:
            self.display_system_message("[SERVER] ERROR: ")
            self.display_system_message(e)
        finally:
            self.display_system_message("[SERVER] Shutting Down!")

if __name__ == '__main__':
    root = tk.Tk()
    server = Server.Server()
    app = ServerUI(root, server)
    root.mainloop()
