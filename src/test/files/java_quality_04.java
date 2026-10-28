// Code quality issue: public mutable state and unclear naming.
class Data {
    public int x;
    public String s;

    public void doIt(int a) {
        x = a;
        s = "value";
    }
}
