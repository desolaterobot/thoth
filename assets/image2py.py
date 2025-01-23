import base64

with open("icon.ico", "rb") as image_file, open("icon.py", 'wb') as newFile:
    encoded_string = base64.b64encode(image_file.read())
    newFile.write(encoded_string)