try:
    import tkinter as tk
    import Assets.Client as Client
    from Assets.utils import check_allowed_values, ask_dropdown, create_packet
    import threading
    import re
    from tkinter import ttk, messagebox, simpledialog
    from Assets.Ansi_Text_Box import ANSIText
except ImportError as IE:
    from Assets.utils import handleIE
    handleIE(IE)
    quit()


class ClientUI:
    def __init__(self, root: tk.Tk, client: Client.Client, uName: str):
        self.root = root
        self.client = client
        self.version = self.client.VERSION
        self.uName = uName
        self.root.title("Client Interface")
        self.root.geometry("600x450")
        self.root.minsize(400,300)
        self.server_commands = ["No server connected"]
        self.command2packet = {}
        self.aServer = {}
        self.color = "white"
        self.ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        self._create_menu_bar()
        self._create_widgets()

    def _create_menu_bar(self):
        menubar = tk.Menu(self.root)

        # Client Menu
        client_menu = tk.Menu(menubar, tearoff=0)
        self.server_submenu = tk.Menu(client_menu, tearoff=0)

        self._update_server_menu()

        client_menu.add_cascade(label="Connect to Server", menu=self.server_submenu)
        client_menu.add_command(label="Disconnect from Server", command=self.disconnect_from_server)
        client_menu.add_command(label="Scan for Server", command=self.scan_for_server)
        client_menu.add_separator()
        client_menu.add_command(label="Quit", command=self.root.quit)
        menubar.add_cascade(label="Client", menu=client_menu)

        # Help Menu (Dynamic)
        self.help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=self.help_menu)

        # Populate initial help menu
        self.update_help_menu()

        self.root.config(menu=menubar)

    def _create_widgets(self):
        # configure main layout grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # display area (messages from server)
        display_frame = ttk.LabelFrame(main_frame, text=" Server Messages ", padding="5")
        display_frame.grid(row=0, column=0, sticky="nsew", pady=(0,10))
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(0, weight=1)

        self.message_display = ANSIText(display_frame, bg="#1e1e1e", fg="#ffffff", wrap="word", state="disabled")
        self.message_display.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=self.message_display.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.message_display.config(yscrollcommand=scrollbar.set)

        # User Input Area
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)

        self.input_box = ttk.Entry(input_frame)
        self.input_box.grid(row=0, column=0, sticky="ew", padx=(0,5))
        self.input_box.bind("<Return>", lambda event: self.send_message())

        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.grid(row=0, column=1)

    # UI Actions & Helper Methods
    def update_help_menu(self):
        """
         * Clears and rebuilds the help menu dynamically from self.server_commands
         * this method would be called whenever the server sends:
         * a <|COMMAND_UPDATE|>{comm1},{comm2},{etc.}<|END_UPDATE|> packet
        """
        self.help_menu.delete(0, tk.END)
        self.help_menu.add_command(label="-- Server Commands --", state="disabled")

        for cmd in self.server_commands:
            self.help_menu.add_command(
                label=cmd,
                command=lambda c=cmd: self._on_command_click(c)
            )

    def display_system_message(self, text: str):
        """
         * appends text to the display area
        """
        self.message_display.config(state="normal")
        self.message_display.append_ansi_text(f"{text}\n")
        self.message_display.see(tk.END)
        self.message_display.config(state="disabled")

    def clear_system_message(self):
        self.message_display.config(state="normal")
        self.message_display.delete("1.0", tk.END)
        self.message_display.config(state="disabled")

    def send_message(self):
        msg = self.input_box.get().strip()
        if not self.client.is_connected():
            self.display_system_message("[CLIENT] ERROR: Could not send message")
            self.input_box.delete(0, tk.END)
            return
        if msg:
            # send message to server
            self._send(msg)
            self.input_box.delete(0, tk.END)

    def _send(self, msg: str):
        threading.Thread(target=self.client.send(msg), daemon=True).start()

    def _sendCode(self, msg: str):
        threading.Thread(target=self.client.sendCode(msg), daemon=True).start()

    def _on_command_click(self, cmd: str):
        """
         * Action when a dynamic help menu command is clicked
        """
        if cmd in self.command2packet:
            packet = self.command2packet[cmd]
            # print(packet)
            if not packet:
                packet = "<|NULL|>"
            else:
                av = check_allowed_values(packet)
                if av == None:
                    value = simpledialog.askstring("Details", f"Please enter a value for {cmd}")
                else:
                    value = ask_dropdown(self.root, cmd, f"Select an Option for {cmd}", av)
                if value:
                    packet = create_packet(packet, value)
                else:
                    messagebox.showinfo("Command Info", f"Command clicked: {cmd}\npacket cancelled")
                    return
            # print(packet)
            # messagebox.showinfo("Command Info", f"Command clicked: {cmd}\npacket to send: {packet}")
            self._sendCode(packet)
            self._handle_ack()

    def _handle_ack(self):
        if self.client.is_connected():
            ack = self.client.waitAckRet()
            if not ack:
                self.display_system_message("[CLIENT] request not acknowledged")
            else:
                self.display_system_message(ack.replace("<|ACK|>",""))

    # Menu Event Handlers
    def connect_to_server(self, s):
        if self.client.is_connected():
            self.display_system_message("[CLIENT] WARNING: Already Connected to Server!")
            return
        # self.display_system_message("[CLIENT] WARNING: Connect To Server Not Completed Yet!")
        self.display_system_message(f"[DEBUG] SELECTED: {self.aServer[s]}")
        addr, port = self.aServer[s]
        self.client.connect(addr, port)

        self.recv_thread = threading.Thread(target=self.client.recv, args=(), daemon=True)
        self.recv_thread.start()

        self.get_thread = threading.Thread(target=self.getMsg, args=(), daemon=True)

        self.client.sendCode(
            f"<|SET_UNAME|>{self.uName}<|END_SET|><|SET_COLOR|>{self.color}<|END_SET|><|SET_VERSION|>{self.version}<|END_SET|>"
        )

        ack = self.client.waitAckRet()
        if not ack:
            self.display_system_message(ack.replace("<|EOF|>", ""))
            self.display_system_message("[CLIENT] Server did not acknowledge request!")
            self.client.disconnect()
            return

        # ack should be something like:
        #* <|ACK|>{comm1},{comm2},{etc.}<|END_ACK|>

        match = re.search(r"<\|ACK\|>(.*?)<\|END_ACK\|>", ack)
        if match:
            raw_values = match.group(1)
            comms = [val.strip() for val in raw_values.split(',')]
            self.server_commands = []
            for c in comms:
                comm, packet = c.split(":", 1)
                self.server_commands.append(comm)
                self.command2packet[comm] = packet
            self.update_help_menu()

        self.clear_system_message()
        self.display_system_message(f"Welcome {self.uName}!")
        self.display_system_message(f"You have connected to {s} succesfully!")
        self.get_thread.start()

    def disconnect_from_server(self):
        # self.display_system_message("[CLIENT] WARNING: Disconnect From Server Not Completed Yet!")
        if self.client.is_connected():
            self.clear_system_message()
            self.client.disconnect()
            self.display_system_message("[CLIENT] Disconnected from server!")
            self.server_commands = ["No server connected"]
            self.update_help_menu()
            return
        self.display_system_message("[CLIENT] WARNING: No Server is connected!")

    def scan_for_server(self):
        self.display_system_message("[CLIENT] INFO: Starting scan for servers!")
        scan_thread = threading.Thread(target=self.threaded_server_scanner, daemon=True)
        scan_thread.start()

    # Menu Helpers
    def _update_server_menu(self):
        self.server_submenu.delete(0, tk.END)
        self.server_submenu.add_command(
            label="-- Servers --", 
            state="disabled"
        )

        for server in self.aServer:
            self.server_submenu.add_command(
                label=server,
                command=lambda s=server: self.connect_to_server(s)
            )

    # Server Scanner Helpers
    def threaded_server_scanner(self):
        servers = self.client.find_server()
        self.display_system_message("[CLIENT] Info: Server Scan complete!")
        self.display_system_message(f"[CLIENT] INFO: Found {len(servers)} Servers!")
        self.aServer = {}
        for server in servers:
            # self.display_system_message(f"\t{server}")
            self.aServer[self.client.get_server_name(server)] = server
        self._update_server_menu()
        # self.display_system_message("[CLIENT] Server List Updated!")

    # Client Helpers
    def getMsg(self):
        while self.client.is_connected():
            if self.client.has_message(self.client.STRING):
                msg = self.client.getMsg()
                if msg:
                    self.display_system_message(msg)

if __name__ == '__main__':
    root = tk.Tk()
    client = Client.Client()
    uName = "Anonymous"
    app = ClientUI(root, client, uName)
    root.mainloop()
    if client.is_connected():
        client.disconnect()