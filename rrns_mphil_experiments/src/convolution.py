from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantization import FixedPointFormat, QuantizationResult, quantize


@dataclass(frozen=True)
class ConvolutionResult:
    input_quantization: QuantizationResult
    kernel_quantization: QuantizationResult
    integer_output: np.ndarray
    dequantized_output: np.ndarray
    float_reference: np.ndarray


def conv2d_valid(input_map: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    Compute a valid 2D deep-learning style convolution (cross-correlation).
    """
    input_map = np.asarray(input_map, dtype=np.float64)
    kernel = np.asarray(kernel, dtype=np.float64)

    if input_map.ndim != 2 or kernel.ndim != 2:
        raise ValueError("conv2d_valid expects 2D arrays.")
    if kernel.shape[0] > input_map.shape[0] or kernel.shape[1] > input_map.shape[1]:
        raise ValueError("Kernel cannot be larger than the input map.")

    out_h = input_map.shape[0] - kernel.shape[0] + 1
    out_w = input_map.shape[1] - kernel.shape[1] + 1
    output = np.zeros((out_h, out_w), dtype=np.float64)

    for row in range(out_h):
        for col in range(out_w):
            window = input_map[row : row + kernel.shape[0], col : col + kernel.shape[1]]
            output[row, col] = np.sum(window * kernel)

    return output


def integer_conv2d_valid(input_map: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    input_map = np.asarray(input_map, dtype=np.int64)
    kernel = np.asarray(kernel, dtype=np.int64)

    if input_map.ndim != 2 or kernel.ndim != 2:
        raise ValueError("integer_conv2d_valid expects 2D arrays.")
    if kernel.shape[0] > input_map.shape[0] or kernel.shape[1] > input_map.shape[1]:
        raise ValueError("Kernel cannot be larger than the input map.")

    out_h = input_map.shape[0] - kernel.shape[0] + 1
    out_w = input_map.shape[1] - kernel.shape[1] + 1
    output = np.zeros((out_h, out_w), dtype=np.int64)

    for row in range(out_h):
        for col in range(out_w):
            window = input_map[row : row + kernel.shape[0], col : col + kernel.shape[1]]
            output[row, col] = int(np.sum(window * kernel, dtype=np.int64))

    return output


def quantized_convolution(
    input_map: np.ndarray,
    kernel: np.ndarray,
    fmt: FixedPointFormat,
) -> ConvolutionResult:
    input_quantization = quantize(input_map, fmt)
    kernel_quantization = quantize(kernel, fmt)

    integer_output = integer_conv2d_valid(
        input_quantization.quantized_int,
        kernel_quantization.quantized_int,
    )
    dequantized_output = integer_output.astype(np.float64) / (fmt.scale ** 2)
    float_reference = conv2d_valid(np.asarray(input_map, dtype=np.float64), np.asarray(kernel, dtype=np.float64))

    return ConvolutionResult(
        input_quantization=input_quantization,
        kernel_quantization=kernel_quantization,
        integer_output=integer_output,
        dequantized_output=dequantized_output,
        float_reference=float_reference,
    )
