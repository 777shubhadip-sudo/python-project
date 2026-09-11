import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime, timedelta
import calendar

# ---------- Database Config ----------
DB_CONFIG = {'host': 'localhost', 'user': 'root', 'password': 'root', 'database': 'gym_db'}

# ---------- Database Connection ----------
def get_conn():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        messagebox.showerror("DB Error", f"Error connecting to database: {err}")
        return None

# ---------- Initialize Database ----------
def init_db():
    # Create DB if not exists
    base = mysql.connector.connect(host='localhost', user='root', password='root')
    cur = base.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS gym_db")
    base.close()

    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()

    # Users table for login/register
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(255),
            role ENUM('admin','trainer','reception') DEFAULT 'admin'
        )
    """)

    # Members table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            age INT,
            gender VARCHAR(10),
            phone VARCHAR(20),
            email VARCHAR(100),
            plan VARCHAR(50),
            join_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Payments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            member_id INT,
            amount DECIMAL(10,2),
            payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
        )
    """)

    # Membership Plans table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS membership_plans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            plan_name VARCHAR(100) UNIQUE,
            duration_days INT,
            price DECIMAL(10,2),
            description TEXT,
            features TEXT
        )
    """)

    # Progress Tracker table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress_tracker (
            id INT AUTO_INCREMENT PRIMARY KEY,
            member_id INT,
            record_date DATE,
            weight DECIMAL(5,2),
            height DECIMAL(5,2),
            bmi DECIMAL(5,2),
            body_fat DECIMAL(5,2),
            muscle_mass DECIMAL(5,2),
            notes TEXT,
            FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
        )
    """)

    # Insert default plans
    cur.execute("SELECT COUNT(*) FROM membership_plans")
    if cur.fetchone()[0] == 0:
        default_plans = [
            ("Basic Plan", 30, 1500.00, "Essential gym access", "Gym Access, Locker Room"),
            ("Premium Plan", 30, 2500.00, "All amenities included", "Gym Access, Group Classes, Personal Trainer Session"),
            ("Gold Plan", 30, 3500.00, "VIP treatment", "All Premium Features + Diet Plan, Spa Access"),
            ("3-Month Basic", 90, 4000.00, "3 months basic access", "Gym Access, Locker Room - 3 Months"),
            ("6-Month Premium", 180, 12000.00, "6 months premium access", "All Premium Features - 6 Months"),
            ("Annual Gold", 365, 35000.00, "1 year gold membership", "All Gold Features - 1 Year")
        ]
        cur.executemany("INSERT INTO membership_plans (plan_name, duration_days, price, description, features) VALUES (%s, %s, %s, %s, %s)", default_plans)

    conn.commit()
    conn.close()

# ---------- Login Page ----------
def login():
    win = tk.Tk()
    win.title("Gym System Login")
    win.geometry("400x300")
    win.configure(bg="#ffffff")

    tk.Label(win, text="Username:", bg="#ffffff", font=("Arial", 11)).pack(pady=10)
    username_entry = tk.Entry(win, font=("Arial", 11))
    username_entry.pack()

    tk.Label(win, text="Password:", bg="#ffffff", font=("Arial", 11)).pack(pady=10)
    password_entry = tk.Entry(win, show="*", font=("Arial", 11))
    password_entry.pack()

    def try_login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Enter username and password")
            return

        conn = get_conn()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
        conn.close()

        if row and row[0] == password:
            messagebox.showinfo("Success", "Login successful!")
            win.destroy()
            main_menu()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    tk.Button(win, text="Login", command=try_login, bg="#4CAF50", fg="white", 
              font=("Arial", 11, "bold"), width=15).pack(pady=20)
    tk.Button(win, text="Register", command=lambda: [win.destroy(), register()], 
              bg="#2196F3", fg="white", font=("Arial", 11), width=15).pack()
    win.mainloop()

# ---------- Register Page ----------
def register():
    win = tk.Tk()
    win.title("Register")
    win.geometry("400x350")
    win.configure(bg="#ffffff")

    tk.Label(win, text="Username:", bg="#ffffff", font=("Arial", 11)).pack(pady=5)
    username_entry = tk.Entry(win, font=("Arial", 11))
    username_entry.pack()

    tk.Label(win, text="Password:", bg="#ffffff", font=("Arial", 11)).pack(pady=5)
    password_entry = tk.Entry(win, show="*", font=("Arial", 11))
    password_entry.pack()

    tk.Label(win, text="Confirm Password:", bg="#ffffff", font=("Arial", 11)).pack(pady=5)
    confirm_entry = tk.Entry(win, show="*", font=("Arial", 11))
    confirm_entry.pack()

    tk.Label(win, text="Role:", bg="#ffffff", font=("Arial", 11)).pack(pady=5)
    role_var = tk.StringVar(win)
    role_combo = ttk.Combobox(win, textvariable=role_var, values=["admin","trainer","reception"], font=("Arial", 11))
    role_combo.pack()

    def submit_register():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        confirm = confirm_entry.get().strip()
        role = role_var.get()

        if not username or not password or not confirm or not role:
            messagebox.showerror("Error", "All fields are required")
            return
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return

        conn = get_conn()
        if not conn:
            return
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username,password,role) VALUES (%s,%s,%s)", (username,password,role))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful")
            win.destroy()
            login()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()

    tk.Button(win, text="Register", command=submit_register, bg="#4CAF50", fg="white", 
              font=("Arial", 11, "bold"), width=15).pack(pady=20)
    tk.Button(win, text="Back to Login", command=lambda: [win.destroy(), login()], 
              bg="#757575", fg="white", font=("Arial", 11), width=15).pack()
    win.mainloop()

