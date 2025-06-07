import os
import numpy as np
from PIL import Image
import datetime
import wave

class ImageLSBSteganography:
    def __init__(self) -> None:
        self.outputFilePath = "./Output/Image/"

    def embedImage(self, coverImagePath, secretImagePath, callback=None):
        cover_image = Image.open(coverImagePath)
        cover_array = np.array(cover_image)

        secret_image = Image.open(secretImagePath)
        secret_array = np.array(secret_image)

        if cover_array.shape != secret_array.shape:
            raise ValueError("Cover and secret images must have the same dimensions.")

        stego_array = np.copy(cover_array)
        for i in range(cover_array.shape[0]):
            for j in range(cover_array.shape[1]):
                for channel in range(3):
                    if cover_array[i, j, channel] != secret_array[i, j, channel]:
                        stego_array[i, j, channel] = (cover_array[i, j, channel] & 0xFE) | (secret_array[i, j, channel] >> 7)

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"ImageStegano_{timestamp}.png"
        filepath = os.path.join(self.outputFilePath, filename)
        stego_image = Image.fromarray(stego_array)
        stego_image.save(filepath)

        if callback:
            callback(filepath)

        print(f"Secret Image embedded within the Cover Image: {filename}")
        return filepath

    def extractImage(self, steganoImagePath, callback=None):
        stego_image = Image.open(steganoImagePath)
        stego_array = np.array(stego_image)

        secret_array = (stego_array & 1) * 255
        secret_image = Image.fromarray(secret_array.astype(np.uint8))

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"ExtractedImage_{timestamp}.png"
        filepath = os.path.join(self.outputFilePath, filename)
        secret_image.save(filepath)

        if callback:
            callback(filepath)

        print(f"Secret Image extracted from Stegano Image: {filename}")
        return filepath

    def embedMessage(self, coverImagePath, secretMessage, callback=None):
        cover_image = Image.open(coverImagePath)
        cover_array = np.array(cover_image)

        max_message_length = (cover_array.shape[0] * cover_array.shape[1] * 3) // 8
        if len(secretMessage) > max_message_length:
            raise ValueError("Secret message is too long to embed in the image.")

        secretMessageLength = len(secretMessage)
        binary_secret_message = ''.join(format(ord(char), '08b') for char in secretMessage)

        stego_array = np.copy(cover_array)
        stego_array[-1, -1, -1] = secretMessageLength

        message_index = 0
        for i in range(cover_array.shape[0]):
            for j in range(cover_array.shape[1]):
                for channel in range(3):
                    if message_index < len(binary_secret_message):
                        stego_array[i, j, channel] = (cover_array[i, j, channel] & 0xFE) | int(binary_secret_message[message_index])
                        message_index += 1

        stego_image = Image.fromarray(stego_array.astype(np.uint8))

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"MessageStegano_{timestamp}.png"
        filepath = os.path.join(self.outputFilePath, filename)
        stego_image.save(filepath)

        if callback:
            callback(filepath)

        print(f"Secret message embedded in Image: {filename}")
        return filepath

    def extractMessage(self, steganoImagePath):
        stego_image = Image.open(steganoImagePath)
        stego_array = np.array(stego_image)

        secretMessageLength = stego_array[-1, -1, -1] * 8

        binary_secret_message = ""
        messageIndex = 0
        for i in range(stego_array.shape[0]):
            for j in range(stego_array.shape[1]):
                for channel in range(3):
                    if messageIndex >= secretMessageLength:
                        break
                    binary_secret_message += str(stego_array[i, j, channel] & 1)
                    messageIndex += 1

        secretMessage = ''.join(
            chr(int(binary_secret_message[i:i + 8], 2))
            for i in range(0, len(binary_secret_message), 8)
        )
        print(f"Hidden secret message was: {secretMessage}")
        return secretMessage


class AudioLSBSteganography:
    def __init__(self) -> None:
        self.outputFilePath = "./Output/Audio/"

    def embedMessage(self, coverAudioPath, secretMessage, callback=None):
        output_dir = self.outputFilePath
        os.makedirs(output_dir, exist_ok=True)
        audio = wave.open(coverAudioPath, mode='rb')

        frames = audio.readframes(audio.getnframes())
        secretMessage = ''.join(format(ord(char), '08b') for char in secretMessage)
        messageLength = len(secretMessage)
        if messageLength > 255:
            raise Exception("Message Length should not be greater than 255")

        frames_modified = bytearray(frames)
        frames_modified[-1] = messageLength

        for i in range(messageLength):
            frames_modified[i] = (frames_modified[i] & 254) | int(secretMessage[i])

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"AudioStegano_{timestamp}.wav"
        filepath = os.path.join(self.outputFilePath, filename)

        audio_steg = wave.open(filepath, 'wb')
        audio_steg.setparams(audio.getparams())
        audio_steg.writeframes(frames_modified)

        audio.close()
        audio_steg.close()

        if callback:
            callback(filepath)

        print(f"Secret message embedded in Audio: {filename}")
        return filepath

    def extractMessage(self, stegoAudioPath, callback=None):
        audio = wave.open(stegoAudioPath, mode='rb')
        frames = audio.readframes(audio.getnframes())
        messageLength = frames[-1]

        extracted_message = ""
        for bit in frames[:messageLength]:
            extracted_message += str(bit & 1)

        extracted_text = ''.join(
            chr(int(extracted_message[i:i + 8], 2))
            for i in range(0, len(extracted_message), 8)
        )

        audio.close()

        if callback:
            callback(extracted_text)

        print(f"Extracted message from Audio: {extracted_text}")
        return extracted_text


if __name__ == "__main__":
    print("-- Testing Stegano Handler Module --")
    steg = ImageLSBSteganography()
    steg.extractMessage("./Output/MessageStegano_20231002223200.png")
