import tkinter as tk
import time

def loop():
    value = 0
    while True:
        if value == 100:
            break
        time.sleep(0.5)
        print(value)
        label.config(text=f"Current Value: {value}")
        app.update()
        value+=1

# Create the Tkinter application
app = tk.Tk()
app.title("Update Widget on Integer Change")


label = tk.Label(app, text="Current Value: 0")
label.pack(pady=10)
button = tk.Button(app, text='start', command=loop)
button.pack(pady=10)

# Start the Tkinter event loop
app.mainloop()