# ---------- Generic Add Record ----------
def add_record(table, fields):
    win = tk.Toplevel(bg="#ffffff")
    win.title(f"Add {table.capitalize()}")
    win.geometry("400x400")
    
    entries = {}
    for i, (field_name, _) in enumerate(fields):
        tk.Label(win, text=field_name.capitalize() + ":", bg="#ffffff", font=("Arial", 10)).grid(row=i, column=0, padx=10, pady=10, sticky="e")
        e = tk.Entry(win, font=("Arial", 10), width=25)
        e.grid(row=i, column=1, padx=10, pady=10)
        entries[field_name] = e

    def submit():
        vals = [entries[f].get().strip() for f,_ in fields]
        if not vals[0]:
            messagebox.showerror("Error", "Required field is empty!")
            return
        conn = get_conn()
        if not conn:
            return
        cur = conn.cursor()
        placeholders = ", ".join(["%s"]*len(fields))
        field_names = ", ".join(f for f,_ in fields)
        try:
            cur.execute(f"INSERT INTO {table} ({field_names}) VALUES ({placeholders})", vals)
            conn.commit()
            messagebox.showinfo("Success", f"{table.capitalize()} added successfully!")
            win.destroy()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()

    tk.Button(win, text="Submit", command=submit, bg="#4CAF50", fg="white", 
              font=("Arial", 11, "bold"), width=15).grid(row=len(fields), column=1, pady=20)

