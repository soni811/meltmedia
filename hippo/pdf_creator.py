
import copy
import img2pdf
import logging
import math

from PIL import Image
from src.the_ark.s3_client import S3ClientException
from hippo.util import create_logger, JPEG_FILE_EXTENSION, MISC_PATH_TEXT, PDF_MAX_PAGE_HEIGHT, PDF_CROP_PADDING

log = create_logger("PDF Creator")


class PDFCreator:
    """
    Create a PDF from an image_list object
    """
    def __init__(self, image_list, s3_client, s3_path):
        """
        Instantiates variables to be used while creating the PDF
        """
        self.log = logging.getLogger(self.__class__.__name__)
        self.image_list = image_list
        self.s3_client = s3_client
        self.s3_path = s3_path
        self.canv = None
        self.pdf_list = copy.deepcopy(image_list)  # A new image list with which to make the screenshot log

    def create_pdf(self, folder, pdf_name="screenshots.pdf", image_extension=JPEG_FILE_EXTENSION,
                   crop_height=PDF_MAX_PAGE_HEIGHT, crop_padding=PDF_CROP_PADDING):
        """
        Takes an image_list, parses out the image data, adds the image paths to a list, uses that list to create a PDF
        :param folder: The path to the  folder that contains the images
        :param pdf_name: The name that you'd like to save the PDF as
        :param image_extension: The file type extension that the images were saved as (jpeg, png, bmp, etc.)
        :param crop_height: The max height of images in the pdf. Defaults to 14400 because it is the tallest that
                            Adobe Acrobat will accept
        :param crop_padding: The overlap, in pixels, that you'd like to have between crops.
        :return: The updated pdf image list and a link to the pdf on S3.
        """
        images = []
        try:
            file_path = folder + pdf_name

            for pin, page in enumerate(self.image_list["image_list"]):
                count = 0  # Tracks the number of times we have updated the length of the pdf_list index
                for index, image_data in enumerate(page.get("image_data", [])):
                    # Check the image height
                    # import pdb; pdb.set_trace();
                    cropped_images = self._crop_for_pdf(image_data, image_extension, crop_height, crop_padding)

                    # Update the PDF Image list if the image got cropped
                    if cropped_images:
                        log.info("Image cropped for pdf...")
                        # Replace the current image in the list with the cropped image(s)
                        self.pdf_list["image_list"][pin]["image_data"][index + count:index + count + 1] = cropped_images

                        # Iterate the count by the number of additional images returned by the crop
                        count += len(cropped_images) - 1

                        # Add the images to the list used to create the PDF
                        for image in cropped_images:
                            images.append(image["local_path"])
                    else:
                        # If the image did not need to get cropped, add it to the images list alone
                        images.append(image_data["local_path"])

                else:
                    # If the page did not have any image data, then send out a warning that no images were caught for it
                    # Do not worry about the misc page being empty
                    if not page.get("image_data") and page["url"] != MISC_PATH_TEXT:
                        log.warning(f"No images were found in the image_list for the page at {page['url']!r}. Check the above log output for errors regarding this page")
        except Exception as e:
            message = f"Issue gathering and/or converting images while attempting to create the PDF S3: {e}"
            raise PDFCreatorException(message)

        try:
            log.info(f"Creating a {len(images)} page PDF...")
            # import pdb; pdb.set_trace();
            # pdf_bytes = img2pdf.convert(images, colorspace="RGB")
            pdf_bytes = img2pdf.convert(images)
            with open(file_path, "wb") as pdf_file:
                pdf_file.write(pdf_bytes)
            log.info("PDF Creation Complete!")

        except Exception as e:
            message = "Issue while creating PDF file: {e}"
            raise PDFCreatorException(message)

        try:
            log.info("Sending the PDF file up to S3... like a boss!!")
            # - Send the PDF to S3 and return the file
            # s3_url = self.s3_client.store_file(self.s3_path, file_path, pdf_name, True, "application/pdf", 4000000000)
            s3_url = self.s3_client.store_file(self.s3_path, file_path, pdf_name, True, "application/pdf")
            return s3_url, self.pdf_list
        except S3ClientException as e:
            message = "Issue sending PDF file up to S3: {e}"
            raise PDFCreatorException(message)

    def _crop_for_pdf(self, image_data, image_extension, crop_height, crop_padding):
        """
        Checks the height of the image and chops it into crop_height sized chunks
        :param image_data: The data object that contains information about the image
        :param image_extension: The file type extension used to save this image
        :param crop_height: The max height for an image. This image will be cropped if taller than this value
        :param crop_padding: The overlap, in pixels, that you'd like to have between crops.
        :return: a list of image data objects.
        """
        cropped_images = []

        # Open the image and get its sweet stats
        full_image = Image.open(image_data["local_path"])
        full_width = full_image.size[0]
        full_height = full_image.size[1]
        # Chop it up if it's taller than the given crop height
        if full_height > crop_height:
            # Determine how many times you need to crop the image
            crop_count = int(math.ceil(full_height / crop_height))

            # Cycle through and chop the image up.
            for iteration in range(crop_count):
                # - Determine the bottom and top of the crop box depending on crop height and padding
                crop_top = (iteration * crop_height) - (iteration * crop_padding)
                # Use the height of the image being cropped if the crop_bottom would be below it
                crop_bottom = min(((iteration + 1) * crop_height) - (iteration * crop_padding), full_height)

                # Crop the image to get a new chunk
                cropped_image = full_image.crop((
                    0,              # Left edge of the image
                    crop_top,       # TOP of the crop
                    full_width,     # Right edge of the image
                    crop_bottom     # BOTTOM of the crop
                ))

                # Generate a new filename by adding _001, etc. to the end of the base image's name
                filename = f"{image_data['filename'].split('.')[0]}_00{(iteration + 1)}.{image_extension}"

                # Save the image locally
                local_path = image_data["local_path"].replace(image_data["filename"], filename)
                cropped_image.save(local_path)

                # Send saved image to S3
                s3_location = self.s3_client.store_file(self.s3_path, local_path, filename, True)

                # Create a new image_list page data object
                new_data = {
                    "suffix": f"{image_data['suffix']}_00{(iteration + 1)}",
                    "s3_location": s3_location,
                    "url": image_data["url"],
                    "filename": filename,
                    "local_path": local_path,
                    "s3_path": self.s3_path
                }
                cropped_images.append(new_data)

        return cropped_images


class PDFCreatorException(Exception):
    def __init__(self, message):
        self.msg = message
        self.message = message

    def __str__(self):
        return self.message
