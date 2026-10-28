// Code quality issue: method does too many things.
class OrderProcessor {
    public String processOrder(boolean valid, boolean inStock, boolean paid) {
        System.out.println("Starting");
        if (!valid) {
            System.out.println("Invalid order");
            return "INVALID";
        }
        if (!inStock) {
            System.out.println("Out of stock");
            return "OUT_OF_STOCK";
        }
        if (!paid) {
            System.out.println("Payment failed");
            return "PAYMENT_FAILED";
        }
        System.out.println("Reserve inventory");
        System.out.println("Send receipt");
        System.out.println("Write audit record");
        System.out.println("Notify shipping");
        return "COMPLETE";
    }
}
