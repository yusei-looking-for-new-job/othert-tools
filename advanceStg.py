import numpy as np
import cv2
from scipy.fft import dctn, idctn
from scipy.stats import norm
import struct
import random

# 色空間変換
def rgb2ycbcr(rgb):
    xform = np.array([[.299, .587, .114], [-.1687, -.3313, .5], [.5, -.4187, -.0813]])
    ycbcr = rgb.dot(xform.T)
    ycbcr[:,:,[1,2]] += 128
    return np.uint8(ycbcr)

def ycbcr2rgb(ycbcr):
    xform = np.array([[1, 0, 1.402], [1, -0.34414, -.71414], [1, 1.772, 0]])
    rgb = ycbcr.astype(np.float)
    rgb[:,:,[1,2]] -= 128
    rgb = rgb.dot(xform.T)
    np.putmask(rgb, rgb > 255, 255)
    np.putmask(rgb, rgb < 0, 0)
    return np.uint8(rgb)

# JPEG 量子化tables
std_luminance_qt = np.array([[16, 11, 10, 16, 24, 40, 51, 61],
                             [12, 12, 14, 19, 26, 58, 60, 55],
                             [14, 13, 16, 24, 40, 57, 69, 56],
                             [14, 17, 22, 29, 51, 87, 80, 62],
                             [18, 22, 37, 56, 68, 109, 103, 77],
                             [24, 35, 55, 64, 81, 104, 113, 92],
                             [49, 64, 78, 87, 103, 121, 120, 101],
                             [72, 92, 95, 98, 112, 100, 103, 99]])


zigzag = [0, 1, 5, 6, 14, 15, 27, 28,
          2, 4, 7, 13, 16, 26, 29, 42,
          3, 8, 12, 17, 25, 30, 41, 43,
          9, 11, 18, 24, 31, 40, 44, 53,
          10, 19, 23, 32, 39, 45, 52, 54,
          20, 22, 33, 38, 46, 51, 55, 60,
          21, 34, 37, 47, 50, 56, 59, 61,
          35, 36, 48, 49, 57, 58, 62, 63]

zigzag_inv = [zigzag.index(i) for i in range(64)]

# DCT 
def dct_2d(block):
    return dctn(block, norm='ortho')

# IDCT
def idct_2d(coeffs):
    return idctn(coeffs, norm='ortho')


def quantize(coeffs, qtable):
    return np.round(coeffs / qtable).astype(np.int32)


def dequantize(quantized, qtable):
    return (quantized * qtable).astype(np.float64)


def encode_coeffs(quantized):
    coeffs = quantized.ravel()
    encoded = b''
    last_non_zero = len(coeffs) - np.trim_zeros(coeffs, 'fb').size
    run = 0
    for i in range(len(coeffs)):
        if i >= last_non_zero:
            break
        if coeffs[i] == 0:
            run += 1
        else:
            val = int(coeffs[i])
            if val < 0:
                val = 0
            elif val > 255:
                val = 255
            encoded += struct.pack('>BB', run, val)
            run = 0
    if last_non_zero > 0:
        encoded += struct.pack('>B', 0)
    return encoded


