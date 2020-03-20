import os
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import filedialog
from mcdconverter import MCDConverter
from pathlib import Path

class App:
    def __init__(self, master):
        self.master = master
        self.master.geometry("200x600+300+300")
        self.master.resizable(0, 0)

        self.top_frame = tk.Frame(master, height=125, bd=2, relief=tk.RIDGE)
        self.top_frame.pack_propagate(0)
        self.top_frame.pack(fill=tk.BOTH, expand=1)
        self.bot_frame = tk.Frame(master, height=450, bd=2, relief=tk.RIDGE)
        self.bot_frame.pack_propagate(0)
        self.bot_frame.pack(fill=tk.BOTH)

        self.input_path = None
        self.output_dir = None

        self.setup()

    def ask_mcdfile(self):
        self.input_path = Path(filedialog.askopenfilename(title="Select MCDFile"))
        self.show_input_path.set(self.input_path)

    def ask_output_dir(self):
        self.output_dir = Path(filedialog.askdirectory(
            initialdir=Path("~").expanduser(),
            title="Select output directory", )
        )
        self.show_output_dir.set(self.output_dir)

    def _add_slider(self, maxval=100, default=1, label=""):
        text = tk.Label(self.bot_frame, text=label, justify=tk.CENTER)
        text.pack()

        slider = tk.Scale(self.bot_frame, orient="horizontal", from_=0, to=maxval)
        slider.set(default)
        slider.pack(fill=tk.X, expand=1)
        return slider

    def setup(self):
        self.show_input_path = tk.StringVar()
        self.show_output_dir = tk.StringVar()

        ask1 = tk.Button(self.top_frame, text="Select MCD File",
                command=self.ask_mcdfile, background="light gray")
        ask2 = tk.Button(self.top_frame, text="Select Output Directory",
                command=self.ask_output_dir, background="light gray")
        show1 = tk.Label(self.top_frame, textvariable=self.show_input_path,
                wraplength=180)
        show2 = tk.Label(self.top_frame, textvariable=self.show_output_dir,
                wraplength=180)
        ask1.pack(fill=tk.X, expand=1)
        show1.pack(fill=tk.X, expand=1)
        ask2.pack(fill=tk.X, expand=1)
        show2.pack(fill=tk.X, expand=1)

        text = tk.Label(self.bot_frame, text="Select input paramaters")
        text.pack()

        self.clipmin = self._add_slider(label="Minimum clip %tile")
        self.clipmax = self._add_slider(default=99, label="Maximum clip %tile")
        self.clipblur = self._add_slider(maxval=50, default=1, label="Clip blur radius")
        self.segblur = self._add_slider(maxval=50, default=25, label="Segmentation blur radius")

        runtiff_button = tk.Button(self.bot_frame, text="Raw tiffs", command=self.run_tiff, fg="blue")
        runtiff_button.pack(fill=tk.X, expand=1)
        runclip_button = tk.Button(self.bot_frame, text="Run clip", command=self.run_clip, fg="blue")
        runclip_button.pack(fill=tk.X, expand=1)
        runseg_button = tk.Button(self.bot_frame, text="Run seg", command=self.run_seg, fg="blue")
        runseg_button.pack(fill=tk.X, expand=1)
        runall_button = tk.Button(self.bot_frame, text="Run all!", command=self.run_all, fg="blue")
        runall_button.pack(fill=tk.X, expand=1)

        quit_button = tk.Button(self.bot_frame, text="Dismiss",
                command=self.quit, background="light gray", fg="red")
        quit_button.pack(fill=tk.X, expand=1)

    def quit(self):
        print("Bye!")
        self.master.destroy()

    def check_inputs(self):
        if (not self.input_path) or (not self.output_dir):
            messagebox.showwarning(
                "Run",
                "Must select MCD file and output directory"
            )
            return False
        return True

    def print_inputs(self, name=""):
        print(
f"""---
Running {name} with the following options:
mcd_file: {self.input_path}
out_dir:  {self.output_dir}
min_clip: {self.clipmin.get()}
max_clip: {self.clipmax.get()}
seg_blur: {self.segblur.get()}
clip_blur:{self.clipblur.get()}"""
)

    def run_all(self):
        if not self.check_inputs(): return
        self.print_inputs("full pipeline")

        converter = MCDConverter(self.input_path, self.output_dir)
        converter.convert(
            cmin=self.clipmin.get(),
            cmax=self.clipmax.get(),
            segmentation_blur_radius=self.segblur.get(),
            clip_blur_radius=self.clipblur.get()
        )
        print("done\n---")

    def run_tiff(self):
        if not self.check_inputs(): return
        self.print_inputs("raw tiff generation")

        converter = MCDConverter(self.input_path, self.output_dir)
        converter.load_mcd()
        converter.save_individual_tiffs(converter.outdir_tiffs)
        print("done\n---")

    def run_clip(self):
        if not self.check_inputs(): return
        self.print_inputs("clipping")

        converter = MCDConverter(self.input_path, self.output_dir)
        converter.load_mcd()
        converter.filter_stack(
            self.clipmin.get(),
            self.clipmax.get(),
            self.clipblur.get()
        )
        converter.save_tiff_stack(converter.outdir_stack)
        converter.save_individual_tiffs(converter.outdir_tiffs_filt)
        print("done\n---")

    def run_seg(self):
        if not self.check_inputs(): return
        self.print_inputs("segmentation blurring")

        converter = MCDConverter(self.input_path, self.output_dir)
        converter.load_mcd()
        converter.filter_stack(
            self.clipmin.get(),
            self.clipmax.get(),
            self.segblur.get()
        )
        converter.save_tiff_stack(converter.outdir_stack_blur)
        print("done\n---")


if __name__ == "__main__":
    master = tk.Tk()
    App(master)
    master.mainloop()
