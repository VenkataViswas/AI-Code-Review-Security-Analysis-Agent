// Security issue: hardcoded credential.
class PaymentClient {
    private static final String API_KEY = "EXAMPLE_SECRET_KEY_DO_NOT_USE";

    public String getApiKeyForRequest() {
        return API_KEY;
    }
}
