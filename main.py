import numpy as np
import cv2
import tkinter as tk
from PIL import Image, ImageTk

import sys
from collections import OrderedDict

from color_labeler import ColorLabeler
# from solver import Solver

class ColorScanner():
	def __init__(self):
		self.cap = cv2.VideoCapture(0)
		self.labeler = ColorLabeler()

		# Window config
		self.root = tk.Tk()
		self.root.wm_title('Rubik\'s Cube Color Detection')
		self.root.config(background='#ffffff')
		self.root.protocol('WM_DELETE_WINDOW', self.destructor)
		self.root.resizable(False, False)

		# Webcam display
		self.webcam = tk.Label(self.root)
		self.webcam.pack(side='left', padx=10, pady=10)

		# Sticker color preview panel
		self.offset = 3
		self.cell_size = 93
		self.colorPreview = tk.Canvas(self.root, 
			height=self.cell_size*3+self.offset, 
			width=self.cell_size*3+self.offset)
		self.colorPreview.pack(padx=10, pady=10)
		self.squares = []

		# User instructions for scanning
		self.colorPromptText = tk.StringVar()
		self.colorPromptText.set('With white facing up, scan the green face.')
		self.colorPrompt = tk.Label(self.root, textvariable=self.colorPromptText)
		self.colorPrompt.pack()

		# When capture_pressed = True, stop scanning and allow user to verify or reject color
		self.capture_pressed = False
		self.captureButton = tk.Button(self.root, text='Capture', command=self.capture_callback)
		self.captureButton.pack(side='left', padx=10)
		self.redoButton = tk.Button(self.root,text='Redo', state='disabled', command=self.reset_buttons)
		self.redoButton.pack(side='right', padx=10)

		self.faces = {
			'green' : [],
			'red' : [],
			'blue' : [],
			'orange' : [],
			'white' : [],
			'yellow' : []
		}

		self.index_to_color = ['green', 'red', 'blue', 'orange', 'white', 'yellow']
		self.current_color = self.index_to_color[0]
		self.currentFace = 0

		self.draw_preview()
		self.scanner_loop()

	def destructor(self):
		print("[INFO] Closing...")
		self.root.destroy()
		self.cap.release()
		cv2.destroyAllWindows()

	# Allow user to either commit or reject scanned colors
	def capture_callback(self):
		self.captureButton['text'] = 'Confirm'
		self.captureButton['command'] = self.confirm_callback
		self.redoButton['state'] = 'normal'
		self.capture_pressed = True

		print("[INFO] Waiting for user to confirm color labels...")

	# Move on to next face and reset buttons
	def confirm_callback(self):
		print('[INFO] Captured {} face: {}'.format(self.current_color, self.faces[self.current_color]))

		self.reset_buttons()
		self.currentFace += 1

		if self.currentFace < 6:
			self.current_color = self.index_to_color[self.currentFace]
			if self.currentFace < 4:
				self.colorPromptText.set('With white facing up, scan the {} face.'.format(self.current_color))
			else:
				self.colorPromptText.set('With green facing up, scan the {} face.'.format(self.current_color))

	# Reset buttons to original state before capture_pressed
	def reset_buttons(self):
		self.captureButton['text'] = 'Capture'
		self.captureButton['command'] = self.capture_callback
		self.redoButton['state'] = 'disabled'
		self.capture_pressed = False

	# Draws color preview panel
	def draw_preview(self):
		for i in range(3):
			for j in range(3):
				self.squares.append(self.colorPreview.create_rectangle(
					i*self.cell_size+self.offset, j*self.cell_size+self.offset, 
					(i+1)*self.cell_size+self.offset, (j+1)*self.cell_size+self.offset))

	# Draw green grid and get coordinates for ROIs
	# TODO: Precompute centers for all 9 ROIs to avoid repeating computation for every frame
	def draw_guides_and_get_rois(self, img):
		center = (int(img.shape[1]/2), int(img.shape[0]/2))
		size = int(img.shape[0]/10)

		rois = []
		img_with_guides = np.copy(img)

		for i in range(-1, 2):
			for j in range(-1, 2):
				x = center[0] + i*(size)*2
				y = center[1] + j*(size)*2

				# Get ROI
				rois.append(img[y-int(size*.75):y+int(size*.75), x-int(size*.75):x+int(size*.75)])

				# Draw guide
				cv2.rectangle(img_with_guides, (x-size,y+size), (x+size,y-size), (0,255,0), 3)

		return img_with_guides, rois

	def scanner_loop(self):
		# Exit after all 6 faces have been scanned
		if self.currentFace > 5:
			self.destructor()

		success, img = self.cap.read()

		if success:
			img_mirrored = cv2.flip(img, 1)
			img_with_guides, rois = self.draw_guides_and_get_rois(img_mirrored)

			# Display webcam feed
			rgb = cv2.cvtColor(img_with_guides, cv2.COLOR_BGR2RGBA)
			imgtk = ImageTk.PhotoImage(image=Image.fromarray(rgb).resize(
				(int(rgb.shape[1]/2), int(rgb.shape[0]/2)), Image.ANTIALIAS))
			self.webcam.imgtk = imgtk
			self.webcam.config(image=imgtk)

			# Predict color for each ROI and update color preview panel
			if not self.capture_pressed:
				for i in range(9):			
					# Preprocessing
					blurred = cv2.GaussianBlur(rois[i], (5,5), 0)
					hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

					color_prediction = self.labeler.label_image(hsv)

					# Override center color prediction with current face color, center color always constant
					if i == 4:
						self.colorPreview.itemconfig(self.squares[4], fill=self.current_color)
					else:
						self.colorPreview.itemconfig(self.squares[i], fill=color_prediction)
			else: # Store predicted colors
				colors = []
				for i in range(6,-1,-3):
					for j in range(i,i+3):
						colors.append(self.colorPreview.itemcget(self.squares[j], 'fill'))

				self.faces[self.current_color] = colors

		self.root.after(30, self.scanner_loop)

if __name__ == '__main__':
	scanner = ColorScanner()
	scanner.root.mainloop()
