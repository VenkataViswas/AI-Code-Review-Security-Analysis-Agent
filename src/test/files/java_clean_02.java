// Clean example: validation and a focused method.
class PriceCalculator {
    public double discountedPrice(double price, double percentage) {
        if (price < 0) {
            throw new IllegalArgumentException("price cannot be negative");
        }
        if (percentage < 0 || percentage > 100) {
            throw new IllegalArgumentException("invalid percentage");
        }
        return price * (1.0 - percentage / 100.0);
    }
}
