import os
import shutil
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

skip = 10

class ImageViewer:
    def __init__(self, root, input_folder, output_folder):
        self.root = root
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.images = sorted([
            f for f in os.listdir(input_folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))
        ])
        self.current_index = 0

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        # Label para exibir a imagem
        self.image_label = tk.Label(root)
        self.image_label.pack(pady=20)  # margem entre a imagem e os botões

        # Label para mostrar o nome da imagem abaixo da imagem
        self.image_name_label = tk.Label(root, text="", anchor="w", font=("Arial", 10, "bold"))
        self.image_name_label.pack(anchor="w", padx=10, pady=5)

        self.create_buttons()
        self.show_image(self.current_index)

        # Usa bind_all para capturar todos os eventos de teclado
        self.root.bind_all("<Key>", self.key_pressed)
        self.root.focus_force()  # força o foco na janela

    def key_pressed(self, event):
        if event.keysym == "Up":
            self.back_10_images(event)
        elif event.keysym == "Left":
            self.back_image(event)
        elif event.keysym in ("Return", "space"):
            self.save_image(event)
        elif event.keysym == "Right":
            self.next_image(event)
        elif event.keysym == "Down":
            self.skip_10_images(event)

    def create_buttons(self):
        # Frame para os botões
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10, padx=10)

        self.back_10_button = tk.Button(
            button_frame, text="Back 10", command=self.back_10_images,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.back_10_button.grid(row=0, column=0, padx=5)

        self.back_button = tk.Button(
            button_frame, text="Back", command=self.back_image,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.back_button.grid(row=0, column=1, padx=5)

        self.save_button = tk.Button(
            button_frame, text="Save", command=self.save_image,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.save_button.grid(row=0, column=2, padx=5)

        self.next_button = tk.Button(
            button_frame, text="Next", command=self.next_image,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.next_button.grid(row=0, column=3, padx=5)

        self.skip_10_button = tk.Button(
            button_frame, text="Next 10", command=self.skip_10_images,
            width=12, height=2, borderwidth=1, relief="solid"
        )
        self.skip_10_button.grid(row=0, column=4, padx=5)

    def show_image(self, index):
        img_path = os.path.join(self.input_folder, self.images[index])
        img = Image.open(img_path)
        img = img.resize((600, 400))  # ajuste de tamanho
        img_tk = ImageTk.PhotoImage(img)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk

        # Atualiza o nome da imagem
        self.image_name_label.config(text=f"Imagem: {self.images[index]}")

    def save_image(self, event=None):
        img_path = os.path.join(self.input_folder, self.images[self.current_index])
        output_img_path = os.path.join(self.output_folder, f"output_{self.images[self.current_index]}")
        shutil.copy(img_path, output_img_path)
        print(f"Imagem salva: {output_img_path}")
        self.next_image()

    def next_image(self, event=None):
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.show_image(self.current_index)
        else:
            print("Já está na última imagem.")

    def back_image(self, event=None):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image(self.current_index)
        else:
            print("Já está na primeira imagem.")

    def skip_10_images(self, event=None):
        if self.current_index + skip < len(self.images):
            self.current_index += skip
        else:
            self.current_index = len(self.images) - 1
        self.show_image(self.current_index)

    def back_10_images(self, event=None):
        if self.current_index - skip >= 0:
            self.current_index -= skip
        else:
            self.current_index = 0
        self.show_image(self.current_index)

    def open_folder(self):
        new_folder = filedialog.askdirectory(title="Selecione a nova pasta de imagens")
        if new_folder:
            self.input_folder = new_folder
            self.output_folder = os.path.join(
                os.path.dirname(new_folder),
                f"output_{os.path.basename(new_folder)}"
            )
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
            self.images = sorted([
                f for f in os.listdir(new_folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))
            ])
            self.current_index = 0
            self.show_image(self.current_index)

def select_folder():
    return filedialog.askdirectory(title="Selecione a pasta de imagens")

def main():
    root = tk.Tk()
    root.title("Visualizador de Imagens")

    input_folder = select_folder()
    if not input_folder:
        print("Pasta de entrada não selecionada.")
        return

    output_folder = os.path.join(
        os.path.dirname(input_folder),
        f"output_{os.path.basename(input_folder)}"
    )

    viewer = ImageViewer(root, input_folder, output_folder)

    # Botão "Open Image Folder" no canto superior esquerdo, acima da imagem
    open_button = tk.Button(
        root, text="Open Image Folder", command=viewer.open_folder,
        width=20, height=2, borderwidth=1, relief="solid"
    )
    open_button.pack(anchor="nw", padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
