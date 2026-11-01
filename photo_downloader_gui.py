import json
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from photo_downloader import MediaFile, scan_media_files


CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.photo_downloader_gui.json')


class PhotoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Photo Downloader')
        self.root.minsize(600, 390)

        self.events = queue.Queue()
        self.source = tk.StringVar()
        self.destination = tk.StringVar()
        self.media_to_copy = []
        self.preview_paths = None

        try:
            self._load_defaults()
        except (OSError, ValueError) as error:
            messagebox.showwarning(
                'Saved folders unavailable',
                f'Could not load saved folders from {CONFIG_PATH}:\n{error}',
                parent=self.root,
            )

        self._create_widgets()
        self.root.after(100, self._process_events)

    def _load_defaults(self):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                defaults = json.load(config_file)
        except FileNotFoundError:
            return

        if not isinstance(defaults, dict):
            raise ValueError('The saved settings are not a JSON object.')

        source = defaults.get('source', '')
        destination = defaults.get('destination', '')
        if not isinstance(source, str) or not isinstance(destination, str):
            raise ValueError('Saved source and destination must be folder paths.')

        self.source.set(source)
        self.destination.set(destination)

    def _save_defaults(self):
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as config_file:
                json.dump(
                    {'source': self.source.get(), 'destination': self.destination.get()},
                    config_file,
                    indent=2,
                )
        except OSError as error:
            messagebox.showwarning(
                'Could not save folders',
                f'The download can continue, but the folders could not be saved:\n{error}',
                parent=self.root,
            )

    def _create_widgets(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(4, weight=1)

        ttk.Label(self.root, text='Source folder').grid(
            row=0, column=0, padx=(12, 8), pady=(14, 6), sticky='w'
        )
        self.source_entry = ttk.Entry(self.root, textvariable=self.source)
        self.source_entry.grid(row=0, column=1, padx=4, pady=(14, 6), sticky='ew')
        self.source_browse = ttk.Button(
            self.root, text='Browse...', command=self._choose_source
        )
        self.source_browse.grid(row=0, column=2, padx=(4, 12), pady=(14, 6))

        ttk.Label(self.root, text='Destination folder').grid(
            row=1, column=0, padx=(12, 8), pady=6, sticky='w'
        )
        self.destination_entry = ttk.Entry(self.root, textvariable=self.destination)
        self.destination_entry.grid(row=1, column=1, padx=4, pady=6, sticky='ew')
        self.destination_browse = ttk.Button(
            self.root, text='Browse...', command=self._choose_destination
        )
        self.destination_browse.grid(row=1, column=2, padx=(4, 12), pady=6)

        actions = ttk.Frame(self.root)
        actions.grid(row=2, column=0, columnspan=3, padx=12, pady=(8, 4), sticky='ew')
        self.preview_button = ttk.Button(
            actions, text='Preview', command=self._preview
        )
        self.preview_button.pack(side='left')
        self.copy_button = ttk.Button(
            actions, text='Copy files', command=self._copy, state='disabled'
        )
        self.copy_button.pack(side='left', padx=(8, 0))

        self.status = tk.StringVar(value='Choose a source and destination folder.')
        ttk.Label(self.root, textvariable=self.status).grid(
            row=3, column=0, columnspan=3, padx=12, pady=6, sticky='w'
        )

        self.output = tk.Text(self.root, height=10, wrap='word', state='disabled')
        self.output.grid(
            row=4, column=0, columnspan=3, padx=(12, 0), pady=(4, 12), sticky='nsew'
        )
        self.output_scrollbar = ttk.Scrollbar(
            self.root, orient='vertical', command=self.output.yview
        )
        self.output.configure(yscrollcommand=self.output_scrollbar.set)
        self.output_scrollbar.grid(
            row=4, column=3, padx=(0, 12), pady=(4, 12), sticky='ns'
        )

    def _choose_source(self):
        folder = filedialog.askdirectory(
            title='Choose source folder', initialdir=self.source.get() or None
        )
        if folder:
            self.source.set(folder)

    def _choose_destination(self):
        folder = filedialog.askdirectory(
            title='Choose destination folder', initialdir=self.destination.get() or None
        )
        if folder:
            self.destination.set(folder)

    def _validate_folders(self):
        source = self.source.get().strip()
        destination = self.destination.get().strip()
        if not source or not os.path.isdir(source):
            messagebox.showerror(
                'Invalid source', 'Choose an existing source folder.', parent=self.root
            )
            return None
        if not destination:
            messagebox.showerror(
                'Invalid destination',
                'Choose a destination folder.',
                parent=self.root,
            )
            return None

        source_path = os.path.normcase(os.path.abspath(source))
        destination_path = os.path.normcase(os.path.abspath(destination))
        try:
            common_path = os.path.commonpath((source_path, destination_path))
        except ValueError:
            common_path = ''
        if common_path == source_path:
            messagebox.showerror(
                'Invalid destination',
                'The destination cannot be the source folder or a folder inside it.',
                parent=self.root,
            )
            return None

        return source, destination

    def _set_busy(self, busy):
        state = 'disabled' if busy else 'normal'
        for widget in (
            self.source_entry,
            self.destination_entry,
            self.source_browse,
            self.destination_browse,
            self.preview_button,
        ):
            widget.configure(state=state)
        if busy:
            self.copy_button.configure(state='disabled')

    def _preview(self):
        paths = self._validate_folders()
        if paths is None:
            return

        source, destination = paths
        self._save_defaults()
        self.media_to_copy = []
        self.preview_paths = None
        self._clear_output()
        self._append_output(
            '------------------------------------------------\n'
            f'Finding pictures and videos \n in {source} \n to copy to {destination}\n'
            '------------------------------------------------'
        )
        self.status.set('Scanning source folder...')
        self._set_busy(True)

        def scan():
            try:
                result = scan_media_files(
                    source,
                    destination,
                    log_callback=lambda message: self.events.put(('log', message)),
                )
                self.events.put(('preview_complete', (paths, result)))
            except Exception as error:
                self.events.put(('error', ('Preview failed', str(error))))

        threading.Thread(target=scan, daemon=True).start()

    def _copy(self):
        paths = self._validate_folders()
        if paths is None:
            return
        if not self.media_to_copy or paths != self.preview_paths:
            messagebox.showinfo(
                'Preview required',
                'Run Preview again before copying.',
                parent=self.root,
            )
            return

        count = len(self.media_to_copy)
        if not messagebox.askyesno(
            'Confirm copy',
            f'Copy {count} media file{"s" if count != 1 else ""} to the destination?',
            parent=self.root,
        ):
            return

        files = list(self.media_to_copy)
        self._set_busy(True)
        self.status.set(f'Copying 0 of {count} files...')

        def copy_files():
            copied = 0
            try:
                for media_file in files:
                    self.events.put(('log', f'Copying file to {media_file.dst}\n'))
                    media_file.copy_to_destination_path()
                    copied += 1
                    self.events.put(('copy_progress', (copied, count)))
                self.events.put(('copy_complete', copied))
            except Exception as error:
                self.events.put(
                    ('error', (f'Copy failed after {copied} of {count} files', str(error)))
                )

        threading.Thread(target=copy_files, daemon=True).start()

    def _process_events(self):
        try:
            while True:
                event, details = self.events.get_nowait()
                if event == 'log':
                    self._append_output(details)
                elif event == 'preview_complete':
                    self._show_preview(details[0], details[1])
                elif event == 'copy_progress':
                    copied, total = details
                    self.status.set(f'Copying {copied} of {total} files...')
                elif event == 'copy_complete':
                    self._set_busy(False)
                    self.copy_button.configure(state='disabled')
                    self.status.set(f'Copied {details} files.')
                    self._append_output(f'\nCopy complete: {details} files copied.')
                    self.media_to_copy = []
                elif event == 'error':
                    self._set_busy(False)
                    self.status.set('The operation failed.')
                    messagebox.showerror(
                        details[0], details[1], parent=self.root
                    )
        except queue.Empty:
            pass
        self.root.after(100, self._process_events)

    def _show_preview(self, paths, result):
        allfiles, media_to_copy, skipped, nonmedia = result
        self._set_busy(False)
        self.preview_paths = paths
        self.media_to_copy = media_to_copy
        self.status.set(
            f'Preview: {len(media_to_copy)} to copy, {skipped} already present.'
        )
        self._append_output(
            '------------------------------------------------\n'
            'Photo download preview:\n'
            '------------------------------------------------\n'
            f'Found {len(allfiles)} files\n'
            f'  {nonmedia} non-media files\n'
            f'  {skipped} media files will be skipped\n'
            f'  {len(media_to_copy)} media files that can be copied'
        )
        if not media_to_copy:
            self._append_output(
                '\nNo files found to copy!\nFile formats supported:\n'
                + '\n'.join(MediaFile.VALID_MEDIA_EXT)
            )
        self.copy_button.configure(
            state='normal' if media_to_copy else 'disabled'
        )

    def _clear_output(self):
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.output.configure(state='disabled')

    def _append_output(self, text):
        self.output.configure(state='normal')
        self.output.insert('end', text)
        if not text.endswith('\n'):
            self.output.insert('end', '\n')
        self.output.see('end')
        self.output.configure(state='disabled')


def main():
    root = tk.Tk()
    PhotoDownloaderApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
