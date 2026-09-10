try:
	import tkinter as tk
	import re
	from tkinter import ttk
	if __name__ == '__main__':
		from Ansi_Text_Box import ANSIText
	else:
		from Assets.Ansi_Text_Box import ANSIText
except ImportError as IE:
	if __name__ == '__main__':
		from utils import handleIE
	else:
		from Assets.utils import handleIE
	handleIE(IE)
	quit()


class GUI:
	def __init__(self, root: tk.Tk, type: str = 'DEMO'):
		self.root = root
		self.type = type
		self.root.geometry("600x450")
		self.root.minsize(400,600)
		self.root.maxsize(800,1200)
		self.ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

		self._create_menu_bar()
		self._create_widgets()

	def _create_menu_bar(self):
		self.menubar = tk.Menu(self.root)

		self.main_menu = tk.Menu(self.menubar, tearoff=0)
		self.menubar.add_cascade(label=self.type, menu=self.main_menu)

		self.help_menu = tk.Menu(self.menubar, tearoff=0)
		self.menubar.add_cascade(label="Help", menu=self.help_menu)

		self.root.config(menu=self.menubar)

	def _create_widgets(self):
		# configure basic layout of UI
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(0, weight=1)

		main_frame = ttk.Frame(self.root, padding="10")
		main_frame.grid(row=0, column=0, sticky="nsew")
		main_frame.columnconfigure(0, weight=1)
		main_frame.rowconfigure(0, weight=1)

		display_frame = ttk.LabelFrame(main_frame, text=" Console Messages ", padding="5")
		display_frame.grid(row=0, column=0, sticky="nsew", pady=(0,10))
		display_frame.columnconfigure(0, weight=1)
		display_frame.rowconfigure(0, weight=1)

		self.message_display = ANSIText(display_frame, bg="#111111", fg="#ffffff", wrap="word", state="disabled")
		self.message_display.grid(row=0, column=0, sticky="nsew")

		scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=self.message_display.yview)
		scrollbar.grid(row=0, column=1, sticky="ns")
		self.message_display.config(yscrollcommand=scrollbar.set)

		input_frame = ttk.Frame(main_frame)
		input_frame.grid(row=1, column=0, sticky="ew")
		input_frame.columnconfigure(0, weight=1)

		self.input_box = ttk.Entry(input_frame)
		self.input_box.grid(row=0, column=0, sticky="ew", padx=(0,5))
		self.input_box.bind("<Return>", lambda event: self.send_message())

		send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
		send_btn.grid(row=0, column=1)

	def display_system_message(self, text: str):
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
		self.display_system_message("[ERROR] send_message() has not been overwritten!")
		self.input_box.delete(0, tk.END)

	def _on_command_click(self, cmd: str):
		self.display_system_message("[ERROR] _on_command_click() has not been overwritten!")

if __name__ == '__main__':
	root = tk.Tk()
	app = GUI(root)
	root.mainloop()