# ---------- View Members with Edit Feature ----------
def view_members():
    win = tk.Toplevel(bg="#ffffff")
    win.title("Members List")
    win.geometry("1000x600")
    
    tk.Label(win, text="Members List", bg="#ffffff", fg="#333", 
             font=("Arial", 16, "bold")).pack(pady=15)
    
    # Search frame
    search_frame = tk.Frame(win, bg="#ffffff")
    search_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Label(search_frame, text="Search:", bg="#ffffff", font=("Arial", 11)).pack(side="left", padx=5)
    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 11), width=30)
    search_entry.pack(side="left", padx=5)
    
    def search_members():
        search_term = search_var.get().strip()
        conn = get_conn()
        if not conn:
            return
        cur = conn.cursor()
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)
                
            if search_term:
                cur.execute("""
                    SELECT id,name,age,gender,phone,email,plan,join_date 
                    FROM members 
                    WHERE name LIKE %s OR email LIKE %s OR phone LIKE %s
                    ORDER BY name
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            else:
                cur.execute("SELECT id,name,age,gender,phone,email,plan,join_date FROM members ORDER BY join_date DESC")
            
            for row in cur.fetchall():
                join_date = row[7].strftime("%Y-%m-%d") if row[7] else ""
                tree.insert("", "end", values=(*row[:7], join_date))
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()
    
    tk.Button(search_frame, text="Search", command=search_members, bg="#2196F3", fg="white",
              font=("Arial", 10, "bold")).pack(side="left", padx=5)
    tk.Button(search_frame, text="Clear", command=lambda: [search_var.set(""), search_members()], 
              bg="#757575", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
    
    # Buttons frame
    button_frame = tk.Frame(win, bg="#ffffff")
    button_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Button(button_frame, text="Refresh", command=search_members, bg="#4CAF50", fg="white",
              font=("Arial", 10, "bold")).pack(side="left", padx=5)
    tk.Button(button_frame, text="Edit Selected", command=lambda: edit_selected_member(), 
              bg="#FF9800", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    tk.Button(button_frame, text="Delete Selected", command=lambda: delete_selected_member(),
              bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    
    # Treeview frame
    tree_frame = tk.Frame(win)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    columns = ("ID","Name","Age","Gender","Phone","Email","Plan","Join Date")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
    
    # Configure columns
    column_widths = {"ID": 50, "Name": 120, "Age": 60, "Gender": 80, "Phone": 120, "Email": 150, "Plan": 120, "Join Date": 100}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=column_widths.get(col, 100))
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)
    
    # Double-click to edit
    def on_double_click(event):
        edit_selected_member()
    
    tree.bind("<Double-1>", on_double_click)
    
    # ---------- Edit Member Function ----------
    def edit_selected_member():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a member to edit")
            return
        
        member_data = tree.item(selected_item[0], "values")
        member_id = member_data[0]
        
        edit_win = tk.Toplevel(win)
        edit_win.title(f"Edit Member - {member_data[1]}")
        edit_win.geometry("500x500")
        edit_win.configure(bg="#ffffff")
        edit_win.transient(win)
        edit_win.grab_set()
        
        # Get current membership plans for dropdown
        conn = get_conn()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("SELECT plan_name FROM membership_plans ORDER BY plan_name")
        plans = [row[0] for row in cur.fetchall()]
        conn.close()
        
        # Form fields
        fields = [
            ("Name", "name", member_data[1]),
            ("Age", "age", member_data[2]),
            ("Gender", "gender", member_data[3]),
            ("Phone", "phone", member_data[4]),
            ("Email", "email", member_data[5]),
            ("Plan", "plan", member_data[6])
        ]
        
        entries = {}
        for i, (label, field, current_value) in enumerate(fields):
            tk.Label(edit_win, text=label + ":", bg="#ffffff", font=("Arial", 10)).grid(row=i, column=0, padx=10, pady=10, sticky="e")
            
            if field == "gender":
                gender_var = tk.StringVar(value=current_value)
                gender_frame = tk.Frame(edit_win, bg="#ffffff")
                gender_frame.grid(row=i, column=1, padx=10, pady=10, sticky="w")
                tk.Radiobutton(gender_frame, text="Male", variable=gender_var, value="Male", bg="#ffffff").pack(side="left")
                tk.Radiobutton(gender_frame, text="Female", variable=gender_var, value="Female", bg="#ffffff").pack(side="left")
                tk.Radiobutton(gender_frame, text="Other", variable=gender_var, value="Other", bg="#ffffff").pack(side="left")
                entries[field] = gender_var
            elif field == "plan":
                plan_var = tk.StringVar(value=current_value)
                plan_combo = ttk.Combobox(edit_win, textvariable=plan_var, values=plans, font=("Arial", 10), width=27)
                plan_combo.grid(row=i, column=1, padx=10, pady=10, sticky="w")
                entries[field] = plan_var
            else:
                e = tk.Entry(edit_win, font=("Arial", 10), width=30)
                e.insert(0, current_value)
                e.grid(row=i, column=1, padx=10, pady=10, sticky="w")
                entries[field] = e
        
        def update_member():
            update_data = {}
            for field, entry in entries.items():
                if isinstance(entry, (tk.StringVar, tk.IntVar, tk.DoubleVar)):
                    update_data[field] = entry.get().strip()
                else:
                    update_data[field] = entry.get().strip()
            
            # Validation
            if not update_data['name']:
                messagebox.showerror("Error", "Name is required")
                return
            
            try:
                if update_data['age']:
                    age_val = int(update_data['age'])
                    if age_val < 1 or age_val > 120:
                        raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Age must be a valid number between 1 and 120")
                return
            
            conn = get_conn()
            if not conn:
                return
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE members 
                    SET name=%s, age=%s, gender=%s, phone=%s, email=%s, plan=%s 
                    WHERE id=%s
                """, (
                    update_data['name'],
                    update_data['age'] if update_data['age'] else None,
                    update_data['gender'],
                    update_data['phone'],
                    update_data['email'],
                    update_data['plan'],
                    member_id
                ))
                conn.commit()
                messagebox.showinfo("Success", "Member updated successfully!")
                edit_win.destroy()
                search_members()  # Refresh the list
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"Database error: {e}")
            finally:
                conn.close()
        
        # Buttons
        button_frame = tk.Frame(edit_win, bg="#ffffff")
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="Update Member", command=update_member, 
                  bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), width=15).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=edit_win.destroy,
                  bg="#757575", fg="white", font=("Arial", 11), width=15).pack(side="left", padx=10)
    
    # ---------- Delete Member Function ----------
    def delete_selected_member():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a member to delete")
            return
        
        member_data = tree.item(selected_item[0], "values")
        member_name = member_data[1]
        
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete member:\n\n{member_name}?\n\nThis action cannot be undone!",
            icon='warning'
        )
        
        if confirm:
            conn = get_conn()
            if not conn:
                return
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM members WHERE id=%s", (member_data[0],))
                conn.commit()
                messagebox.showinfo("Success", f"Member '{member_name}' deleted successfully!")
                search_members()  # Refresh the list
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"Database error: {e}")
            finally:
                conn.close()
    
    # Load initial data
    search_members()

