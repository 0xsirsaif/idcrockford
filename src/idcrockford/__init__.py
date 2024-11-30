__version__ = "0.1.0"

import re
import secrets
from typing import Dict, Pattern

# =============================================================================
# Constants
# =============================================================================

CROCKFORD_BASE32_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CHECK_SYMBOLS = "*~$=U"

ENCODE_MAP = {i: char for i, char in enumerate(CROCKFORD_BASE32_ALPHABET)}
DECODE_MAP = {char: i for i, char in enumerate(CROCKFORD_BASE32_ALPHABET)}
DECODE_MAP.update({char.lower(): i for char, i in DECODE_MAP.items()})

# Normalization mapping for ambiguous characters
NORMALIZE_MAP: Dict[str, str] = {
	"I": "1",
	"i": "1",
	"L": "1",
	"l": "1",
	"O": "0",
	"o": "0",
}

# Regular expression for valid symbols
VALID_SYMBOLS_PATTERN: Pattern = re.compile(
	f"^[{CROCKFORD_BASE32_ALPHABET}]+[{re.escape(CHECK_SYMBOLS)}]?=*$"
)

# =============================================================================
# Utils
# =============================================================================


def _calculate_checksum(number: int) -> str:
	check_base = len(CROCKFORD_BASE32_ALPHABET + CHECK_SYMBOLS)
	check_value = number % check_base
	return (CROCKFORD_BASE32_ALPHABET + CHECK_SYMBOLS)[check_value]


def _split_string(symbol_string: str, split: int = 4) -> str:
	"""Split string into chunks of specified size.

	Args:
		symbol_string: String to split
		split: Chunk size (default: 4). If 0, no splitting is performed.
	"""
	if not split:
		return symbol_string

	chunks = []
	for pos in range(0, len(symbol_string), split):
		chunks.append(symbol_string[pos : pos + split])
	return "-".join(chunks)


# =============================================================================
# Exceptions
# =============================================================================


class Base32CrockfordError(Exception):
	"""Base exception for Base32Crockford module."""

	pass


class EncodingError(Base32CrockfordError):
	"""Exception raised for errors during encoding."""

	pass


class DecodingError(Base32CrockfordError):
	"""Exception raised for errors during decoding."""

	pass


# =============================================================================
# Encoders
# =============================================================================


class Base32Crockford:
	def __init__(
		self,
		*,
		checksum: bool = False,
		split: int | bool = False,
		padding: bool = False,
	):
		self.checksum = checksum
		self.split = split
		self.padding = padding

	def encode(self, data: int | bytes) -> str:
		# Handle different input types
		if isinstance(data, int):
			if data < 0:
				raise EncodingError("Cannot encode negative integers")
			encoded = self._encode_integer(data)
			num = data
		elif isinstance(data, (bytes, bytearray)):
			encoded = self._encode_bytes(data)
			num = int.from_bytes(data, "big")
		else:
			raise EncodingError(f"Unsupported data type: {type(data).__name__}")

		# Apply options
		if self.checksum:
			encoded += _calculate_checksum(num)

		if self.padding:
			while len(encoded) % 8 != 0:
				encoded += "="

		return _split_string(encoded, self.split)

	def decode(self, data: str) -> int:
		if not isinstance(data, str):
			raise DecodingError(f"Cannot decode data of type: {type(data).__name__}")

		normalized = normalize(data)

		if self.checksum:
			if len(normalized) < 2:
				raise ValueError("String too short to contain checksum")
			symbol_string, check_symbol = normalized[:-1], normalized[-1]
			number = self._decode_string(symbol_string)
			expected_check = _calculate_checksum(number)
			if check_symbol != expected_check:
				raise ValueError(f"Invalid check symbol '{check_symbol}' for string '{symbol_string}'")
			return number

		return self._decode_string(normalized)

	@classmethod
	def generate(cls, size: int = 16, **kwargs) -> str:
		encoder = cls(**kwargs)
		return encoder.encode(secrets.token_bytes(size))

	# =========================================================================
	# Private methods
	# =========================================================================

	def _encode_integer(self, num: int) -> str:
		"""Encode integer to base32 string."""
		if not isinstance(num, int):
			raise EncodingError(f"Input must be an integer, got {type(num).__name__}")
		if num < 0:
			raise EncodingError("Cannot encode negative integers")

		if num == 0:
			return ENCODE_MAP[0]  # 0

		# Convert to base32
		output = ""
		while num > 0:
			num, remainder = divmod(num, 32)
			output = CROCKFORD_BASE32_ALPHABET[remainder] + output

		return output

	def _encode_bytes(self, data: bytes | bytearray) -> str:
		"""Encode bytes to base32 string.

		Each 5-bit group is encoded as a single base32 character.
		If the last group has fewer than 5 bits, it's right-padded with zeros.
		"""
		output = ""
		bits = 0
		buffer = 0

		# Process each byte
		for byte in data:
			# Add byte to buffer
			buffer = (buffer << 8) | byte
			bits += 8

			# Extract 5-bit groups
			while bits >= 5:
				# Take top 5 bits
				index = (buffer >> (bits - 5)) & 0x1F
				output += CROCKFORD_BASE32_ALPHABET[index]
				bits -= 5

		# Handle remaining bits (if any)
		if bits > 0:
			# Right-pad with zeros to make a complete 5-bit group
			index = (buffer << (5 - bits)) & 0x1F
			output += CROCKFORD_BASE32_ALPHABET[index]

		return output

	def _decode_string(self, data: str) -> int:
		normalized = normalize(data)
		try:
			num = 0
			for char in normalized:
				num = num * 32 + DECODE_MAP[char]
			return num
		except KeyError as e:
			raise DecodingError(f"Invalid character in Base32 string: {e}") from e


