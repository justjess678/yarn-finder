import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import os
import shutil

import color_selector
import image_tools
from color_selector import ColorSelector

col_selector = ColorSelector()


# Function to clear cache (if you have any cached images)
def clear_cache():
    image_tools.clear_data()
    messagebox.showinfo("Cache Cleared", "The cache has been cleared.")


def scrape_yarn_data():
    log_message(f"Checking Ice Yarns, please wait...")
    image_tools.make_data()
    log_message(f"Done checking Ice Yarns!")


# Function to index yarns (process images and show results)
def index_yarns():
    # Log the result
    log_message(f"Comparing yarn colors, please wait...")
    results = col_selector.compare_all_yarn_images()
    log_message(f"Done comparing yarn colors!")
    show_results(results)


# Function to let user select and replace the reference image
def input_reference_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if file_path:
        # Replace the existing reference image with the selected one
        shutil.copy(file_path, color_selector.REFERENCE_IMAGE_PATH)
        load_reference_image()
    log_message(f"Reference image updated")


# Function to load and display the reference image in the UI
def load_reference_image():
    if os.path.exists(color_selector.REFERENCE_IMAGE_PATH):
        ref_img = Image.open(color_selector.REFERENCE_IMAGE_PATH)
        ref_img = ref_img.resize((150, 150))  # Resize for display
        img = ImageTk.PhotoImage(ref_img)
        reference_image_label.config(image=img)
        reference_image_label.image = img


# Function to show the top 9 results in a 3x3 grid
def show_results(results):
    # Clear any previous results
    for widget in result_frame.winfo_children():
        widget.destroy()

    # Limit the results to the top 9
    top_results = results[:9]

    # Display the images in a 3x3 grid
    for idx, result in enumerate(top_results):
        # Download and display the image
        response = requests.get(result["image_url"])
        img_data = Image.open(BytesIO(response.content))
        img_data = img_data.resize((100, 100))  # Resize image for display
        img = ImageTk.PhotoImage(img_data)

        # Create a Label to display the image
        img_label = tk.Label(result_frame, image=img, cursor="hand2")
        img_label.image = img  # Store a reference to the image to prevent garbage collection
        img_label.grid(row=idx // 3, column=idx % 3, padx=10, pady=10)  # Arrange in a 3x3 grid

        # Bind a click event on the image to open the link, passing the URL as a default argument
        img_label.bind("<Button-1>", lambda e, url=result["link"]: open_link(url))

        # Log the result
        log_message(f"Displayed image {idx + 1}: {result['link']}")



# Function to open a link in the browser
def open_link(url):
    import webbrowser
    webbrowser.open(url)


# Function to log messages
def log_message(message):
    log_text.config(state='normal')  # Enable editing to add text
    log_text.insert(tk.END, message + '\n')  # Insert new message
    log_text.config(state='disabled')  # Disable editing again
    log_text.yview(tk.END)  # Scroll to the bottom of the log


# Setting up the main window
root = tk.Tk()
root.title("Yarn Indexer")
root.geometry("400x800")

# Section for reference image input
reference_frame = tk.Frame(root)
reference_frame.pack(pady=10)

reference_image_label = tk.Label(reference_frame)
reference_image_label.pack()

# Create a Text widget for logs at the bottom of the window
log_frame = tk.Frame(root)
log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

log_text = tk.Text(log_frame, height=5, state='disabled')  # Disabled so user can't edit
log_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

select_image_button = tk.Button(reference_frame, text="Input a Reference Image", command=input_reference_image)
select_image_button.pack(pady=5)

# Buttons for "Index Yarns" and "Clear Cache"
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

index_button = tk.Button(button_frame, text="Update Ice Yarns DB", command=scrape_yarn_data)
index_button.pack(pady=10)

index_button = tk.Button(button_frame, text="Get Yarns", command=index_yarns)
index_button.pack(pady=10)


# Frame to display results
result_frame = tk.Frame(root)
result_frame.pack(pady=20)

# Load the reference image if it exists
load_reference_image()

# Start the Tkinter event loop
root.mainloop()
