"""Generate a large benchmark dataset for the evaluation pipeline."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


FACTUAL_CAPITALS = [
    ("France", "Paris", "Berlin"),
    ("India", "New Delhi", "Mumbai"),
    ("Japan", "Tokyo", "Osaka"),
    ("Germany", "Berlin", "Munich"),
    ("Italy", "Rome", "Milan"),
    ("Canada", "Ottawa", "Toronto"),
    ("Australia", "Canberra", "Sydney"),
    ("Brazil", "Brasilia", "Rio de Janeiro"),
    ("Spain", "Madrid", "Barcelona"),
    ("Egypt", "Cairo", "Alexandria"),
]

DEFINITIONS = [
    ("AI", "Artificial Intelligence", "only robots"),
    ("CPU", "Central Processing Unit", "a storage device"),
    ("RAM", "temporary memory", "permanent storage"),
    ("HTTP", "a web communication protocol", "a database"),
    ("CSS", "used to style web pages", "backend code"),
    ("SQL", "used to query databases", "a web browser"),
    ("Linux", "an operating system", "a hardware device"),
    ("Git", "a version control system", "a programming language"),
    ("HTML", "a markup language for web pages", "a database"),
    ("Machine Learning", "a subset of AI", "manual learning"),
]

GENERAL_QUERIES = [
    (
        "Where is my order?",
        "Your order is in transit",
        "Your order details are available in the tracking page",
        "Your order has turned into a sandwich",
    ),
    (
        "When will my package arrive?",
        "Your package will arrive tomorrow",
        "Your package is on the way and should arrive soon",
        "Your package arrived on the moon",
    ),
    (
        "Can I track my shipment?",
        "Yes, you can track it with the tracking ID",
        "Tracking is available through the app or email updates",
        "No shipment can ever be tracked",
    ),
    (
        "My parcel is delayed, what should I do?",
        "Please check the tracking page or contact support",
        "A delay can happen, so review tracking updates and reach support if needed",
        "Throw your phone into the sea",
    ),
    (
        "Can I change the delivery address?",
        "Yes, address change may be possible before dispatch",
        "You may be able to update the address if the shipment has not been dispatched yet",
        "Addresses are stored on Jupiter",
    ),
    (
        "Do you offer international shipping?",
        "Yes, international shipping is available to selected regions",
        "International shipping may be available depending on destination and service coverage",
        "We only ship to volcanoes",
    ),
]

MATH_OPERATIONS = [
    ("+", lambda a, b: a + b),
    ("-", lambda a, b: a - b),
    ("*", lambda a, b: a * b),
]


def factual_row(rng: random.Random, quality: str) -> dict[str, str]:
    country, capital, wrong_city = rng.choice(FACTUAL_CAPITALS)
    prompt = rng.choice(
        [
            f"What is the capital of {country}?",
            f"Name the capital city of {country}.",
            f"Which city is the capital of {country}?",
        ],
    )
    if quality == "GOOD":
        output = rng.choice(
            [
                capital,
                f"{capital} is the capital of {country}.",
                f"The capital of {country} is {capital}.",
            ],
        )
    elif quality == "BAD":
        output = rng.choice(
            [
                f"{country} has many important cities, and the capital is commonly referred to as {capital}.",
                f"{capital} is associated with the capital administration of {country}, though the answer depends on what detail you need.",
                f"{capital} is the capital, but there are also other major cities in {country}.",
            ],
        )
    else:
        output = rng.choice(
            [
                wrong_city,
                f"{wrong_city} is the capital of {country}.",
                f"The capital of {country} is {wrong_city}.",
            ],
        )
    return {"input": prompt, "output": output}


def math_row(rng: random.Random, quality: str) -> dict[str, str]:
    op, fn = rng.choice(MATH_OPERATIONS)
    a = rng.randint(2, 50)
    b = rng.randint(2, 20)
    answer = fn(a, b)
    wrong_answer = answer + rng.choice([-7, -3, 2, 5, 9])
    prompt = rng.choice(
        [
            f"What is {a} {op} {b}?",
            f"Calculate {a} {op} {b}.",
            f"Solve {a} {op} {b}.",
        ],
    )
    if quality == "GOOD":
        output = rng.choice(
            [
                str(answer),
                f"{answer}",
                f"The answer is {answer}.",
            ],
        )
    elif quality == "BAD":
        output = rng.choice(
            [
                f"If you work it out carefully, the result comes to about {answer}.",
                f"This is a straightforward arithmetic problem, and the final result is {answer}, assuming standard calculation.",
                f"After doing the calculation step by step, you get {answer}.",
            ],
        )
    else:
        output = rng.choice(
            [
                str(wrong_answer),
                f"The answer is {wrong_answer}.",
                f"After calculation, it becomes {wrong_answer}.",
            ],
        )
    return {"input": prompt, "output": output}


def definition_row(rng: random.Random, quality: str) -> dict[str, str]:
    term, correct, wrong = rng.choice(DEFINITIONS)
    prompt = rng.choice(
        [
            f"What is {term}?",
            f"Define {term}.",
            f"What does {term} mean?",
        ],
    )
    if quality == "GOOD":
        output = rng.choice(
            [
                f"{term} is {correct}.",
                correct.capitalize() + ".",
                f"{term} means {correct}.",
            ],
        )
    elif quality == "BAD":
        output = rng.choice(
            [
                f"{term} is related to {correct}, although people can describe it in different ways depending on context.",
                f"In simple terms, {term} refers to {correct}, but there is more detail behind it.",
                f"{term} is generally understood as {correct}, though the exact wording may vary.",
            ],
        )
    else:
        output = rng.choice(
            [
                f"{term} is {wrong}.",
                wrong.capitalize() + ".",
                f"{term} means {wrong}.",
            ],
        )
    return {"input": prompt, "output": output}


def general_row(rng: random.Random, quality: str) -> dict[str, str]:
    prompt, correct_short, partial, incorrect = rng.choice(GENERAL_QUERIES)
    if quality == "GOOD":
        output = rng.choice(
            [
                correct_short + ".",
                correct_short,
                f"{correct_short} right now.",
            ],
        )
    elif quality == "BAD":
        output = rng.choice(
            [
                partial + ".",
                f"{partial}, although the exact next step depends on the shipment status.",
                f"{partial}. You may need to review more details in the app.",
            ],
        )
    else:
        output = rng.choice(
            [
                incorrect + ".",
                incorrect,
                f"Actually, {incorrect.lower()}.",
            ],
        )
    return {"input": prompt, "output": output}


ROW_BUILDERS = [factual_row, math_row, definition_row, general_row]


def generate_dataset(size: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    good_count = int(size * 0.4)
    bad_count = int(size * 0.3)
    incorrect_count = size - good_count - bad_count

    qualities = (
        ["GOOD"] * good_count
        + ["BAD"] * bad_count
        + ["INCORRECT"] * incorrect_count
    )
    rng.shuffle(qualities)

    dataset = []
    for quality in qualities:
        builder = rng.choice(ROW_BUILDERS)
        dataset.append(builder(rng, quality))

    rng.shuffle(dataset)
    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate benchmark dataset.json")
    parser.add_argument("--size", type=int, default=50000, help="Number of rows to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dataset.json"),
        help="Output JSON file path",
    )
    args = parser.parse_args()

    dataset = generate_dataset(args.size, args.seed)
    args.output.write_text(json.dumps(dataset, indent=2), encoding="utf-8")

    good_count = int(args.size * 0.4)
    bad_count = int(args.size * 0.3)
    incorrect_count = args.size - good_count - bad_count
    print(
        f"Generated {args.size} rows -> GOOD={good_count} BAD={bad_count} INCORRECT={incorrect_count} | output={args.output}",
    )


if __name__ == "__main__":
    main()
