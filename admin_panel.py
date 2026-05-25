import customtkinter as ctk
from tkinter import messagebox
import database
from tksheet import Sheet

class AdminPanel(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Admin Dashboard")
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
        
        self.tab_users = self.tabview.add("Manage Users")
        self.tab_history = self.tabview.add("Edit History")
        
        self.setup_users_tab()
        self.setup_history_tab()

    def setup_users_tab(self):
        # Left frame: Add user
        self.add_frame = ctk.CTkFrame(self.tab_users, width=300)
        self.add_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkLabel(self.add_frame, text="Add New User", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        self.new_user_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Username")
        self.new_user_entry.pack(pady=10, padx=20)
        
        self.new_pass_entry = ctk.CTkEntry(self.add_frame, placeholder_text="Password", show="*")
        self.new_pass_entry.pack(pady=10, padx=20)
        
        self.role_var = ctk.StringVar(value="user")
        self.role_dropdown = ctk.CTkOptionMenu(self.add_frame, variable=self.role_var, values=["user", "admin"])
        self.role_dropdown.pack(pady=10, padx=20)
        
        self.add_btn = ctk.CTkButton(self.add_frame, text="Add User", command=self.add_user)
        self.add_btn.pack(pady=20, padx=20)
        
        # Right frame: List users
        self.list_frame = ctk.CTkFrame(self.tab_users)
        self.list_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(self.list_frame, text="User List", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        self.user_sheet = Sheet(self.list_frame)
        self.user_sheet.enable_bindings(("single_select", "row_select"))
        self.user_sheet.pack(fill="both", expand=True, pady=(0, 10))
        
        self.btn_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=10)
        
        self.del_btn = ctk.CTkButton(self.btn_frame, text="Delete Selected", command=self.delete_user, fg_color="red", hover_color="darkred")
        self.del_btn.pack(side="left", padx=10)

        self.pass_entry = ctk.CTkEntry(self.btn_frame, placeholder_text="New password")
        self.pass_entry.pack(side="left", padx=(50, 5))
        self.change_pass_btn = ctk.CTkButton(self.btn_frame, text="Change Password", command=self.change_password)
        self.change_pass_btn.pack(side="left", padx=5)

        self.refresh_users()

    def add_user(self):
        username = self.new_user_entry.get()
        password = self.new_pass_entry.get()
        role = self.role_var.get()
        
        if not username or not password:
            messagebox.showwarning("Error", "Username and password cannot be empty.")
            return
            
        success = database.add_user(username, password, role)
        if success:
            messagebox.showinfo("Success", f"User {username} created!")
            self.new_user_entry.delete(0, 'end')
            self.new_pass_entry.delete(0, 'end')
            self.refresh_users()
        else:
            messagebox.showerror("Error", "Username already exists!")

    def delete_user(self):
        selected = self.user_sheet.get_currently_selected()
        if not selected:
            messagebox.showwarning("Error", "Please select a user to delete.")
            return
        
        row = selected.row
        username = self.user_sheet.get_cell_data(row, 0)
        
        if username == 'admin':
            messagebox.showerror("Error", "Cannot delete the default admin account.")
            return
            
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete {username}?"):
            database.delete_user(username)
            self.refresh_users()

    def change_password(self):
        selected = self.user_sheet.get_currently_selected()
        if not selected:
            messagebox.showwarning("Error", "Please select a user first.")
            return
            
        row = selected.row
        username = self.user_sheet.get_cell_data(row, 0)
        new_password = self.pass_entry.get()
        
        if not new_password:
            messagebox.showwarning("Error", "Please enter a new password.")
            return
            
        database.change_password(username, new_password)
        messagebox.showinfo("Success", f"Password changed for {username}.")
        self.pass_entry.delete(0, 'end')

    def refresh_users(self):
        users = database.get_all_users()
        data = [[u[0], u[1]] for u in users]
        self.user_sheet.set_sheet_data(data)
        self.user_sheet.headers(["Username", "Role"])

    def setup_history_tab(self):
        self.history_sheet = Sheet(self.tab_history)
        self.history_sheet.enable_bindings(("single_select", "row_select", "column_width_resize", "arrowkeys"))
        self.history_sheet.pack(fill="both", expand=True, padx=10, pady=10)
        
        refresh_btn = ctk.CTkButton(self.tab_history, text="Refresh History", command=self.refresh_history)
        refresh_btn.pack(pady=10)
        
        self.refresh_history()

    def refresh_history(self):
        history = database.get_history()
        data = [list(h) for h in history]
        self.history_sheet.set_sheet_data(data)
        self.history_sheet.headers(["Timestamp", "User", "Row", "Column", "Old Value", "New Value"])
        self.history_sheet.set_column_widths([150, 100, 50, 100, 150, 150])
