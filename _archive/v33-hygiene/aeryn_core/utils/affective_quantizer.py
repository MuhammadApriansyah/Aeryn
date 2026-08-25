class BinaryAffectionVectorQuantizer:
    def __init__(self):
        pass

    def quantize_float_tensor_to_binary_bit(self, emotional_snapshot_dict: dict) -> dict:
        binary_tensor_dict = {}
        bitmask_integer = 0
        bit_position = 0
        
        for key, value in sorted(emotional_snapshot_dict.items()):
            float_val = float(value)
            binary_bit = 1 if float_val >= 0.5 else -1
            binary_tensor_dict[key] = binary_bit
            
            if binary_bit == 1:
                bitmask_integer |= (1 << bit_position)
            bit_position += 1
            
        return {
            "quantized_binary_tensor": binary_tensor_dict,
            "packed_bitmask_integer": bitmask_integer
        }

    def compute_hamming_distance_bitwise(self, packed_bitmask_a: int, packed_bitmask_b: int) -> int:
        xor_result = packed_bitmask_a ^ packed_bitmask_b
        hamming_distance = 0
        while xor_result > 0:
            hamming_distance += xor_result & 1
            xor_result >>= 1
        return hamming_distance
