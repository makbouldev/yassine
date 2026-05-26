import customtkinter as ctk
from tkinter import messagebox
import database
from tksheet import Sheet

class AdminPanel(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Administration")
        self.geometry("900x600")
        
        # Center the window
        self.update_idletasks()
        width = 900
        height = 600
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        self.transient(parent)
        self.grab_set()

        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_users = self.tabview.add("Utilisateurs")
        self.tab_history = self.tabview.add("Historique")
        
        self.setup_users_tab()
        self.setup_history_tab()

    def setup_users_tab(self):
        # Left frame: Add user
        self.add_frame = ctk.CTkFrame(self.tab_users, width=300)
        self.add_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkLabel(self.add_frame, text="Ajouter un utilisateur", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        self.new_user_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Nom d'utilisateur")
        self.new_user_entry.pack(pady=10, padx=20)
        
        self.new_pass_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Mot de passe", show="*")
        self.new_pass_entry.pack(pady=10, padx=20)
        
        self.role_var = ctk.StringVar(value="utilisateur")
        self.role_dropdown = ctk.CTkOptionMenu(
            self.add_frame,
            variable=self.role_var,
            values=["utilisateur", "administrateur"],
        )
        self.role_dropdown.pack(pady=10, padx=20)
        
        self.add_btn = ctk.CTkButton(self.add_frame, text="Ajouter", command=self.add_user)
        self.add_btn.pack(pady=20, padx=20)
        
        # Right frame: List users
        self.list_frame = ctk.CTkFrame(self.tab_users)
        self.list_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(self.list_frame, text="Liste des utilisateurs", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        self.user_sheet = Sheet(self.list_frame)
        self.user_sheet.enable_bindings(("single_select", "row_select"))
        self.user_sheet.pack(fill="both", expand=True, pady=(0, 10))
        
        self.btn_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=10)
        
        self.del_btn = ctk.CTkButton(self.btn_frame, text="Supprimer", command=self.delete_user, fg_color="red", hover_color="darkred")
        self.del_btn.pack(side="left", padx=10)

        self.pass_entry = ctk.CTkEntry(self.btn_frame, placeholder_text="Nouveau mot de passe")
        self.pass_entry.pack(side="left", padx=(50, 5))
        self.change_pass_btn = ctk.CTkButton(self.btn_frame, text="Modifier le mot de passe", command=self.change_password)
        self.change_pass_btn.pack(side="left", padx=5)

        self.refresh_users()

    def add_user(self):
        username = self.new_user_entry.get()
        password = self.new_pass_entry.get()
        role = self._db_role(self.role_var.get())
        
        if not username or not password:
            messagebox.showwarning("Erreur", "Le nom d'utilisateur et le mot de passe sont obligatoires.")
            return
            
        success = database.add_user(username, password, role)
        if success:
            messagebox.showinfo("Succès", f"Utilisateur {username} créé.")
            self.new_user_entry.delete(0, 'end')
            self.new_pass_entry.delete(0, 'end')
            self.refresh_users()
        else:
            messagebox.showerror("Erreur", "Ce nom d'utilisateur existe déjà.")

    def delete_user(self):
        selected = self.user_sheet.get_currently_selected()
        if not selected:
            messagebox.showwarning("Erreur", "Sélectionnez un utilisateur à supprimer.")
            return
        
        row = selected.row
        username = self.user_sheet.get_cell_data(row, 0)
        
        if username == 'admin':
            messagebox.showerror("Erreur", "Impossible de supprimer le compte administrateur par défaut.")
            return
            
        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer {username} ?"):
            database.delete_user(username)
            self.refresh_users()

    def change_password(self):
        selected = self.user_sheet.get_currently_selected()
        if not selected:
            messagebox.showwarning("Erreur", "Sélectionnez d'abord un utilisateur.")
            return
            
        row = selected.row
        username = self.user_sheet.get_cell_data(row, 0)
        new_password = self.pass_entry.get()
        
        if not new_password:
            messagebox.showwarning("Erreur", "Veuillez saisir un nouveau mot de passe.")
            return
            
        database.change_password(username, new_password)
        messagebox.showinfo("Succès", f"Mot de passe modifié pour {username}.")
        self.pass_entry.delete(0, 'end')

    def refresh_users(self):
        users = database.get_all_users()
        data = [[u[0], self._role_label(u[1])] for u in users]
        self.user_sheet.set_sheet_data(data)
        self.user_sheet.headers(["Nom d'utilisateur", "Rôle"])

    def _db_role(self, role_label):
        return "admin" if role_label == "administrateur" else "user"

    def _role_label(self, role):
        return "administrateur" if role == "admin" else "utilisateur"

    def setup_history_tab(self):
        self.history_sheet = Sheet(self.tab_history)
        self.history_sheet.enable_bindings(("single_select", "row_select", "column_width_resize", "arrowkeys"))
        self.history_sheet.pack(fill="both", expand=True, padx=10, pady=10)
        
        refresh_btn = ctk.CTkButton(self.tab_history, text="Actualiser l'historique", command=self.refresh_history)
        refresh_btn.pack(pady=10)
        
        self.refresh_history()

    def refresh_history(self):
        history = database.get_history()
        data = [list(h) for h in history]
        self.history_sheet.set_sheet_data(data)
        self.history_sheet.headers(["Date/heure", "Utilisateur", "Ligne", "Colonne", "Ancienne valeur", "Nouvelle valeur"])
        self.history_sheet.set_column_widths([150, 100, 50, 100, 150, 150])
