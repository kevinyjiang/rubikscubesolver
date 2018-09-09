from collections import defaultdict
from collections import OrderedDict
from cv2 import mean

class ColorLabeler:
	def __init__(self):
		# Bounds for hue values
		self.colors = OrderedDict({
			'red-lower' : (0, 5),
			'orange' : (5, 20),
			'yellow' : (20, 45),
			'green' : (45, 90),
			'blue' : (90, 120),
			'red-upper' : (120, 180)
		})

	def label_image(self, image):
		# Get average color of image
		average_color = mean(image)

		if average_color[1] < .3*255 and average_color[2] > .3*255:
			return 'white'

		# Frequency seems to be more effective than average for non-white colors
		most_frequent_hue = self.get_most_frequent_hue(image)

		for color in self.colors.items():
			if most_frequent_hue[0] >= color[1][0] and most_frequent_hue[0] < color[1][1]:
				if color[0] == 'red-lower' or color[0] == 'red-upper':
					return 'red'
				else:
					return color[0]

	def get_most_frequent_hue(self, image):
		hues = defaultdict(int)

		for i in range(image.shape[0]):
			for j in range(image.shape[1]):
				hues[image[i,j,0]] += 1

		most_frequent_hue = (None, 0)
		for k,v in hues.items():
			if v > most_frequent_hue[1]:
				most_frequent_hue = (k, v)

		return most_frequent_hue