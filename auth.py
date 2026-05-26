import customtkinter as ctk

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.title("Connexion")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Center the window
        self.update_idletasks()
        width = 400
        height = 300
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.parent = parent
        self.on_success = on_success

        # Ensure login is on top and blocks parent
        self.transient(parent)
        self.grab_set()

        # UI Elements
        self.title_label = ctk.CTkLabel(self, text="Bienvenue", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(30, 20))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Nom d'utilisateur", width=200)
        self.username_entry.pack(pady=(0, 15))

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Mot de passe", show="*", width=200)
        self.password_entry.pack(pady=(0, 20))

        self.login_button = ctk.CTkButton(self, text="Se connecter", command=self.login, width=200)
        self.login_button.pack()

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack(pady=(10, 0))

        # Bind Enter key to login
        self.bind('<Return>', lambda event: self.login())

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        import database
        role = database.verify_login(username, password)
        if role:
            self.error_label.configure(text="")
            self.destroy()
            self.on_success(username, role)
        else:
            self.error_label.configure(text="Identifiants invalides.")
