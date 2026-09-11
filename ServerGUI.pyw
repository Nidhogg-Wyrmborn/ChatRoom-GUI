try:
    import tkinter as tk
    import Assets.Server as Server
    from Assets.utils import check_allowed_values, ask_dropdown, create_packet
    import threading
    import re
    import time
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
        self.server_thread = threading.Thread(target=self.start_server, args=(),daemon=True)
        self.server_thread.start()
        self.server_running = True

    def _create_menu_bar(self):
        super()._create_menu_bar()
        self.main_menu.add_command(label="Set Server Name", command=self._server_name_popup)
        self.main_menu.add_command(label="restart", command=self.restart)
        self.main_menu.add_separator()
        self.main_menu.add_command(label="Quit", command=self.root.quit)

    def start_server(self):
        try:
            self.server.start()
            while self.server.is_running():
                time.sleep(1)
            self.server.reset()
        except Exception as e:
            self.display_system_message("[SERVER] ERROR: ")
            self.display_system_message(e)
            print(e)
        finally:
            self.display_system_message("[SERVER] Shutting Down!")
            
    def restart(self):
        threading.Thread(target=self._restart, args=(), daemon=True).start()

    def _server_name_popup(self):
        server_name = simpledialog.askstring("Server Name", f"Please enter a new Server name")
        self.server.set_name(server_name)

    def _restart(self):
        self.display_system_message("[DEBUG] Ending current Server!")
        threading.Thread(target=self._restart_server, args=(), daemon=True).start()
        self.server.stop()
        while self.server.is_running():
            time.sleep(1)
        self.server.reset()

        
    def _restart_server(self):
        while self.server.is_running():
            time.sleep(1)
        self.display_system_message("[DEBUG] Starting new Server!")
        self.server_thread = None
        self.server_thread = threading.Thread(target=self.start_server, args=(), daemon=True)
        self.server_thread.start()


if __name__ == '__main__':
    root = tk.Tk()
    server = Server.Server()
    app = ServerUI(root, server)
    root.mainloop()
