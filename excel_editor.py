import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
from tksheet import Sheet

import database


class ExcelEditor(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.parent = parent
        self.current_user = current_user
        self.df = None
        self._resize_after_id = None

        self.top_bar = ctk.CTkFrame(self, height=50)
        self.top_bar.pack(side="top", fill="x", padx=10, pady=(10, 5))

        self.save_button = ctk.CTkButton(
            self.top_bar,
            text="Save Changes",
            command=self.save_file,
            state="disabled",
        )
        self.save_button.pack(side="left", padx=5)

        self.refresh_button = ctk.CTkButton(
            self.top_bar,
            text="Refresh",
            command=self.load_table,
            fg_color="#6c757d",
            hover_color="#5a6268",
            width=90,
        )
        self.refresh_button.pack(side="left", padx=5)

        self.export_button = ctk.CTkButton(
            self.top_bar,
            text="Export Excel",
            command=self.export_excel,
            fg_color="#28a745",
            hover_color="#218838",
            width=110,
        )
        self.export_button.pack(side="left", padx=5)

        self.file_label = ctk.CTkLabel(self.top_bar, text="No table loaded.")
        self.file_label.pack(side="left", padx=20)

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(side="top", fill="x", padx=10, pady=(0, 5))

        self.entries = {}
        input_cols = ["Rep", "Date", "Reçu", "Libelles", "Versement", "Débours"]

        for col in input_cols:
            container = ctk.CTkFrame(self.input_frame, fg_color="transparent")
            container.pack(side="left", padx=4, pady=4, expand=True, fill="x")
            ctk.CTkLabel(container, text=col, font=ctk.CTkFont(size=11)).pack(anchor="w")
            entry = ctk.CTkEntry(container, height=26)
            entry.pack(fill="x")
            self.entries[col] = entry

        self.add_btn = ctk.CTkButton(
            self.input_frame,
            text="Add",
            command=self.add_from_inputs,
            fg_color="#17a2b8",
            hover_color="#138496",
            width=70,
        )
        self.add_btn.pack(side="left", padx=10, pady=(18, 0))

        self.sheet_frame = ctk.CTkFrame(self)
        self.sheet_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 5))

        self.sheet = Sheet(
            self.sheet_frame,
            show_x_scrollbar=True,
            show_y_scrollbar=True,
        )
        self.sheet.enable_bindings(
            (
                "single_select",
                "drag_select",
                "column_select",
                "row_select",
                "column_width_resize",
                "double_click_column_resize",
                "row_height_resize",
                "double_click_row_resize",
                "right_click_popup_menu",
                "rc_select",
                "rc_insert_row",
                "rc_delete_row",
                "copy",
                "cut",
                "paste",
                "delete",
                "undo",
                "edit_cell",
            )
        )
        self.sheet.extra_bindings("end_edit_cell", func=self.on_cell_edited)
        self.sheet.pack(fill="both", expand=True)

        self.sheet_frame.bind("<Configure>", self._on_frame_configure)

        self.footer = ctk.CTkFrame(self, height=50)
        self.footer.pack(side="bottom", fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(
            self.footer,
            text="TOTAUX",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=16)

        self.total_labels = {}
        for col in ("Versement", "Débours", "Honoraires", "T.V.A", "Honors/H.T"):
            container = ctk.CTkFrame(self.footer, fg_color="transparent")
            container.pack(side="left", padx=14, expand=True)
            ctk.CTkLabel(container, text=col, font=ctk.CTkFont(size=10, weight="bold")).pack()
            label = ctk.CTkLabel(
                container,
                text="0,00",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#28a745",
            )
            label.pack()
            self.total_labels[col] = label

        self.load_table()

    def load_table(self):
        try:
            headers, data = database.get_table_data()
            self.df = pd.DataFrame(data, columns=headers)

            self.sheet.set_sheet_data(data)
            self.sheet.headers(headers)

            self.file_label.configure(text=f"Loaded from {database.storage_label()}")
            self.save_button.configure(state="normal")

            self.after(100, self._fit_columns)
            self.recalculate()
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible de charger la table:\n{exc}")

    def _on_frame_configure(self, event):
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(80, lambda: self._fit_columns(event.width))

    def _fit_columns(self, frame_width=None):
        headers = self.sheet.headers()
        if not headers:
            return
        column_count = len(headers)
        if frame_width is None:
            self.sheet_frame.update_idletasks()
            frame_width = self.sheet_frame.winfo_width()

        available = max(frame_width - 68, column_count * 60)
        column_width = available // column_count

        try:
            self.sheet.set_column_widths([column_width] * column_count)
        except Exception:
            pass

    def add_from_inputs(self):
        headers = self.sheet.headers()
        if not headers:
            return

        new_row = [""] * len(headers)

        if "N°Fact" in headers:
            fact_index = headers.index("N°Fact")
            data = self.sheet.get_sheet_data()
            last_fact = 0
            for row in data:
                value = str(row[fact_index]).strip()
                try:
                    last_fact = max(last_fact, int(value))
                except ValueError:
                    pass
            new_row[fact_index] = f"{last_fact + 1:02d}"

        for col_name, entry in self.entries.items():
            if col_name in headers:
                new_row[headers.index(col_name)] = entry.get().strip()
                entry.delete(0, "end")

        data = self.sheet.get_sheet_data()
        data.append(new_row)
        self.sheet.set_sheet_data(data)
        self.recalculate()

    def on_cell_edited(self, event=None):
        self.recalculate()

    def recalculate(self, event=None):
        headers = self.sheet.headers()
        if not headers:
            return

        try:
            versement_index = headers.index("Versement")
            debours_index = headers.index("Débours")
            honoraires_index = headers.index("Honoraires")
            tva_index = headers.index("T.V.A")
            ht_index = headers.index("Honors/H.T")
        except ValueError:
            return

        data = self.sheet.get_sheet_data()

        for row_index, row in enumerate(data):
            try:
                versement_raw = str(row[versement_index]).replace(",", ".").replace(" ", "").strip()
                debours_raw = str(row[debours_index]).replace(",", ".").replace(" ", "").strip()
                if not versement_raw and not debours_raw:
                    continue

                versement = float(versement_raw) if versement_raw else 0.0
                debours = float(debours_raw) if debours_raw else 0.0
                honoraires = versement - debours
                ht = honoraires / 1.2
                tva = honoraires - ht

                for column_index, value in (
                    (honoraires_index, honoraires),
                    (tva_index, tva),
                    (ht_index, ht),
                ):
                    formatted = self._format_money(value)
                    if str(row[column_index]) != formatted:
                        self.sheet.set_cell_data(row_index, column_index, formatted)
            except (ValueError, IndexError):
                pass

        totals = {column: 0.0 for column in self.total_labels}
        for row in self.sheet.get_sheet_data():
            for column_name in totals:
                try:
                    column_index = headers.index(column_name)
                    value = str(row[column_index]).replace(",", ".").replace(" ", "").strip()
                    if value:
                        totals[column_name] += float(value)
                except (ValueError, IndexError):
                    pass

        for column_name, value in totals.items():
            self.total_labels[column_name].configure(text=self._format_money(value))

    def _format_money(self, value):
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ")

    def save_file(self):
        try:
            data = self.sheet.get_sheet_data()
            headers = self.sheet.headers()
            new_df = pd.DataFrame(data, columns=headers)

            if self.df is not None:
                self._log_changes(self.df, new_df, headers)

            database.save_table_data(headers, data)
            self.df = new_df
            messagebox.showinfo("Succès", "Table sauvegardée dans la base de données!")
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder:\n{exc}")

    def export_excel(self):
        headers = self.sheet.headers()
        if not headers:
            messagebox.showwarning("Erreur", "Aucune table à exporter.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Exporter vers Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="export_table.xlsx",
        )
        if not filepath:
            return

        try:
            data = self.sheet.get_sheet_data()
            export_df = pd.DataFrame(data, columns=headers)
            export_df.to_excel(filepath, index=False)
            messagebox.showinfo("Succès", f"Export Excel créé:\n{filepath}")
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible d'exporter:\n{exc}")

    def _log_changes(self, old_df, new_df, headers):
        for row_index in range(min(len(old_df), len(new_df))):
            for column in headers:
                if column not in old_df.columns:
                    continue
                old_value = str(old_df.at[row_index, column]).strip()
                new_value = str(new_df.at[row_index, column]).strip()
                if old_value.endswith(".0"):
                    old_value = old_value[:-2]
                if new_value.endswith(".0"):
                    new_value = new_value[:-2]
                if old_value != new_value and not (old_value in ("nan", "") and new_value == ""):
                    database.log_edit(self.current_user, row_index + 2, column, old_value, new_value)

        for row_index in range(len(old_df), len(new_df)):
            database.log_edit(self.current_user, row_index + 2, "ROW", "", "ADDED")