def decode_coeffs(encoded):
    coeffs = np.zeros(64, dtype=int)
    i = 0
    for b1, b2 in (bytes((b1, b2)) for b1, b2 in zip(encoded[::2], encoded[1::2])):
        run = b1 >> 4
        val = (b2 if b1 & 0xf == 0 else b1 & 0xf)
        if val == 0:
            break
        for _ in range(run):
            coeffs[zigzag[i]] = 0
            i += 1
        coeffs[zigzag[i]] = (-1) ** (val // 16) * (val % 16)
        i += 1
    return coeffs

# カバー画像からDCT係数を取得
def get_dct_coeffs(image):
    if len(image.shape) == 3: # カラー画像の場合
        ycbcr = rgb2ycbcr(image)
        dct_coeffs = []
        for c in range(ycbcr.shape[2]):
            c_dcts = []
            for i in range(0, ycbcr.shape[0], 8):
                row_coeffs = []
                for j in range(0, ycbcr.shape[1], 8):
                    block = ycbcr[i:i+8, j:j+8, c]
                    coeffs = dct_2d(block.astype(np.float64))
                    row_coeffs.append(coeffs)
                c_dcts.append(row_coeffs)
            dct_coeffs.append(np.array(c_dcts))
        return dct_coeffs
    else: # グレースケール画像の場合
        dct_coeffs = []
        for i in range(0, image.shape[0], 8):
            row_coeffs = []
            for j in range(0, image.shape[1], 8):
                block = image[i:i+8, j:j+8]
                coeffs = dct_2d(block.astype(np.float64))
                row_coeffs.append(coeffs)
            dct_coeffs.append(row_coeffs)
        return np.array(dct_coeffs)

# DCT係数からカバー画像を復元  
def get_image_from_dct(dct_coeffs):
    if isinstance(dct_coeffs, list): # カラー画像の場合
        ycbcr = []
        for c_dcts in dct_coeffs:
            c_img = np.zeros((c_dcts.shape[0]*8, c_dcts.shape[1]*8))
            for i in range(c_dcts.shape[0]):
                for j in range(c_dcts.shape[1]):
                    coeffs = c_dcts[i,j]
                    block = idct_2d(coeffs)
                    c_img[i*8:(i+1)*8, j*8:(j+1)*8] = block
            ycbcr.append(np.round(c_img).astype(np.uint8))
        ycbcr = np.stack(ycbcr, axis=2)
        return ycbcr2rgb(ycbcr)
    else:  # グレースケール画像の場合
        image = np.zeros((dct_coeffs.shape[0]*8, dct_coeffs.shape[1]*8))
        for i in range(dct_coeffs.shape[0]):
            for j in range(dct_coeffs.shape[1]):
                coeffs = dct_coeffs[i,j]
                block = idct_2d(coeffs)
                image[i*8:(i+1)*8, j*8:(j+1)*8] = block
        return np.round(image).astype(np.uint8)

# JPEG圧縮
def compress_jpeg(image, quality=95):
    if len(image.shape) == 3: # カラー画像
        ycbcr = rgb2ycbcr(image)
        qtables = []
        encoded = []
        for c in range(ycbcr.shape[2]):
            qtable = np.floor((std_luminance_qt * 100 / quality) + 0.5)
            dct_coeffs = get_dct_coeffs(ycbcr[:,:,c])
            quant_coeffs = np.array([quantize(block, qtable) for row in dct_coeffs for block in row])
            qtables.append(qtable)
            encoded.append(encode_coeffs(quant_coeffs))
        return (encoded, qtables)
    else: # グレースケール画像
        qtable = np.floor((std_luminance_qt * 100 / quality) + 0.5)
        dct_coeffs = get_dct_coeffs(image)
        quant_coeffs = np.array([quantize(block, qtable) for row in dct_coeffs for block in row])
        return (encode_coeffs(quant_coeffs), qtable)

# JPEG展開
def decompress_jpeg(encoded, qtables):
    if isinstance(qtables, list): # カラー画像
        ycbcr = []
        for enc, qtable in zip(encoded, qtables):
            quant_coeffs = decode_coeffs(enc)
            dct_coeffs = np.array([dequantize(block, qtable) for block in quant_coeffs])
            c_img = get_image_from_dct(dct_coeffs.reshape(-1, dct_coeffs.shape[1] // 8, 8, 8))
            ycbcr.append(c_img)
        ycbcr = np.stack(ycbcr, axis=2)
        return ycbcr2rgb(ycbcr)
    else: # グレースケール画像
        quant_coeffs = decode_coeffs(encoded)
        dct_coeffs = np.array([dequantize(block, qtables) for block in quant_coeffs])
        return get_image_from_dct(dct_coeffs.reshape(-1, dct_coeffs.shape[1] // 8, 8, 8))

def stc_embed(dct_coeffs, payload):
    payload_bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    modified_coeffs = dct_coeffs.copy()
    embeddable_positions = np.abs(dct_coeffs) > 1
    for i, bit in enumerate(payload_bits):
        modified_coeffs[embeddable_positions][i] ^= bit
    return modified_coeffs


def stc_extract(dct_coeffs, payload_length):
    extracted_bits = []
    embeddable_positions = np.abs(dct_coeffs) > 1
    for coeff in dct_coeffs[embeddable_positions]:
        extracted_bits.append(coeff & 1)
    payload = np.packbits(extracted_bits[:payload_length * 8])
    return payload.tobytes()

# 隠蔽関数
def embed_message(image, message, quality=95):
    dct_coeffs = get_dct_coeffs(image)
    quant_coeffs = quantize(dct_coeffs, np.floor((std_luminance_qt * 100 / quality) + 0.5))
    modified_quant_coeffs = stc_embed(quant_coeffs, message)
    modified_dct_coeffs = dequantize(modified_quant_coeffs, np.floor((std_luminance_qt * 100 / quality) + 0.5))
    return get_image_from_dct(modified_dct_coeffs)

# 抽出関数
def extract_message(image, message_length, quality=95):
    dct_coeffs = get_dct_coeffs(image)
    quant_coeffs = quantize(dct_coeffs, np.floor((std_luminance_qt * 100 / quality) + 0.5))
    return stc_extract(quant_coeffs, message_length)

def is_robust(cover_image, payload, quality=95):
    embedded_image = embed_message(cover_image, payload, quality)
    compressed, qtables = compress_jpeg(embedded_image, quality)
    decompressed_image = decompress_jpeg(compressed, qtables)
    extracted_payload = extract_message(decompressed_image, len(payload), quality)
    return extracted_payload == payload

cover_image = cv2.imread('image.jpg')
message = b'Hello, World!'
quality = 95

print(is_robust(cover_image, message, quality))

# 埋め込み後の画像を確認
embedded_image = embed_message(cover_image, message, quality)
cv2.imwrite('embedded_image.jpg', embedded_image)

# 圧縮後の画像を確認
compressed, qtables = compress_jpeg(embedded_image, quality)
with open('compressed_image.jpg', 'wb') as f:
    f.write(compressed)

# 解凍後の画像を確認
decompressed_image = decompress_jpeg(compressed, qtables)
cv2.imwrite('decompressed_image.jpg', decompressed_image)

# 抽出されたメッセージを確認
extracted_payload = extract_message(decompressed_image, len(message), quality)
print('Extracted Message:', extracted_payload)
print('Message:',message)
print('Messages Match:', extracted_payload == message)