# ---------- Add Payment ----------
def add_payment():
    win = tk.Toplevel(bg="#ffffff")
    win.title("Add Payment")
    win.geometry("400x300")
    
    tk.Label(win, text="Select Member:", bg="#ffffff", font=("Arial", 11)).pack(pady=10)
    
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute("SELECT id,name FROM members")
    members = cur.fetchall()
    conn.close()
    
    member_names = [m[1] for m in members]
    member_var = tk.StringVar(win)
    combo = ttk.Combobox(win, textvariable=member_var, values=member_names, 
                         font=("Arial", 11), width=30)
    combo.pack(pady=5)
    
    tk.Label(win, text="Payment Amount (₹):", bg="#ffffff", font=("Arial", 11)).pack(pady=10)
    amount_entry = tk.Entry(win, font=("Arial", 11))
    amount_entry.pack(pady=5)

    def submit_payment():
        member_name = member_var.get()
        amount = amount_entry.get().strip()
        if not member_name or not amount:
            messagebox.showerror("Error","Please select member and enter amount")
            return
        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error","Please enter a valid positive amount")
            return
        
        member_id = next((m[0] for m in members if m[1]==member_name), None)
        if member_id is None:
            messagebox.showerror("Error","Selected member not found")
            return
        
        conn = get_conn()
        if not conn:
            return
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO payments (member_id,amount) VALUES (%s,%s)",(member_id,amount_val))
            conn.commit()
            messagebox.showinfo("Success","Payment recorded successfully")
            win.destroy()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()

    tk.Button(win, text="Submit Payment", command=submit_payment, bg="#4CAF50", fg="white",
              font=("Arial", 11, "bold"), width=15).pack(pady=20)

# ---------- View Payments ----------
def view_payments():
    win = tk.Toplevel(bg="#ffffff")
    win.title("Payments History")
    win.geometry("800x500")
    
    tk.Label(win, text="Payments List", bg="#ffffff", fg="#333",
             font=("Arial", 16, "bold")).pack(pady=15)
    
    frame = tk.Frame(win)
    frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    columns = ("ID","Member Name","Amount","Payment Date")
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=150)
    
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)
    
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT p.id, m.name, p.amount, p.payment_date
            FROM payments p
            JOIN members m ON p.member_id = m.id
            ORDER BY p.payment_date DESC
        """)
        for row in cur.fetchall():
            payment_date = row[3].strftime("%Y-%m-%d %H:%M") if row[3] else ""
            tree.insert("", "end", values=(row[0], row[1], f"₹{row[2]:.2f}", payment_date))
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Database error: {e}")
    finally:
        conn.close()

# ---------- Membership Plans Page ----------
def membership_plans():
    win = tk.Toplevel(bg="#ffffff")
    win.title("Membership Plans")
    win.geometry("900x500")
    
    tk.Label(win, text="Membership Plans & Packages", bg="#ffffff", fg="#333",
             font=("Arial", 16, "bold")).pack(pady=15)
    
    # Buttons frame
    button_frame = tk.Frame(win, bg="#ffffff")
    button_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Button(button_frame, text="Add New Plan", command=add_membership_plan, 
              bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    
    # Treeview frame
    tree_frame = tk.Frame(win)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    columns = ("ID", "Plan Name", "Duration (Days)", "Price (₹)", "Description", "Features")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
    
    # Configure columns
    for col in columns:
        tree.heading(col, text=col)
        if col == "ID":
            tree.column(col, width=50, anchor="center")
        elif col in ["Duration (Days)", "Price (₹)"]:
            tree.column(col, width=100, anchor="center")
        elif col == "Plan Name":
            tree.column(col, width=120)
        else:
            tree.column(col, width=150)
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)
    
    # Load data
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, plan_name, duration_days, price, description, features FROM membership_plans ORDER BY price")
        for row in cur.fetchall():
            tree.insert("", "end", values=row)
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Database error: {e}")
    finally:
        conn.close()

def add_membership_plan():
    win = tk.Toplevel(bg="#ffffff")
    win.title("Add Membership Plan")
    win.geometry("500x400")
    
    fields = [
        ("Plan Name", "plan_name"),
        ("Duration (Days)", "duration_days"), 
        ("Price (₹)", "price"),
        ("Description", "description"),
        ("Features", "features")
    ]
    
    entries = {}
    for i, (label, field) in enumerate(fields):
        tk.Label(win, text=label + ":", bg="#ffffff", font=("Arial", 10)).grid(row=i, column=0, padx=10, pady=10, sticky="e")
        if field == "features":
            e = tk.Text(win, height=4, width=30, font=("Arial", 10))
        else:
            e = tk.Entry(win, width=30, font=("Arial", 10))
        e.grid(row=i, column=1, padx=10, pady=10)
        entries[field] = e
    
    def submit():
        data = {}
        for field, entry in entries.items():
            if field == "features":
                data[field] = entry.get("1.0", "end-1c").strip()
            else:
                data[field] = entry.get().strip()
        
        # Validation
        if not all([data['plan_name'], data['duration_days'], data['price']]):
            messagebox.showerror("Error", "Please fill all required fields")
            return
        
        try:
            data['duration_days'] = int(data['duration_days'])
            data['price'] = float(data['price'])
        except ValueError:
            messagebox.showerror("Error", "Duration and Price must be numbers")
            return
        
        conn = get_conn()
        if not conn:
            return
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO membership_plans (plan_name, duration_days, price, description, features) 
                VALUES (%s, %s, %s, %s, %s)
            """, (data['plan_name'], data['duration_days'], data['price'], data['description'], data['features']))
            conn.commit()
            messagebox.showinfo("Success", "Membership plan added successfully!")
            win.destroy()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()
    
    tk.Button(win, text="Add Plan", command=submit, bg="#4CAF50", fg="white", 
              font=("Arial", 11, "bold"), width=15).grid(row=len(fields), column=1, pady=20)

