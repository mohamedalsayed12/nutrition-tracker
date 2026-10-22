const MAX_GRAMS = 10000

export function gramsFromServing(gramsPerServing: number, quantity: number): number {
  if (!Number.isFinite(gramsPerServing) || gramsPerServing <= 0) {
    throw new Error("Choose a serving size.")
  }
  if (!Number.isFinite(quantity) || quantity <= 0) {
    throw new Error("Enter a quantity greater than 0.")
  }
  const grams = Math.round(gramsPerServing * quantity * 10) / 10
  if (grams <= 0 || grams > MAX_GRAMS) {
    throw new Error("That amount must be greater than 0 g and at most 10,000 g.")
  }
  return grams
}
