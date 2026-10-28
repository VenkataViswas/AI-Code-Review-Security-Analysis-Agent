// Mixed: possible HTML injection and no length/character validation.
class WelcomePage {
    public String render(String displayName) {
        if (displayName == null) {
            displayName = "";
        }
        return "<h1>Welcome " + displayName + "</h1>";
    }
}