# =============================================================================
# Fast API
# =============================================================================


class CFIdentifierConfig:
	"""Configuration and methods for Crockford Base32 ID handling.

	Suitable for use in FastAPI:
		- validates IDs
		- generates IDs
	"""

	def __init__(
		self,
		*,
		checksum: bool = True,
		size: int = 16,
	):
		self.checksum = checksum
		self.size = size

	def validate(self, symbol_string: str) -> str:
		try:
			normalized = normalize(symbol_string)
		except ValueError as e:
			raise ValueError(f"Invalid Crockford Base32 string: {e}") from e

		if self.checksum:
			if len(normalized) < 2:
				raise ValueError("String too short to contain checksum")

			value_part, check = normalized[:-1], normalized[-1]

			try:
				number = Base32Crockford().decode(value_part)
				expected_check = _calculate_checksum(number)
				if check != expected_check:
					raise ValueError(f"Invalid checksum '{check}', expected '{expected_check}'")
			except (ValueError, DecodingError) as e:
				raise ValueError(f"Invalid Crockford Base32 string: {e}") from e

		return normalized

	def generate(self) -> str:
		return generate(
			size=self.size,
			checksum=self.checksum,
			split=False,
			padding=False,
		)


# =============================================================================
# Public API
# =============================================================================


def encode(
	data: int | bytes,
	*,
	checksum: bool = False,
	split: int | bool = False,
	padding: bool = False,
) -> str:
	encoder = Base32Crockford(checksum=checksum, split=split, padding=padding)
	return encoder.encode(data)


def decode(symbol_string: str, *, checksum: bool = False) -> int:
	decoder = Base32Crockford(checksum=checksum)
	return decoder.decode(symbol_string)


def normalize(symbol_string: str, strict: bool = False) -> str:
	original = symbol_string
	# Remove hyphens and padding
	norm_string = symbol_string.replace("-", "").rstrip("=")

	# Replace ambiguous characters and convert to uppercase
	for char, replacement in NORMALIZE_MAP.items():
		norm_string = norm_string.replace(char, replacement)
	norm_string = norm_string.upper()

	# Validate characters
	if not VALID_SYMBOLS_PATTERN.match(norm_string):
		raise ValueError(f"string '{norm_string}' contains invalid characters")

	# Check if normalization was needed in strict mode
	if strict and norm_string != original:
		raise ValueError(f"string '{original}' requires normalization")

	return norm_string


def generate(
	size: int = 16,
	*,
	checksum: bool = False,
	split: int | bool = False,
	padding: bool = False,
) -> str:
	return Base32Crockford.generate(size, checksum=checksum, split=split, padding=padding)
