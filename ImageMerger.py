from PIL import Image
from urllib.request import Request, urlopen
from datetime import datetime
from random import shuffle as suffleLib
from typing import List
import traceback
from dataclasses import dataclass


MERGE_HORIZONTALLY = 1
MERGE_VERTICALLY = 2
MERGE_GRID = 3


@dataclass
class ImageToMerge:

	path: str

	def __get_image_from_url(self):
		try:
			req = Request(self.path)
			with urlopen(req) as u:
				img = Image.open(u)
				return img
		except Exception as e:
			print(str(e))
			print(traceback.format_exc())
			return None

	def __post_init__(self):
		if self.path.startswith("http://") or self.path.startswith("https://"):
			self.content = self.__get_image_from_url()
		else:
			self.content = Image.open(self.path)

	def resize(self, basewidth=800):
		if self.content is None:
			return None
		wpercent = (basewidth / float(self.content.size[0]))
		hsize = int((float(self.content.size[1]) * float(wpercent)))
		img = self.content.resize((basewidth, hsize), Image.Resampling.LANCZOS)
		self.content = img


@dataclass
class Merger:

	list_images: List[ImageToMerge]
	merge_strategy: int = MERGE_GRID
	shuffle: bool = None
	limit_horizontal: int = None
	limit_vertical: int = None
	filename: str = None
	preserve_aspect_ratio: bool = False

	def __nearest_square(self, limit):
		sq = int((limit ** 0.5))
		return sq

	def __post_init__(self):
		# self.list_images = [im.content for im in list_images]
		warning_str = (f"Warning: limit_horizontal({self.limit_horizontal})*limit_vertical({self.limit_vertical}) is smaller than image set size({len(self.list_images)}). Output will not contain all images")

		if self.shuffle:
			suffleLib(self.list_images)

		if self.limit_vertical and self.limit_horizontal is None:
			self.limit_horizontal = len(self.list_images) / self.limit_vertical

		elif self.limit_vertical and self.limit_horizontal:
			print(warning_str)
			m = self.limit_vertical * self.limit_horizontal
			if m < len(self.list_images):
				self.list_images = self.list_images[0:m]
				self.limit_horizontal = self.limit_horizontal

	def generate_merge_list(self):

		if self.merge_strategy == MERGE_HORIZONTALLY:
			if self.limit_horizontal and self.limit_horizontal < len(self.list_images):
				return self.list_images[0:self.limit_horizontal]
			return self.list_images

		elif self.merge_strategy == MERGE_VERTICALLY:
			if self.limit_vertical and self.limit_vertical < len(self.list_images):
				return self.list_images[0:self.limit_vertical]
			return self.list_images

		elif self.merge_strategy == MERGE_GRID:
			merge, h = [], []
			limit_h = self.limit_horizontal
			if self.limit_horizontal is None:
				limit_h = self.__nearest_square(len(self.list_images))

			for idx, im in enumerate(self.list_images):
				if idx < limit_h or idx > len(self.list_images) - self.limit_horizontal / 2:
					h.append(im)
				else:
					merge.append(h)
					h = [im]
					limit_h += self.limit_horizontal
			merge.append(h)
			return merge

	def __generate_merged_image(self):

		t = self.generate_merge_list()
		print(t)
		if self.merge_strategy in (MERGE_HORIZONTALLY, MERGE_VERTICALLY):
			_im = merge_images(list_images_tmp=t, direction=self.merge_strategy, preserve_aspect_ratio=self.preserve_aspect_ratio)
		else:
			# Concat horizontally by line
			result = []
			for line in t:
				_im = None
				_im = merge_images(list_images_tmp=line, direction=MERGE_HORIZONTALLY, preserve_aspect_ratio=self.preserve_aspect_ratio)
				result.append(_im)

			# Concat vertically by concatenated-line
			_im = merge_images(list_images_tmp=result, direction=MERGE_VERTICALLY, preserve_aspect_ratio=self.preserve_aspect_ratio)
		return _im

	def save_image(self, filename: str = None):
		if filename is None:
			filename = generate_filename(suffix="merged", extension="png")
		self.__generate_merged_image().save(filename)
		print(f"Merge images in {filename}")


def generate_filename(suffix, extension):
	seed = datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
	return f"{suffix}_{seed}.{extension}"


def concat_two_images(im1, im2, direction):
	if im1 is None:
		return im2
	if direction == MERGE_HORIZONTALLY:
		dst = Image.new('RGB', (im1.width + im2.width, max(im1.height, im2.height)), (0, 0, 0))
		dst.paste(im1, (0, 0))
		dst.paste(im2, (im1.width, 0))
	elif direction == MERGE_VERTICALLY:
		dst = Image.new('RGB', (max(im1.width, im2.width), im1.height + im2.height), (0, 0, 0))
		dst.paste(im1, (0, 0))
		dst.paste(im2, (0, im1.height))
	return dst


def merge_images(list_images_tmp: List[ImageToMerge], direction: int, preserve_aspect_ratio: bool):
	_im = None
	for im in list_images_tmp:
		if not preserve_aspect_ratio:
			im = im.resize()
		_im = concat_two_images(im1=_im, im2=im, direction=direction)
	return _im