# ---------- Progress Tracker Page ----------
def progress_tracker():
    win = tk.Toplevel(bg="#ffffff")
    win.title("Progress Tracker")
    win.geometry("1000x600")
    
    tk.Label(win, text="Fitness Progress Tracker", bg="#ffffff", fg="#333",
             font=("Arial", 16, "bold")).pack(pady=15)
    
    # Controls frame
    controls_frame = tk.Frame(win, bg="#ffffff")
    controls_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Label(controls_frame, text="Select Member:", bg="#ffffff", font=("Arial", 11)).pack(side="left", padx=5)
    
    conn = get_conn()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM members")
    members = cur.fetchall()
    conn.close()
    
    member_var = tk.StringVar(win)
    member_combo = ttk.Combobox(controls_frame, textvariable=member_var, 
                               values=[m[1] for m in members], width=25, font=("Arial", 11))
    member_combo.pack(side="left", padx=5)
    
    # Progress data frame
    progress_frame = tk.Frame(win)
    progress_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    columns = ("Date", "Weight (kg)", "Height (cm)", "BMI", "Body Fat %", "Muscle Mass (kg)", "Notes")
    tree = ttk.Treeview(progress_frame, columns=columns, show="headings", height=10)
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="center")
    
    scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)
    
    # Stats frame
    stats_frame = tk.Frame(win, bg="#f5f5f5", height=80)
    stats_frame.pack(fill="x", padx=20, pady=10)
    stats_frame.pack_propagate(False)
    
    stats_labels = {}
    stats_data = ["Current Weight: -", "BMI: -", "Body Fat: -", "Progress: -"]
    for i, text in enumerate(stats_data):
        stats_labels[i] = tk.Label(stats_frame, text=text, bg="#f5f5f5", fg="#333", 
                                  font=("Arial", 11))
        stats_labels[i].pack(side="left", expand=True)
    
    def load_progress_data():
        member_name = member_var.get()
        if not member_name:
            messagebox.showwarning("Warning", "Please select a member first")
            return
        
        member_id = next((m[0] for m in members if m[1] == member_name), None)
        if not member_id:
            messagebox.showerror("Error", "Member not found")
            return
        
        # Clear tree
        for item in tree.get_children():
            tree.delete(item)
        
        conn = get_conn()
        if not conn:
            return
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT record_date, weight, height, bmi, body_fat, muscle_mass, notes 
                FROM progress_tracker 
                WHERE member_id = %s 
                ORDER BY record_date DESC
            """, (member_id,))
            
            for row in cur.fetchall():
                tree.insert("", "end", values=row)
            
            # Update stats
            cur.execute("""
                SELECT weight, bmi, body_fat 
                FROM progress_tracker 
                WHERE member_id = %s 
                ORDER BY record_date DESC LIMIT 1
            """, (member_id,))
            
            latest = cur.fetchone()
            if latest:
                stats_labels[0].config(text=f"Current Weight: {latest[0]} kg")
                stats_labels[1].config(text=f"BMI: {latest[1]}")
                stats_labels[2].config(text=f"Body Fat: {latest[2]}%")
                
                # Calculate progress
                cur.execute("""
                    SELECT weight FROM progress_tracker 
                    WHERE member_id = %s 
                    ORDER BY record_date ASC LIMIT 1
                """, (member_id,))
                first_record = cur.fetchone()
                if first_record and first_record[0]:
                    progress = latest[0] - first_record[0]
                    progress_text = f"Progress: {progress:+.1f} kg"
                    color = "green" if progress < 0 else "red" if progress > 0 else "black"
                    stats_labels[3].config(text=progress_text, fg=color)
                    
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
        finally:
            conn.close()
    
    def add_progress_record():
        member_name = member_var.get()
        if not member_name:
            messagebox.showwarning("Warning", "Please select a member first")
            return
        
        add_progress_window = tk.Toplevel(bg="#ffffff")
        add_progress_window.title("Add Progress Record")
        add_progress_window.geometry("400x500")
        
        member_id = next((m[0] for m in members if m[1] == member_name), None)
        if not member_id:
            messagebox.showerror("Error", "Member not found")
            add_progress_window.destroy()
            return
        
        fields = [
            ("Weight (kg)", "weight"),
            ("Height (cm)", "height"), 
            ("Body Fat %", "body_fat"),
            ("Muscle Mass (kg)", "muscle_mass"),
            ("Notes", "notes")
        ]
        
        entries = {}
        for i, (label, field) in enumerate(fields):
            tk.Label(add_progress_window, text=label + ":", bg="#ffffff", font=("Arial", 10)).grid(row=i, column=0, padx=10, pady=10, sticky="e")
            if field == "notes":
                e = tk.Text(add_progress_window, height=4, width=25, font=("Arial", 10))
            else:
                e = tk.Entry(add_progress_window, width=25, font=("Arial", 10))
            e.grid(row=i, column=1, padx=10, pady=10)
            entries[field] = e
        
        def calculate_bmi():
            try:
                weight = float(entries['weight'].get())
                height = float(entries['height'].get()) / 100  # convert cm to m
                bmi = weight / (height * height)
                bmi_label.config(text=f"BMI: {bmi:.1f}")
                return bmi
            except:
                bmi_label.config(text="BMI: -")
                return None
        
        tk.Button(add_progress_window, text="Calculate BMI", command=calculate_bmi, 
                  bg="#2196F3", fg="white", font=("Arial", 10)).grid(row=len(fields), column=0, pady=10)
        bmi_label = tk.Label(add_progress_window, text="BMI: -", bg="#ffffff", 
                            font=("Arial", 11, "bold"), fg="#f44336")
        bmi_label.grid(row=len(fields), column=1, pady=10)
        
        def submit():
            data = {}
            for field, entry in entries.items():
                if field == "notes":
                    data[field] = entry.get("1.0", "end-1c").strip()
                else:
                    val = entry.get().strip()
                    data[field] = float(val) if val else None
            
            bmi = calculate_bmi()
            if bmi is None:
                messagebox.showerror("Error", "Please enter valid weight and height to calculate BMI")
                return
            
            conn = get_conn()
            if not conn:
                return
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO progress_tracker (member_id, record_date, weight, height, bmi, body_fat, muscle_mass, notes) 
                    VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s)
                """, (member_id, data['weight'], data['height'], bmi, data['body_fat'], data['muscle_mass'], data['notes']))
                conn.commit()
                messagebox.showinfo("Success", "Progress record added successfully!")
                add_progress_window.destroy()
                load_progress_data()
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"Database error: {e}")
            finally:
                conn.close()
        
        tk.Button(add_progress_window, text="Save Record", command=submit, bg="#4CAF50", fg="white", 
                  font=("Arial", 11, "bold"), width=15).grid(row=len(fields)+1, column=1, pady=20)
    
    tk.Button(controls_frame, text="Add Progress Record", command=add_progress_record, 
              bg="#FF9800", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)
    tk.Button(controls_frame, text="View Progress", command=load_progress_data, 
              bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

# ---------- Reports & Analytics Page ----------
def reports_analytics():
    win = tk.Toplevel(bg="#ffffff")
    win.title("Reports & Analytics")
    win.geometry("1000x600")
    
    tk.Label(win, text="Reports & Analytics Dashboard", bg="#ffffff", fg="#333",
             font=("Arial", 16, "bold")).pack(pady=15)
    
    # Stats frame
    stats_frame = tk.Frame(win, bg="#e3f2fd")
    stats_frame.pack(fill="x", padx=20, pady=10)
    
    # Create stats labels
    stats_data = {
        "Total Members": "0",
        "Total Revenue": "₹0",
        "Monthly Revenue": "₹0", 
        "Active Plans": "0"
    }
    
    stats_labels = {}
    for i, (key, value) in enumerate(stats_data.items()):
        stat_frame = tk.Frame(stats_frame, bg="#bbdefb", relief="raised", bd=1)
        stat_frame.pack(side="left", expand=True, fill="both", padx=5, pady=5)
        
        tk.Label(stat_frame, text=key, bg="#bbdefb", fg="#333", 
                font=("Arial", 10, "bold")).pack(pady=5)
        stats_labels[key] = tk.Label(stat_frame, text=value, bg="#bbdefb", fg="#1976d2",
                                   font=("Arial", 12, "bold"))
        stats_labels[key].pack(pady=5)
    
    # Reports frame
    reports_frame = tk.Frame(win)
    reports_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Left frame for quick stats
    left_frame = tk.Frame(reports_frame)
    left_frame.pack(side="left", fill="both", expand=True)
    
    # Right frame for detailed reports
    right_frame = tk.Frame(reports_frame)
    right_frame.pack(side="right", fill="both", expand=True)
    
    # Quick statistics
    quick_stats_frame = tk.LabelFrame(left_frame, text="Quick Statistics", 
                                    font=("Arial", 11, "bold"), bg="#ffffff")
    quick_stats_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    quick_stats_text = tk.Text(quick_stats_frame, height=10, width=40, font=("Arial", 10))
    quick_stats_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Detailed reports
    detailed_frame = tk.LabelFrame(right_frame, text="Detailed Reports", 
                                 font=("Arial", 11, "bold"), bg="#ffffff")
    detailed_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Report type selection
    report_type = tk.StringVar(value="membership")
    tk.Radiobutton(detailed_frame, text="Membership Report", variable=report_type, 
                   value="membership", bg="#ffffff", font=("Arial", 10)).pack(anchor="w", padx=10, pady=5)
    tk.Radiobutton(detailed_frame, text="Revenue Report", variable=report_type, 
                   value="revenue", bg="#ffffff", font=("Arial", 10)).pack(anchor="w", padx=10, pady=5)
    tk.Radiobutton(detailed_frame, text="Plan Popularity", variable=report_type, 
                   value="plans", bg="#ffffff", font=("Arial", 10)).pack(anchor="w", padx=10, pady=5)
    
    report_text = tk.Text(detailed_frame, height=12, width=50, font=("Arial", 10))
    report_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    tk.Button(detailed_frame, text="Generate Report", 
              command=lambda: generate_report(report_type.get(), report_text),
              bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(pady=10)
    
    # Load initial data
    load_dashboard_data(stats_labels, quick_stats_text)

def load_dashboard_data(stats_labels, quick_stats_text):
    conn = get_conn()
    if not conn:
        return
    
    cur = conn.cursor()
    try:
        # Total members
        cur.execute("SELECT COUNT(*) FROM members")
        total_members = cur.fetchone()[0]
        stats_labels["Total Members"].config(text=str(total_members))
        
        # Total revenue
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payments")
        total_revenue = cur.fetchone()[0]
        stats_labels["Total Revenue"].config(text=f"₹{total_revenue:,.2f}")
        
        # Monthly revenue (current month)
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments 
            WHERE MONTH(payment_date) = MONTH(CURRENT_DATE()) 
            AND YEAR(payment_date) = YEAR(CURRENT_DATE())
        """)
        monthly_revenue = cur.fetchone()[0]
        stats_labels["Monthly Revenue"].config(text=f"₹{monthly_revenue:,.2f}")
        
        # Active plans count
        cur.execute("SELECT COUNT(DISTINCT plan) FROM members WHERE plan IS NOT NULL AND plan != ''")
        active_plans = cur.fetchone()[0]
        stats_labels["Active Plans"].config(text=str(active_plans))
        
        # Quick statistics
        quick_stats_text.delete("1.0", "end")
        
        # Recent signups
        cur.execute("SELECT COUNT(*), DATE(join_date) FROM members GROUP BY DATE(join_date) ORDER BY DATE(join_date) DESC LIMIT 5")
        recent_signups = cur.fetchall()
        
        quick_stats_text.insert("end", "Recent Signups:\n")
        for count, date in recent_signups:
            quick_stats_text.insert("end", f"  {date}: {count} member(s)\n")
        
        # Gender distribution
        cur.execute("SELECT gender, COUNT(*) FROM members GROUP BY gender")
        gender_stats = cur.fetchall()
        quick_stats_text.insert("end", "\nGender Distribution:\n")
        for gender, count in gender_stats:
            quick_stats_text.insert("end", f"  {gender}: {count}\n")
        
        # Recent payments
        quick_stats_text.insert("end", "\nRecent Revenue:\n")
        cur.execute("""
            SELECT DATE(payment_date), SUM(amount) 
            FROM payments 
            GROUP BY DATE(payment_date) 
            ORDER BY DATE(payment_date) DESC 
            LIMIT 5
        """)
        recent_payments = cur.fetchall()
        for date, amount in recent_payments:
            quick_stats_text.insert("end", f"  {date}: ₹{amount:,.2f}\n")
        
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Database error: {e}")
    finally:
        conn.close()

def generate_report(report_type, report_text):
    report_text.delete("1.0", "end")
    
    conn = get_conn()
    if not conn:
        return
    
    cur = conn.cursor()
    try:
        if report_type == "membership":
            report_text.insert("end", "=== MEMBERSHIP REPORT ===\n\n")
            
            # Age distribution
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN age < 18 THEN 'Under 18'
                        WHEN age BETWEEN 18 AND 25 THEN '18-25'
                        WHEN age BETWEEN 26 AND 35 THEN '26-35' 
                        WHEN age BETWEEN 36 AND 45 THEN '36-45'
                        WHEN age > 45 THEN 'Over 45'
                        ELSE 'Not specified'
                    END as age_group,
                    COUNT(*) as count
                FROM members 
                GROUP BY age_group 
                ORDER BY count DESC
            """)
            report_text.insert("end", "Age Distribution:\n")
            for age_group, count in cur.fetchall():
                report_text.insert("end", f"  {age_group}: {count} members\n")
            
            # Plan popularity
            cur.execute("SELECT plan, COUNT(*) FROM members WHERE plan IS NOT NULL GROUP BY plan ORDER BY COUNT(*) DESC")
            report_text.insert("end", "\nPlan Popularity:\n")
            for plan, count in cur.fetchall():
                report_text.insert("end", f"  {plan}: {count} members\n")
                
        elif report_type == "revenue":
            report_text.insert("end", "=== REVENUE REPORT ===\n\n")
            
            # Monthly revenue for last 6 months
            cur.execute("""
                SELECT 
                    YEAR(payment_date) as year,
                    MONTH(payment_date) as month, 
                    SUM(amount) as revenue
                FROM payments 
                WHERE payment_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
                GROUP BY YEAR(payment_date), MONTH(payment_date)
                ORDER BY year DESC, month DESC
            """)
            report_text.insert("end", "Last 6 Months Revenue:\n")
            for year, month, revenue in cur.fetchall():
                month_name = calendar.month_name[month]
                report_text.insert("end", f"  {month_name} {year}: ₹{revenue:,.2f}\n")
            
            # Top paying members
            cur.execute("""
                SELECT m.name, SUM(p.amount) as total_paid
                FROM payments p
                JOIN members m ON p.member_id = m.id
                GROUP BY m.id, m.name
                ORDER BY total_paid DESC
                LIMIT 10
            """)
            report_text.insert("end", "\nTop Paying Members:\n")
            for name, total in cur.fetchall():
                report_text.insert("end", f"  {name}: ₹{total:,.2f}\n")
                
        elif report_type == "plans":
            report_text.insert("end", "=== PLAN POPULARITY REPORT ===\n\n")
            
            cur.execute("""
                SELECT 
                    mp.plan_name,
                    mp.price,
                    COUNT(m.id) as member_count,
                    COUNT(m.id) * mp.price as estimated_revenue
                FROM membership_plans mp
                LEFT JOIN members m ON mp.plan_name = m.plan
                GROUP BY mp.id, mp.plan_name, mp.price
                ORDER BY member_count DESC
            """)
            report_text.insert("end", "Plan Popularity & Revenue:\n")
            for plan_name, price, count, revenue in cur.fetchall():
                report_text.insert("end", f"  {plan_name} (₹{price:,.2f}): {count} members, Est. Revenue: ₹{revenue:,.2f}\n")
                
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Database error: {e}")
    finally:
        conn.close()

# ---------- Main Menu ----------
def main_menu():
    root = tk.Tk()
    root.title("Gym Fitness Management System")
    root.geometry("600x500")
    root.configure(bg="#ffffff")
    
    # Header
    header_frame = tk.Frame(root, bg="#2196F3", height=80)
    header_frame.pack(fill="x", padx=20, pady=20)
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="🏋️ Gym Management System", bg="#2196F3", fg="white", 
             font=("Arial", 18, "bold")).pack(expand=True)
    tk.Label(header_frame, text="Complete Gym Management Solution", bg="#2196F3", fg="#e3f2fd",
             font=("Arial", 11)).pack(expand=True)
    
    # Main buttons frame
    main_frame = tk.Frame(root, bg="#ffffff")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Button configuration with simple color scheme
    buttons = [
        ("👥 Add New Member", lambda: add_record("members",[("name",""),("age",""),("gender",""),("phone",""),("email",""),("plan","")]), "#4CAF50"),
        ("📋 View Members", view_members, "#2196F3"),
        ("💳 Add Payment", add_payment, "#FF9800"),
        ("💰 View Payments", view_payments, "#009688"),
        ("📊 Membership Plans", membership_plans, "#673AB7"),
        ("📈 Progress Tracker", progress_tracker, "#E91E63"),
        ("📊 Reports & Analytics", reports_analytics, "#607D8B")
    ]
    
    # Create buttons in a grid
    for i, (text, command, color) in enumerate(buttons):
        row = i // 2
        col = i % 2
        btn = tk.Button(main_frame, text=text, command=command, bg=color, fg="white", 
                       font=("Arial", 11, "bold"), width=20, height=2)
        btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
    
    # Configure grid weights
    for i in range(2):
        main_frame.columnconfigure(i, weight=1)
    for i in range((len(buttons) + 1) // 2):
        main_frame.rowconfigure(i, weight=1)
    
    # Footer
    footer_frame = tk.Frame(root, bg="#f5f5f5", height=40)
    footer_frame.pack(fill="x", padx=20, pady=10)
    footer_frame.pack_propagate(False)
    
    tk.Label(footer_frame, text="© 2024 Gym Management System | Python & MySQL", 
             bg="#f5f5f5", fg="#666", font=("Arial", 9)).pack(expand=True)
    
    root.mainloop()

# ---------- Start Program ----------
if __name__ == "__main__":
    init_db()
    login()
