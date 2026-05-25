import customtkinter as ctk
from auth import LoginWindow
from excel_editor import ExcelEditor
from admin_panel import AdminPanel
import database

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Excel Manager")
        self.geometry("800x600")
        
        # Center the window
        self.update_idletasks()
        width = 800
        height = 600
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Initially hide the main window
        self.withdraw()

        # Show login window
        self.show_login()

    def show_login(self):
        self.login_window = LoginWindow(self, self.on_login_success)

    def on_login_success(self, username, role):
        # Reveal the main window and load the editor
        self.deiconify()
        
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(self.top_frame, text=f"Logged in as: {username} ({role})", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        if role == 'admin':
            ctk.CTkButton(self.top_frame, text="Admin Dashboard", command=self.open_admin_panel, fg_color="#28a745", hover_color="#218838").pack(side="right")
            
        self.editor = ExcelEditor(self, username)
        self.editor.pack(fill="both", expand=True)

    def open_admin_panel(self):
        AdminPanel(self)

if __name__ == "__main__":
    database.init_db()
    database.seed_table_from_excel_if_empty()
    app = App()
    app.mainloop()
