import argparse
import sys

from . import Base32CrockfordError, decode, encode, generate, normalize


def main():
	parser = argparse.ArgumentParser(description="Crockford Base32 Utility")
	parser.add_argument(
		"command",
		choices=["encode", "decode", "normalize", "generate"],
		help="Operation to perform",
	)
	parser.add_argument(
		"input",
		nargs="?",
		default=None,
		help="Input to process. For encode: integer or string. For generate: size (optional)",
	)
	parser.add_argument(
		"--checksum",
		action="store_true",
		help="Add/validate checksum symbol",
	)
	parser.add_argument(
		"--split",
		type=int,
		default=0,
		metavar="SIZE",
		help="Split encoded string with hyphens (chunk size, default: no splitting)",
	)
	parser.add_argument(
		"--padding",
		action="store_true",
		help="Add padding characters (=) to output",
	)
	parser.add_argument(
		"--strict",
		action="store_true",
		help="Strict mode for normalize command - error if normalization needed",
	)

	args = parser.parse_args()

	try:
		if args.command == "generate":
			size = int(args.input) if args.input else 16
			result = generate(
				size,
				checksum=args.checksum,
				split=args.split,
				padding=args.padding,
			)
		elif args.command == "encode":
			if args.input is None:
				parser.error("encode command requires an input value")
			try:
				input_value = int(args.input)
			except ValueError:
				parser.error("encode command requires an integer input")
			result = encode(
				input_value,
				checksum=args.checksum,
				split=args.split,
				padding=args.padding,
			)
		elif args.command == "decode":
			if args.input is None:
				parser.error("decode command requires an input value")
			result = decode(args.input, checksum=args.checksum)
		elif args.command == "normalize":
			if args.input is None:
				parser.error("normalize command requires an input value")
			result = normalize(args.input, strict=args.strict)

		print(result)
	except Base32CrockfordError as e:
		print(f"Error: {e}", file=sys.stderr)
		sys.exit(1)
	except ValueError as e:
		print(f"Error: Invalid input - {e}", file=sys.stderr)
		sys.exit(1)


if __name__ == "__main__":
	main()
