// Code quality issue: duplicated calculation logic.
class InvoiceTotals {
    public double totalForA(double price, int quantity) {
        double total = 0;
        for (int i = 0; i < quantity; i++) {
            total += price;
        }
        return total;
    }

    public double totalForB(double price, int quantity) {
        double total = 0;
        for (int i = 0; i < quantity; i++) {
            total += price;
        }
        return total;
    }
}
