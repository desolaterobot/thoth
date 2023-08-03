import tkinter as tk
import time

def update_label(*args):
    new_value = int_var.get()
    label.config(text=f"Current Value: {new_value}")

def loop():
    while True:
        value:int = int_var.get()
        if value == 100:
            break
        time.sleep(0.5)
        int_var.set(value+1)

# Create the Tkinter application
app = tk.Tk()
app.title("Update Widget on Integer Change")

# Create an integer variable
int_var = tk.IntVar()

# Set the initial value of the integer variable
int_var.set(0)

# Create a label to display the current value of the integer variable
label = tk.Label(app, text="Current Value: 0")
label.pack(pady=10)
button = tk.Button(app, text='start', command=loop)
button.pack(pady=10)

# Attach the update_label function as a callback to the integer variable
int_var.trace("w", update_label)

# Start the Tkinter event loop
app.mainloop()