import tkinter as tk
from tkinter import scrolledtext, Entry, Button, Frame, END
import threading
import time
from datetime import datetime

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Window Application")
        self.root.geometry("600x500")
        self.root.minsize(400, 300)
        
        # Set colors and fonts
        self.bg_color = "#f5f5f5"
        self.chat_bg = "white"
        self.send_button_color = "#4CAF50"
        self.message_font = ("Helvetica", 10)
        self.input_font = ("Helvetica", 11)
        
        self.root.configure(bg=self.bg_color)
        
        # Create main frame
        self.main_frame = Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(
            self.main_frame, 
            wrap=tk.WORD, 
            bg=self.chat_bg, 
            font=self.message_font,
            bd=1,
            relief=tk.SOLID
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_display.config(state=tk.DISABLED)
        
        # Bottom frame for message input and send button
        self.bottom_frame = Frame(self.main_frame, bg=self.bg_color)
        self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # Message input field
        self.msg_entry = Entry(
            self.bottom_frame, 
            font=self.input_font,
            bd=1,
            relief=tk.SOLID
        )
        self.msg_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(5, 2))
        self.msg_entry.bind("<Return>", self.send_message)
        self.msg_entry.focus()
        
        # Send button
        self.send_button = Button(
            self.bottom_frame, 
            text="Send", 
            command=self.send_message,
            bg=self.send_button_color,
            fg="white",
            relief=tk.FLAT,
            font=("Helvetica", 10, "bold"),
            padx=15
        )
        self.send_button.pack(side=tk.RIGHT, padx=5)
        
        # Initialize users and messages
        self.users = ["You", "Friend"]
        self.user_colors = {"You": "#007bff", "Friend": "#28a745"}
        
        # Add welcome message
        self.add_message("System", "Welcome to the chat! Start typing to send a message.", "gray")
        
        # For demo purposes - simulated incoming messages
        self.simulate_incoming_messages()
        
    def add_message(self, user, message, color):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        
        # Format the message with timestamp
        formatted_msg = f"[{timestamp}] {user}: "
        
        # Insert the username with its color
        self.chat_display.insert(END, formatted_msg, f"{user}_name")
        self.chat_display.tag_config(f"{user}_name", foreground=color, font=("Helvetica", 10, "bold"))
        
        # Insert the message text
        self.chat_display.insert(END, f"{message}\n")
        
        # Auto-scroll to the bottom
        self.chat_display.see(END)
        self.chat_display.config(state=tk.DISABLED)
        
    def send_message(self, event=None):
        """Send a message (triggered by button or Enter key)"""
        message = self.msg_entry.get().strip()
        if message:
            self.add_message("You", message, self.user_colors["You"])
            self.msg_entry.delete(0, END)
            
    def simulate_incoming_messages(self):
        """Simulate incoming messages for demo purposes"""
        def run_demo():
            time.sleep(2)
            self.add_message("Friend", "Hey there! How are you doing?", self.user_colors["Friend"])
            
            time.sleep(5)
            self.add_message("Friend", "I was wondering if you'd like to meet up this weekend?", self.user_colors["Friend"])
            
            time.sleep(8)
            self.add_message("Friend", "We could grab lunch at that new restaurant downtown.", self.user_colors["Friend"])
            
        # Run in a separate thread to avoid blocking the UI
        threading.Thread(target=run_demo, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
